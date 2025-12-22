# Image Classification Discrepancy: Unclassified vs Uncategorized

## Problem

The agent reports 4 unclassified images, but the frontend shows 12 uncategorized images. This discrepancy occurs because the backend and frontend use different definitions.

## Root Cause

### Backend Definition: "Unclassified"
The backend counts images as "unclassified" when:
- `image_tags` is `NULL` (never attempted classification)
- `image_tags` is an empty array `[]` (classification attempted but failed)

### Frontend Definition: "Uncategorized"  
The frontend shows images as "uncategorized" when:
- `image_tags` is `NULL` or empty `[]` (same as backend)
- **PLUS** images that have tags, but those tags don't match valid categories

## Why This Happens

1. **Classification Failures**: When classification fails with parsing errors, some images may have:
   - `image_tags` set to `[]` (empty array) instead of `NULL`
   - Invalid tags that don't match the predefined categories

2. **Tag Validation**: The frontend validates tags against a list of valid categories. If an image has tags like `["invalid_tag"]`, the frontend treats it as "uncategorized" because the primary tag doesn't match any valid category.

3. **Model Conversion**: When loading from the database, `NULL` values are converted to `[]` (empty arrays) in the Python model (see `backend/database/models.py` line 115), which can cause confusion.

## How to Diagnose

Run the diagnostic script to see the actual state of images:

```bash
cd backend
python3 scripts/check_image_classification_status.py --property-id <property_id>
```

Or check all properties:
```bash
python3 scripts/check_image_classification_status.py
```

This script will show:
- Images with `NULL` tags (never classified)
- Images with empty `[]` tags (classification failed)
- Images with valid tags
- Images with invalid tags (tags that don't match valid categories)

## Solutions

### Option 1: Align Backend Count with Frontend
Update the backend to also count images with invalid tags as "unclassified":

```python
# In backend code that counts unclassified images
def count_unclassified_images(property_id: str) -> int:
    images = repo.get_property_images(property_id)
    valid_categories = ["exterior", "interior", "amenities", ...]
    
    unclassified = 0
    for image in images:
        tags = image.image_tags or []
        # Count as unclassified if:
        # 1. No tags at all
        # 2. Tags don't match valid categories
        if not tags or not any(tag in valid_categories for tag in tags):
            unclassified += 1
    
    return unclassified
```

### Option 2: Clean Up Invalid Tags
Re-classify images that have invalid tags:

```bash
cd backend
python3 tools/bulk_classify_images.py --property-id <property_id> --force
```

### Option 3: Fix Classification Failures
Investigate why 8 images failed classification and fix the parsing errors. Check the classification logs for details about parsing errors.

## Quick Fix

To see the actual count matching what the frontend shows, you can query the database directly:

```sql
-- Count images that would show as "uncategorized" in frontend
SELECT COUNT(*) 
FROM property_images 
WHERE property_id = '<property_id>'
  AND (
    image_tags IS NULL 
    OR image_tags = '[]'::jsonb
    OR NOT EXISTS (
      SELECT 1 FROM jsonb_array_elements_text(image_tags) AS tag
      WHERE tag IN ('exterior', 'interior', 'amenities', 'outdoor_spaces', 
                    'common_areas', 'lifestyle', 'floor_plans', 
                    'virtual_tours', 'marketing')
    )
  );
```

## Next Steps

1. Run the diagnostic script to identify the exact issue
2. Decide which solution to implement (align counts, clean tags, or fix classification)
3. Update the backend counting logic if needed
4. Consider adding validation to prevent invalid tags from being saved


