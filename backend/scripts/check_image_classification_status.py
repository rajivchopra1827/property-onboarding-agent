#!/usr/bin/env python3
"""
Script to check the actual classification status of images in the database.
Helps diagnose discrepancies between "unclassified" and "uncategorized" counts.
"""

import sys
import os

# Add parent directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from database import PropertyRepository
from database.supabase_client import get_supabase_client


def check_image_classification_status(property_id: str = None):
    """
    Check the classification status of images and identify discrepancies.
    
    Args:
        property_id: Optional property ID to check. If None, checks all properties.
    """
    repo = PropertyRepository()
    client = get_supabase_client()
    
    # Build query
    query = client.table("property_images").select("*")
    
    if property_id:
        query = query.eq("property_id", property_id)
    
    response = query.execute()
    
    if not response.data:
        print("No images found.")
        return
    
    images = response.data
    print(f"\nTotal images found: {len(images)}\n")
    
    # Categorize images
    never_classified = []  # image_tags is NULL
    empty_tags = []  # image_tags is []
    has_tags = []  # image_tags has values
    has_errors = []  # classification attempted but failed
    
    for img in images:
        image_tags = img.get("image_tags")
        image_id = img.get("id")
        image_url = img.get("image_url", "")[:60]
        
        # Check if image_tags is NULL (never classified)
        if image_tags is None:
            never_classified.append({
                "id": image_id,
                "url": image_url,
                "classified_at": img.get("classified_at"),
                "classification_method": img.get("classification_method")
            })
        # Check if image_tags is empty array
        elif isinstance(image_tags, list) and len(image_tags) == 0:
            empty_tags.append({
                "id": image_id,
                "url": image_url,
                "classified_at": img.get("classified_at"),
                "classification_method": img.get("classification_method"),
                "confidence": img.get("classification_confidence")
            })
        # Check if has tags
        elif isinstance(image_tags, list) and len(image_tags) > 0:
            has_tags.append({
                "id": image_id,
                "url": image_url,
                "tags": image_tags,
                "confidence": img.get("classification_confidence")
            })
        else:
            # Unexpected format
            print(f"⚠ Unexpected image_tags format for {image_id}: {type(image_tags)}")
    
    # Print summary
    print("=" * 80)
    print("CLASSIFICATION STATUS SUMMARY")
    print("=" * 80)
    print(f"\nNever classified (NULL tags): {len(never_classified)}")
    print(f"Empty tags ([]): {len(empty_tags)}")
    print(f"Has tags: {len(has_tags)}")
    print(f"\nTotal 'unclassified' (NULL + empty): {len(never_classified) + len(empty_tags)}")
    print(f"Total 'uncategorized' (what frontend shows): {len(never_classified) + len(empty_tags)}")
    
    # Show details
    if never_classified:
        print(f"\n{'='*80}")
        print(f"NEVER CLASSIFIED ({len(never_classified)} images):")
        print("=" * 80)
        for img in never_classified[:10]:  # Show first 10
            print(f"  - {img['url']}...")
            if img.get("classified_at"):
                print(f"    (classified_at: {img['classified_at']}, method: {img.get('classification_method')})")
        if len(never_classified) > 10:
            print(f"  ... and {len(never_classified) - 10} more")
    
    if empty_tags:
        print(f"\n{'='*80}")
        print(f"EMPTY TAGS ({len(empty_tags)} images):")
        print("=" * 80)
        for img in empty_tags[:10]:  # Show first 10
            print(f"  - {img['url']}...")
            if img.get("classified_at"):
                print(f"    (classified_at: {img['classified_at']}, method: {img.get('classification_method')})")
            if img.get("confidence") is not None:
                print(f"    (confidence: {img['confidence']})")
        if len(empty_tags) > 10:
            print(f"  ... and {len(empty_tags) - 10} more")
    
    # Check for images with invalid tags (not in valid categories)
    # Valid categories from the system (uncategorized is not a selectable tag)
    valid_categories = [
        "floor_plans", "amenities", "common_areas", "lifestyle",
        "exterior", "outdoor_spaces"
    ]
    
    if has_tags:
        
        invalid_tag_images = []
        for img in has_tags:
            tags = img.get("image_tags", [])
            invalid_tags = [tag for tag in tags if tag not in valid_categories]
            if invalid_tags:
                invalid_tag_images.append({
                    "id": img["id"],
                    "url": img.get("image_url", "N/A"),
                    "invalid_tags": invalid_tags,
                    "all_tags": tags
                })
        
        if invalid_tag_images:
            print(f"\n{'='*80}")
            print(f"IMAGES WITH INVALID TAGS ({len(invalid_tag_images)} images):")
            print("=" * 80)
            print("These have tags that don't match valid categories, so frontend shows them as 'uncategorized'")
            for img in invalid_tag_images[:5]:
                print(f"  - {img['url']}...")
                print(f"    Invalid tags: {img['invalid_tags']}")
                print(f"    All tags: {img['all_tags']}")
            if len(invalid_tag_images) > 5:
                print(f"  ... and {len(invalid_tag_images) - 5} more")
    
    print(f"\n{'='*80}")
    print("DIAGNOSIS:")
    print("=" * 80)
    print(f"\nBackend counts 'unclassified' as: images with NULL or empty [] tags")
    print(f"  = {len(never_classified)} (NULL) + {len(empty_tags)} (empty) = {len(never_classified) + len(empty_tags)}")
    print(f"\nFrontend shows 'uncategorized' as: images with no valid primary tag")
    print(f"  = {len(never_classified)} (NULL) + {len(empty_tags)} (empty) + {len(invalid_tag_images) if 'invalid_tag_images' in locals() else 0} (invalid tags)")
    
    if 'invalid_tag_images' in locals() and len(invalid_tag_images) > 0:
        print(f"\n⚠ DISCREPANCY FOUND:")
        print(f"  The frontend is showing {len(invalid_tag_images)} additional images as 'uncategorized'")
        print(f"  because they have tags that don't match valid categories.")
        print(f"  These images are NOT counted as 'unclassified' by the backend.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check image classification status")
    parser.add_argument("--property-id", type=str, help="Property ID to check (optional)")
    
    args = parser.parse_args()
    
    try:
        check_image_classification_status(property_id=args.property_id)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

