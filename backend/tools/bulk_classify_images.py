"""
Bulk classification script for existing property images.

Processes all unclassified images (or re-classifies existing ones) in batches
to respect rate limits and provide progress tracking.
"""

import sys
import os
import importlib.util
from pathlib import Path
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env.local or .env file
# Check project root (parent of backend)
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

# Import classify_images directly without triggering __init__.py
# This avoids loading dependencies from other tools
classify_images_path = os.path.join(os.path.dirname(__file__), 'classify_images.py')
spec = importlib.util.spec_from_file_location("classify_images", classify_images_path)
classify_images_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(classify_images_module)
classify_images = classify_images_module.classify_images

# Quality threshold below which images are auto-hidden after classification
AUTO_HIDE_QUALITY_THRESHOLD = 0.4


def bulk_classify_images(
    property_id: Optional[str] = None,
    url: Optional[str] = None,
    force_reclassify: bool = False,
    batch_size: int = 5,
    max_images: Optional[int] = None
) -> dict:
    """
    Classify all unclassified images (or re-classify if force_reclassify is True).
    
    Args:
        property_id: Optional property ID (UUID) to limit classification to one property
        url: Optional website URL to find property by URL instead of ID
        force_reclassify: If True, re-classify images that already have classifications
        batch_size: Number of images to process per batch
        max_images: Maximum number of images to process (None for all)
        
    Returns:
        Dictionary with classification statistics
    """
    repo = PropertyRepository()
    
    # Resolve property_id from URL if needed
    resolved_property_id = property_id
    if url and not property_id:
        # Look up property by website URL
        property_obj = repo.get_property_by_website_url(url)
        if property_obj and property_obj.id:
            resolved_property_id = property_obj.id
            print(f"Found property: {property_obj.property_name} (ID: {resolved_property_id})")
        else:
            return {
                "total_images": 0,
                "images_to_classify": 0,
                "classified": 0,
                "failed": 0,
                "error": f"Property not found for URL: {url}"
            }
    
    # Get images to classify
    if resolved_property_id:
        images = repo.get_property_images(resolved_property_id)
    else:
        # Get all images from all properties
        # We'll need to query all properties first
        from database.supabase_client import get_supabase_client
        client = get_supabase_client()
        
        # Get all properties
        properties_response = client.table("properties").select("id").execute()
        property_ids = [p["id"] for p in properties_response.data] if properties_response.data else []
        
        # Get all images
        images = []
        for pid in property_ids:
            images.extend(repo.get_property_images(pid))
    
    # Filter images
    images_to_classify = []
    for image in images:
        # Skip hidden images
        if image.is_hidden:
            continue
        
        # Skip if already classified and not forcing re-classification
        if not force_reclassify:
            if image.image_tags and len(image.image_tags) > 0:
                continue
        
        images_to_classify.append(image)
    
    # Limit if max_images is set
    if max_images and len(images_to_classify) > max_images:
        images_to_classify = images_to_classify[:max_images]
    
    if not images_to_classify:
        print("No images to classify.")
        return {
            "total_images": len(images),
            "images_to_classify": 0,
            "classified": 0,
            "failed": 0
        }
    
    print(f"Found {len(images_to_classify)} images to classify (out of {len(images)} total)")
    
    # Extract image URLs
    image_urls = [img.image_url for img in images_to_classify]
    image_map = {img.image_url: img for img in images_to_classify}
    
    # Classify images
    print(f"Starting classification with batch size {batch_size}...")
    results = classify_images(image_urls, batch_size=batch_size)
    
    # Update database
    classified_count = 0
    failed_count = 0
    
    for result in results:
        image_url = result.get("image_url")
        if not image_url:
            continue
        
        image = image_map.get(image_url)
        if not image:
            continue
        
        if "error" in result:
            print(f"  ✗ Failed to classify {image_url[:60]}...: {result.get('error')}")
            failed_count += 1
            continue
        
        tags = result.get("tags", [])
        confidence = result.get("confidence", 0.0)
        quality_score = result.get("quality_score", 0.0)
        
        # Update in database
        success = repo.update_image_classification(
            image_id=image.id,
            tags=tags,
            confidence=confidence,
            quality_score=quality_score,
            method="ai_vision"
        )
        
        if success:
            classified_count += 1
            print(f"  ✓ Classified: {image_url[:60]}... (tags: {', '.join(tags)}, confidence: {confidence:.2f}, quality: {quality_score:.2f})")
        else:
            failed_count += 1
            print(f"  ✗ Failed to update database for {image_url[:60]}...")

    # Auto-hide low-quality and uncategorized images
    auto_hidden_count = 0
    for result in results:
        image_url = result.get("image_url")
        if not image_url or "error" in result:
            continue

        image = image_map.get(image_url)
        if not image:
            continue

        tags = result.get("tags", [])
        quality_score = result.get("quality_score", 0.0)

        should_hide = False
        hide_reason = ""

        # Auto-hide if quality is below threshold
        if quality_score < AUTO_HIDE_QUALITY_THRESHOLD:
            should_hide = True
            hide_reason = f"quality {quality_score:.2f} < {AUTO_HIDE_QUALITY_THRESHOLD}"

        # Auto-hide if uncategorized AND low confidence (likely not a useful property photo)
        if not tags and result.get("confidence", 0.0) < 0.3:
            should_hide = True
            hide_reason = "uncategorized with low confidence"

        if should_hide and not image.is_hidden:
            success = repo.update_image_visibility(image.id, True)
            if success:
                auto_hidden_count += 1
                print(f"  👁 Auto-hidden: {image_url[:60]}... ({hide_reason})")

    print(f"\n✓ Classification complete!")
    print(f"  Total images: {len(images)}")
    print(f"  Images to classify: {len(images_to_classify)}")
    print(f"  Successfully classified: {classified_count}")
    print(f"  Failed: {failed_count}")
    if auto_hidden_count > 0:
        print(f"  Auto-hidden (low quality): {auto_hidden_count}")

    return {
        "total_images": len(images),
        "images_to_classify": len(images_to_classify),
        "classified": classified_count,
        "failed": failed_count,
        "auto_hidden": auto_hidden_count
    }


def get_tool_definition():
    """Returns the tool definition for OpenAI function calling."""
    return {
        "type": "function",
        "function": {
            "name": "bulk_classify_images",
            "description": "Bulk classify all unclassified images for a property (or all properties). Processes images in batches to respect rate limits. Can re-classify existing images if force_reclassify is True. Use this when user asks to 'bulk classify images' or 'classify all images' for a property. Accepts either property_id (UUID) or url (website URL) to identify the property.",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "string",
                        "description": "Property ID (UUID) to classify images for. If not provided, will classify images for all properties."
                    },
                    "url": {
                        "type": "string",
                        "description": "Property website URL to find property and classify its images. Alternative to property_id. If both are provided, property_id takes precedence."
                    },
                    "force_reclassify": {
                        "type": "boolean",
                        "description": "If True, re-classify images that already have classifications. Default: False (only classify unclassified images).",
                        "default": False
                    },
                    "batch_size": {
                        "type": "integer",
                        "description": "Number of images to process per batch (default: 5)",
                        "default": 5
                    },
                    "max_images": {
                        "type": "integer",
                        "description": "Maximum number of images to process. If not provided, processes all images."
                    }
                },
                "required": []
            }
        }
    }


def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the bulk_classify_images tool.
    
    Args:
        arguments: Dictionary containing tool arguments
            - property_id (str, optional): Property ID (UUID) to classify images for
            - url (str, optional): Property website URL to find property and classify its images
            - force_reclassify (bool, optional): Re-classify existing images
            - batch_size (int, optional): Batch size for processing
            - max_images (int, optional): Maximum number of images to process
            
    Returns:
        Dictionary with classification statistics
    """
    property_id = arguments.get("property_id")
    url = arguments.get("url")
    force_reclassify = arguments.get("force_reclassify", False)
    batch_size = arguments.get("batch_size", 5)
    max_images = arguments.get("max_images")
    
    try:
        stats = bulk_classify_images(
            property_id=property_id,
            url=url,
            force_reclassify=force_reclassify,
            batch_size=batch_size,
            max_images=max_images
        )
        
        # Check if there was an error (e.g., property not found)
        if stats.get("error"):
            return {
                "success": False,
                "error": stats.get("error"),
                "statistics": stats,
                "message": stats.get("error")
            }
        
        return {
            "success": True,
            "statistics": stats,
            "message": f"Successfully classified {stats['classified']} images (failed: {stats['failed']})"
        }
    except Exception as e:
        print(f"Error during bulk classification: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to bulk classify images: {str(e)}"
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Bulk classify property images")
    parser.add_argument("--property-id", type=str, help="Property ID to classify images for (optional)")
    parser.add_argument("--force", action="store_true", help="Re-classify images that already have classifications")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of images per batch (default: 5)")
    parser.add_argument("--max-images", type=int, help="Maximum number of images to process")
    
    args = parser.parse_args()
    
    try:
        stats = bulk_classify_images(
            property_id=args.property_id,
            force_reclassify=args.force,
            batch_size=args.batch_size,
            max_images=args.max_images
        )
        print(f"\nFinal statistics: {stats}")
    except KeyboardInterrupt:
        print("\n\nClassification interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during bulk classification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

