#!/usr/bin/env python3
"""
Script to reclassify existing images tagged as "floor_plans" to distinguish
between actual floor plans (drawings/diagrams) and apartment interiors (photos).

This script queries all images with "floor_plans" tag and re-runs classification
using the updated classifier that can distinguish between these two categories.

Usage:
    python3 reclassify_floor_plan_images.py [property_id] [--dry-run]
    
    property_id: Optional property ID to limit reclassification to one property
    --dry-run: Show what would be changed without making updates
"""

import sys
import os
import argparse
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env.local or .env file
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env.local"
if not env_file.exists():
    env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"Loaded environment variables from {env_file}")

# Add parent directory to path to import modules
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from database import PropertyRepository
from database.supabase_client import get_supabase_client

# Import classify_images directly without triggering __init__.py
classify_images_path = os.path.join(os.path.dirname(__file__), '..', 'tools', 'classify_images.py')
spec = importlib.util.spec_from_file_location("classify_images", classify_images_path)
classify_images_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(classify_images_module)
classify_image_with_openai = classify_images_module.classify_image_with_openai
get_openai_client = classify_images_module.get_openai_client


def find_floor_plan_images(property_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Find all images tagged with "floor_plans".
    
    Args:
        property_id: Optional property ID to filter by
        
    Returns:
        List of image dictionaries with floor_plans tag
    """
    client = get_supabase_client()
    
    # Build query to fetch images
    query = client.table("property_images").select("*")
    
    if property_id:
        query = query.eq("property_id", property_id)
    
    response = query.execute()
    
    if not response.data:
        return []
    
    # Filter in Python for images that have "floor_plans" in their tags
    # This is more reliable than using contains() which can have syntax issues
    floor_plan_images = []
    for img in response.data:
        image_tags = img.get("image_tags")
        if image_tags and isinstance(image_tags, list) and "floor_plans" in image_tags:
            floor_plan_images.append(img)
    
    return floor_plan_images


def reclassify_floor_plan_images(property_id: Optional[str] = None, dry_run: bool = True, batch_size: int = 5):
    """
    Reclassify images currently tagged as "floor_plans".
    
    Args:
        property_id: Optional property ID to limit to one property
        dry_run: If True, only show what would be changed
        batch_size: Number of images to process per batch
    """
    repo = PropertyRepository()
    client = get_openai_client()
    
    # Find all images with floor_plans tag
    print("Finding images tagged as 'floor_plans'...")
    images = find_floor_plan_images(property_id)
    
    if not images:
        print("No images found with 'floor_plans' tag.")
        return
    
    print(f"\nFound {len(images)} images tagged as 'floor_plans'\n")
    
    if dry_run:
        print("DRY RUN MODE - No changes will be made\n")
    
    # Statistics
    stats = {
        "total": len(images),
        "reclassified": 0,
        "kept_as_floor_plans": 0,
        "changed_to_apartment_interior": 0,
        "failed": 0,
        "errors": []
    }
    
    # Process images in batches
    for i in range(0, len(images), batch_size):
        batch = images[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(images) + batch_size - 1) // batch_size
        
        print(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} images)...")
        
        for img in batch:
            image_id = img.get("id")
            image_url = img.get("image_url", "")
            current_tags = img.get("image_tags") or []
            property_id_val = img.get("property_id")
            
            print(f"\n  Image ID: {image_id}")
            print(f"  URL: {image_url[:80]}...")
            print(f"  Current tags: {current_tags}")
            
            if dry_run:
                print(f"  [DRY RUN] Would reclassify this image...")
                continue
            
            # Reclassify the image
            try:
                result = classify_image_with_openai(image_url, client)
                
                if "error" in result:
                    print(f"  ✗ Error: {result.get('error')}")
                    stats["failed"] += 1
                    stats["errors"].append({
                        "image_id": image_id,
                        "error": result.get("error")
                    })
                    continue
                
                new_tags = result.get("tags", [])
                confidence = result.get("confidence", 0.0)
                quality_score = result.get("quality_score", 0.0)
                
                print(f"  New tags: {new_tags}")
                print(f"  Confidence: {confidence:.3f}")
                
                # Determine what changed
                kept_floor_plan = "floor_plans" in new_tags
                changed_to_interior = "apartment_interior" in new_tags
                
                # Update the image in database
                success = repo.update_image_classification(
                    image_id=image_id,
                    tags=new_tags,
                    confidence=confidence,
                    quality_score=quality_score,
                    method="ai_vision_reclassification"
                )
                
                if success:
                    stats["reclassified"] += 1
                    if kept_floor_plan:
                        stats["kept_as_floor_plans"] += 1
                        print(f"  ✓ Kept as 'floor_plans'")
                    elif changed_to_interior:
                        stats["changed_to_apartment_interior"] += 1
                        print(f"  ✓ Changed to 'apartment_interior'")
                    else:
                        print(f"  ✓ Reclassified (no longer floor_plans or apartment_interior)")
                else:
                    print(f"  ✗ Failed to update database")
                    stats["failed"] += 1
                
                # Small delay to respect rate limits
                import time
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ✗ Exception: {e}")
                stats["failed"] += 1
                stats["errors"].append({
                    "image_id": image_id,
                    "error": str(e)
                })
        
        # Longer delay between batches
        if i + batch_size < len(images):
            import time
            time.sleep(2)
    
    # Print summary
    print("\n" + "=" * 80)
    print("RECLASSIFICATION SUMMARY")
    print("=" * 80)
    print(f"\nTotal images processed: {stats['total']}")
    print(f"Successfully reclassified: {stats['reclassified']}")
    print(f"  - Kept as 'floor_plans': {stats['kept_as_floor_plans']}")
    print(f"  - Changed to 'apartment_interior': {stats['changed_to_apartment_interior']}")
    print(f"Failed: {stats['failed']}")
    
    if stats["errors"]:
        print(f"\nErrors encountered:")
        for error in stats["errors"][:10]:  # Show first 10 errors
            print(f"  - Image {error['image_id']}: {error['error']}")
        if len(stats["errors"]) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more errors")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reclassify images tagged as 'floor_plans' to distinguish between floor plans and apartment interiors"
    )
    parser.add_argument(
        "property_id",
        nargs="?",
        default=None,
        help="Optional property ID to limit reclassification to one property"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making updates"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of images to process per batch (default: 5)"
    )
    
    args = parser.parse_args()
    
    try:
        reclassify_floor_plan_images(
            property_id=args.property_id,
            dry_run=args.dry_run,
            batch_size=args.batch_size
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

