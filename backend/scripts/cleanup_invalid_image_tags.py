#!/usr/bin/env python3
"""
Script to clean up invalid image tags from existing images in the database.

Removes 'interior', 'virtual_tours', and 'marketing' tags from images.
If an image ends up with no tags after cleanup, sets image_tags to empty array [].
"""

import sys
import os

# Add parent directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from database.supabase_client import get_supabase_client

# Valid categories (matching frontend)
VALID_CATEGORIES = [
    "floor_plans",
    "amenities",
    "common_areas",
    "lifestyle",
    "exterior",
    "outdoor_spaces"
]

# Categories to remove
INVALID_CATEGORIES = ["interior", "virtual_tours", "marketing", "uncategorized"]


def cleanup_invalid_tags(property_id: str = None, dry_run: bool = True):
    """
    Clean up invalid tags from images in the database.
    
    Args:
        property_id: Optional property ID to clean. If None, cleans all properties.
        dry_run: If True, only shows what would be changed without making updates.
    """
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
    
    if dry_run:
        print("DRY RUN MODE - No changes will be made\n")
    
    updated_count = 0
    needs_cleanup = []
    
    for img in images:
        image_id = img.get("id")
        image_tags = img.get("image_tags") or []
        
        # Filter out invalid categories
        valid_tags = [tag for tag in image_tags if tag in VALID_CATEGORIES]
        invalid_tags = [tag for tag in image_tags if tag in INVALID_CATEGORIES]
        
        # Check if cleanup is needed
        if invalid_tags or (not image_tags and len(valid_tags) == 0):
            needs_cleanup.append({
                "id": image_id,
                "property_id": img.get("property_id"),
                "current_tags": image_tags,
                "valid_tags": valid_tags,
                "invalid_tags": invalid_tags
            })
    
    if not needs_cleanup:
        print("No images need cleanup. All tags are valid.")
        return
    
    print(f"Images needing cleanup: {len(needs_cleanup)}\n")
    
    # Show what will be changed
    for item in needs_cleanup:
        print(f"Image ID: {item['id']}")
        print(f"  Property ID: {item['property_id']}")
        print(f"  Current tags: {item['current_tags']}")
        print(f"  Invalid tags to remove: {item['invalid_tags']}")
        print(f"  New tags: {item['valid_tags']}")
        print()
    
    if dry_run:
        print("\nRun with dry_run=False to apply these changes.")
        return
    
    # Apply updates
    print("\nApplying updates...\n")
    
    for item in needs_cleanup:
        try:
            update_data = {"image_tags": item['valid_tags']}
            
            result = client.table("property_images").update(update_data).eq("id", item['id']).execute()
            
            if result.data:
                updated_count += 1
                print(f"✓ Updated image {item['id']}: {item['current_tags']} → {item['valid_tags']}")
            else:
                print(f"✗ Failed to update image {item['id']}")
        except Exception as e:
            print(f"✗ Error updating image {item['id']}: {e}")
    
    print(f"\n✓ Successfully updated {updated_count} images")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up invalid image tags")
    parser.add_argument(
        "--property-id",
        type=str,
        help="Optional property ID to clean. If not provided, cleans all properties."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (default is dry-run mode)"
    )
    
    args = parser.parse_args()
    
    cleanup_invalid_tags(
        property_id=args.property_id,
        dry_run=not args.apply
    )


