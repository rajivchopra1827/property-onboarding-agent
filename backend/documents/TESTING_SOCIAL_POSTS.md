# Testing Guide: Social Media Post Generator

This guide explains how to test the `generate_social_posts` tool.

## Quick Start

**Easiest way to test:**

```bash
cd backend
python3 test_social_posts.py [property_id] [post_count]
```

Example:
```bash
python3 test_social_posts.py abc-123-def-456 5
```

The script will:
- Check if property exists
- Verify required data (images, etc.)
- Generate posts
- Show results and example post

## Prerequisites

### 1. Run Database Migration

**IMPORTANT:** You must run the database migration first to create the `property_social_posts` table:

```bash
# If using local Supabase, migrations run automatically when you start Supabase
npx supabase start

# Or manually apply the migration:
# The migration file is at: supabase/migrations/20251222000003_add_property_social_posts_table.sql
```

### 2. Install Dependencies

Make sure Pillow is installed:

```bash
cd backend
pip install -r requirements.txt
```

### 3. Property Data

Before testing, ensure you have:

1. **A property in the database** with at least:
   - Basic property information (name, address, etc.)
   - **Images extracted** (required - tool will fail without images)
   - **Brand identity extracted** (optional but recommended for better results)

2. **Optional but recommended data:**
   - Amenities
   - Floor plans
   - Special offers
   - Reviews summary

3. **Environment variables set:**
   - `OPENAI_API_KEY` - Required for AI generation
   - `SUPABASE_URL` and `SUPABASE_KEY` - Required for database access

## Method 1: Direct Python Testing

Create a test script to call the tool directly:

```python
# test_social_posts.py
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_file = Path(".env.local") or Path(".env")
if env_file.exists():
    load_dotenv(env_file)

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from tools.generate_social_posts import execute

# Replace with an actual property ID from your database
PROPERTY_ID = "your-property-id-here"

# Test with default settings (8 posts)
result = execute({
    "property_id": PROPERTY_ID,
    "post_count": 8
})

print("\n" + "="*60)
print("RESULT:")
print("="*60)
print(f"Generated {result.get('count', 0)} posts")
print(f"Property ID: {result.get('property_id')}")

if result.get("error"):
    print(f"ERROR: {result.get('error')}")
else:
    posts = result.get("posts", [])
    for i, post in enumerate(posts, 1):
        print(f"\n--- Post {i} ---")
        print(f"Theme: {post.get('theme')}")
        print(f"Image: {post.get('image_url')}")
        print(f"Caption: {post.get('caption')[:100]}...")
        print(f"Hashtags: {', '.join(post.get('hashtags', [])[:5])}...")
        print(f"CTA: {post.get('cta')}")
        print(f"Mockup: {post.get('mockup_image_url')}")
```

Run it:
```bash
cd backend
python3 test_social_posts.py
```

## Method 2: Via CLI Agent

Use the FionaFast CLI agent:

```bash
cd backend
python3 fiona_fast.py
```

Then in the conversation, say:
```
Generate 8 social media posts for property [property-id]
```

Or:
```
Use generate_social_posts tool with property_id [property-id] and post_count 5
```

## Method 3: Check Database Directly

After running the tool, verify posts were saved:

1. **Via Supabase Studio:**
   - Open `http://127.0.0.1:54323` (local Supabase Studio)
   - Navigate to `property_social_posts` table
   - Filter by `property_id` to see generated posts

2. **Via Python:**
```python
from database import PropertyRepository

repo = PropertyRepository()
posts = repo.get_property_social_posts("your-property-id")

for post in posts:
    print(f"Post ID: {post.id}")
    print(f"Theme: {post.theme}")
    print(f"Caption: {post.caption[:100]}...")
    print(f"Ready to post:\n{post.ready_to_post_text[:200]}...")
    print("-" * 60)
```

## What to Verify

### 1. **Posts Generated Successfully**
- Check that `result.get('count')` matches requested number
- Verify no errors in the result

### 2. **Post Content Quality**
- **Captions:** Should match brand tone, be 150-300 words, include property-specific info
- **Hashtags:** Should include property name, location, theme-specific tags (10-15 total)
- **CTAs:** Should vary across posts (no repetition)
- **Themes:** Should be distributed across available themes

### 3. **Database Storage**
- Posts saved to `property_social_posts` table
- All fields populated (caption, hashtags, CTA, ready_to_post_text, structured_data)
- Mockup images created (check `mockup_image_url` field)

### 4. **Visual Mockups**
- Check `backend/mockups/` directory for generated PNG files
- Mockups should be 1080x1080px (Instagram square format)
- Should have brand-colored border
- Should have caption preview overlay at bottom

### 5. **Image Selection**
- Each post should use a different image (no duplicates)
- Images should be relevant to the theme
- Hidden images should be excluded

## Troubleshooting

### Error: "No images found for this property"
**Solution:** Extract images first using `extract_website_images` tool

### Error: "Property with ID X not found"
**Solution:** Verify the property exists in the database. Check `properties` table.

### Mockups not generating
**Possible causes:**
- Image URLs are invalid or inaccessible
- Pillow library not installed (`pip install Pillow`)
- Network issues downloading images

### Captions seem generic
**Solution:** Ensure brand identity is extracted first. The tool uses brand tone to match writing style.

### All posts use same theme
**Solution:** Check that `post_count` is high enough to distribute across themes. With 6 themes, you need at least 6 posts to see all themes.

## Example Test Flow

1. **Onboard a property** (if not already done):
   ```
   Onboard property from https://example-property.com
   ```

2. **Extract brand identity** (if not already done):
   ```
   Extract brand identity from https://example-property.com
   ```

3. **Get the property ID:**
   - Check Supabase Studio `properties` table
   - Or query: `SELECT id, property_name FROM properties WHERE website_url = 'https://example-property.com';`

4. **Generate posts:**
   ```python
   from tools.generate_social_posts import execute
   result = execute({"property_id": "your-id-here", "post_count": 8})
   ```

5. **Verify results:**
   - Check console output for success messages
   - Verify posts in database
   - Check mockup images in `backend/mockups/` directory

## Expected Output

When successful, you should see:
```
Generating 8 social media posts for property abc-123-def-456
📊 Collecting property data...
✓ Collected data: 25 images, branding: yes
✓ Theme distribution: ['lifestyle', 'amenities', 'floor_plans', 'special_offers', 'reviews', 'location', 'lifestyle', 'amenities']

📝 Generating post 1/8 (theme: lifestyle)...
✓ Post 1 created (ID: xyz-789-abc-123)

📝 Generating post 2/8 (theme: amenities)...
✓ Post 2 created (ID: xyz-789-abc-124)

...

✅ Successfully generated 8 posts
```

## Next Steps

After testing:
- Review generated posts in database
- Check mockup images for visual quality
- Adjust brand colors/fonts if needed
- Consider adding more property data (amenities, offers) for richer captions

