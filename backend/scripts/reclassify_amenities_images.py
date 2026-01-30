#!/usr/bin/env python3
"""
Script to reclassify existing images tagged as "amenities" to distinguish
between building amenities (shared/public facilities) and apartment amenities (in-unit features).

This script queries all images with "amenities" tag and re-runs classification
using the updated classifier with amenities data as context to help distinguish
between the two categories.

Usage:
    python3 reclassify_amenities_images.py [property_id] [--dry-run] [--batch-size N]
    
    property_id: Optional property ID to limit reclassification to one property
    --dry-run: Show what would be changed without making updates
    --batch-size: Number of images to process per batch (default: 5)
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


def find_amenities_images(property_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Find all images tagged with "amenities".
    
    Args:
        property_id: Optional property ID to filter by
        
    Returns:
        List of image dictionaries with amenities tag
    """
    client = get_supabase_client()
    
    # Build query to fetch images
    query = client.table("property_images").select("*")
    
    if property_id:
        query = query.eq("property_id", property_id)
    
    response = query.execute()
    
    if not response.data:
        return []
    
    # Filter in Python for images that have "amenities" in their tags
    # This is more reliable than using contains() which can have syntax issues
    amenities_images = []
    for img in response.data:
        image_tags = img.get("image_tags")
        if image_tags and isinstance(image_tags, list) and "amenities" in image_tags:
            amenities_images.append(img)
    
    return amenities_images


def reclassify_amenities_images(property_id: Optional[str] = None, dry_run: bool = True, batch_size: int = 5):
    """
    Reclassify images currently tagged as "amenities".
    
    Args:
        property_id: Optional property ID to limit to one property
        dry_run: If True, only show what would be changed
        batch_size: Number of images to process per batch
    """
    repo = PropertyRepository()
    client = get_openai_client()
    
    # Find all images with amenities tag
    print("Finding images tagged as 'amenities'...")
    images = find_amenities_images(property_id)
    
    if not images:
        print("No images found with 'amenities' tag.")
        return
    
    print(f"\nFound {len(images)} images tagged as 'amenities'\n")
    
    if dry_run:
        print("DRY RUN MODE - No changes will be made\n")
    
    # Group images by property_id to fetch amenities data efficiently
    images_by_property = {}
    for img in images:
        prop_id = img.get("property_id")
        if prop_id not in images_by_property:
            images_by_property[prop_id] = []
        images_by_property[prop_id].append(img)
    
    print(f"Images grouped across {len(images_by_property)} properties\n")
    
    # Statistics
    stats = {
        "total": len(images),
        "reclassified": 0,
        "kept_as_building_amenities": 0,
        "changed_to_apartment_amenities": 0,
        "changed_to_other": 0,
        "failed": 0,
        "errors": []
    }
    
    # Process images by property to use amenities data context
    for prop_id, prop_images in images_by_property.items():
        print(f"\n{'='*80}")
        print(f"Processing property: {prop_id} ({len(prop_images)} images)")
        print(f"{'='*80}")
        
        # Fetch amenities data for this property
        amenities_data = None
        try:
            amenities_obj = repo.get_amenities_by_property_id(prop_id)
            if amenities_obj and amenities_obj.amenities_data:
                amenities_data = amenities_obj.amenities_data
                building_count = len(amenities_data.get("building_amenities", []))
                apartment_count = len(amenities_data.get("apartment_amenities", []))
                print(f"✓ Loaded amenities data: {building_count} building, {apartment_count} apartment")
            else:
                print("⚠ No amenities data found for this property - classifying without context")
        except Exception as e:
            print(f"⚠ Error fetching amenities data: {e} - classifying without context")
        
        # Process images in batches
        for i in range(0, len(prop_images), batch_size):
            batch = prop_images[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(prop_images) + batch_size - 1) // batch_size
            
            print(f"\n  Processing batch {batch_num}/{total_batches} ({len(batch)} images)...")
            
            for img in batch:
                image_id = img.get("id")
                image_url = img.get("image_url", "")
                current_tags = img.get("image_tags") or []
                
                print(f"\n    Image ID: {image_id}")
                print(f"    URL: {image_url[:80]}...")
                print(f"    Current tags: {current_tags}")
                
                if dry_run:
                    print(f"    [DRY RUN] Would reclassify this image with amenities context...")
                    continue
                
                # Reclassify the image with amenities data context
                try:
                    result = classify_image_with_openai(
                        image_url, 
                        client, 
                        amenities_data=amenities_data
                    )
                    
                    if "error" in result:
                        print(f"    ✗ Error: {result.get('error')}")
                        stats["failed"] += 1
                        stats["errors"].append({
                            "image_id": image_id,
                            "property_id": prop_id,
                            "error": result.get("error")
                        })
                        continue
                    
                    new_tags = result.get("tags", [])
                    confidence = result.get("confidence", 0.0)
                    quality_score = result.get("quality_score", 0.0)
                    
                    print(f"    New tags: {new_tags}")
                    print(f"    Confidence: {confidence:.3f}")
                    
                    # Determine what changed
                    kept_building = "building_amenities" in new_tags
                    changed_to_apartment = "apartment_amenities" in new_tags
                    changed_to_other_cat = not kept_building and not changed_to_apartment
                    
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
                        if kept_building:
                            stats["kept_as_building_amenities"] += 1
                            print(f"    ✓ Changed to 'building_amenities'")
                        elif changed_to_apartment:
                            stats["changed_to_apartment_amenities"] += 1
                            print(f"    ✓ Changed to 'apartment_amenities'")
                        else:
                            stats["changed_to_other"] += 1
                            print(f"    ✓ Changed to other category: {new_tags[0] if new_tags else 'none'}")
                    else:
                        print(f"    ✗ Failed to update database")
                        stats["failed"] += 1
                    
                    # Small delay to respect rate limits
                    import time
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"    ✗ Exception: {e}")
                    stats["failed"] += 1
                    stats["errors"].append({
                        "image_id": image_id,
                        "property_id": prop_id,
                        "error": str(e)
                    })
            
            # Longer delay between batches
            if i + batch_size < len(prop_images):
                import time
                time.sleep(2)
    
    # Print summary
    print("\n" + "=" * 80)
    print("RECLASSIFICATION SUMMARY")
    print("=" * 80)
    print(f"\nTotal images processed: {stats['total']}")
    print(f"Successfully reclassified: {stats['reclassified']}")
    print(f"  - Changed to 'building_amenities': {stats['kept_as_building_amenities']}")
    print(f"  - Changed to 'apartment_amenities': {stats['changed_to_apartment_amenities']}")
    print(f"  - Changed to other categories: {stats['changed_to_other']}")
    print(f"Failed: {stats['failed']}")
    
    if stats["errors"]:
        print(f"\nErrors encountered:")
        for error in stats["errors"][:10]:  # Show first 10 errors
            print(f"  - Image {error['image_id']} (Property {error['property_id']}): {error['error']}")
        if len(stats["errors"]) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more errors")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reclassify images tagged as 'amenities' to distinguish between building and apartment amenities"
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
        reclassify_amenities_images(
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











