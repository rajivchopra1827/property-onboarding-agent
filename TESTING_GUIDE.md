# Testing Guide for Split Tools Implementation

This guide will help you verify that the changes are working correctly.

## Prerequisites

Before testing, make sure you have:

1. **All dependencies installed:**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **All API keys set:**
   ```bash
   export OPENAI_API_KEY='your-openai-api-key'
   export APIFY_API_TOKEN='your-apify-api-token'
   ```
   
   Or in your `.env.local` or `.env` file:
   ```
   OPENAI_API_KEY=your-openai-api-key
   APIFY_API_TOKEN=your-apify-api-token
   ```

## Test 1: Verify crawl_property_website returns markdown only (no images)

**Goal:** Confirm that the crawl tool no longer returns images.

1. Start FionaFast:
   ```bash
   python3 fiona_fast.py
   ```

2. Test crawling a website:
   ```
   You: crawl https://www.villasattowngate.com
   ```

3. **What to check:**
   - ✅ Tool should crawl and return markdown content
   - ✅ Response should NOT include an "images" field
   - ✅ Console output should say something like "Successfully crawled X pages, Y total characters of markdown content"
   - ✅ Should NOT mention images in the success message

4. **Expected output structure:**
   ```json
   {
     "markdown": "...",
     "cache_info": {...}
   }
   ```
   - Should NOT have an "images" key

## Test 2: Verify extract_website_images works independently

**Goal:** Confirm the new image extraction tool works correctly.

1. In the same FionaFast session (or start a new one), test image extraction:
   ```
   You: extract images from https://www.villasattowngate.com
   ```

2. **What to check:**
   - ✅ Tool should run Apify Actor successfully
   - ✅ Should return a list of images
   - ✅ Console should show "Running Apify Actor: gomorrhadev/website-image-scraper..."
   - ✅ Console should show "Successfully extracted X images"
   - ✅ Each image should have: `url`, `page_url`, `alt`, `width`, `height`

3. **Expected output structure:**
   ```json
   {
     "images": [
       {
         "url": "https://example.com/image.jpg",
         "page_url": "https://example.com/page",
         "alt": null,
         "width": null,
         "height": null
       }
     ],
     "cache_info": {...}
   }
   ```

## Test 3: Verify caching works for both tools independently

**Goal:** Confirm that markdown and images are cached separately.

### Test 3a: Markdown caching

1. First crawl (fresh):
   ```
   You: crawl https://www.villasattowngate.com
   ```
   - Should crawl fresh and cache markdown

2. Second crawl (should use cache):
   ```
   You: crawl https://www.villasattowngate.com
   ```
   - Should prompt about cache or use cache if `use_cache=True`
   - Should say "Using cached data" or "USING CACHE"

### Test 3b: Images caching

1. First image extraction (fresh):
   ```
   You: extract images from https://www.villasattowngate.com
   ```
   - Should extract fresh and cache images

2. Second image extraction (should use cache):
   ```
   You: extract images from https://www.villasattowngate.com
   ```
   - Should prompt about cache or use cache if `use_cache=True`
   - Should say "Using cached images" or "USING CACHE"

### Test 3c: Independent caches

1. Clear markdown cache but keep images cache (or vice versa)
2. Verify that:
   - If markdown cache is cleared, `crawl_property_website` crawls fresh
   - If images cache exists, `extract_website_images` can still use it
   - Caches don't affect each other

## Test 4: Verify tools work together

**Goal:** Confirm both tools can be used in sequence.

1. Extract markdown:
   ```
   You: crawl https://www.villasattowngate.com
   ```

2. Extract images:
   ```
   You: extract images from https://www.villasattowngate.com
   ```

3. Extract property information (should use cached markdown):
   ```
   You: extract property information from https://www.villasattowngate.com
   ```

4. **What to check:**
   - ✅ All three tools should work independently
   - ✅ Property extraction should use cached markdown (faster)
   - ✅ No errors or conflicts between tools

## Test 5: Verify error handling

### Test 5a: Missing Apify API token

1. Temporarily unset Apify token:
   ```bash
   unset APIFY_API_TOKEN
   ```

2. Try to crawl a website or extract images:
   ```
   You: crawl https://www.villasattowngate.com
   ```
   or
   ```
   You: extract images from https://www.villasattowngate.com
   ```

3. **What to check:**
   - ✅ Should show clear error message about missing APIFY_API_TOKEN
   - ✅ Should NOT crash the application
   - ✅ Should return error in result, not raise exception

### Test 5b: Invalid URL

1. Try with invalid URL:
   ```
   You: extract images from https://invalid-url-that-does-not-exist.com
   ```

2. **What to check:**
   - ✅ Should handle error gracefully
   - ✅ Should return error message, not crash

## Test 6: Verify cache files are separate

**Goal:** Confirm markdown and images use different cache files.

1. After running both tools on a website, check the cache directory:
   ```bash
   ls -la cache/
   ```

2. **What to check:**
   - ✅ Should see `{domain}.json` for markdown cache
   - ✅ Should see `{domain}_images.json` for images cache
   - ✅ Both files should exist independently

3. Inspect the cache files:
   ```bash
   cat cache/villasattowngate_com.json  # Markdown cache
   cat cache/villasattowngate_com_images.json  # Images cache
   ```

4. **What to check:**
   - ✅ Markdown cache should have `pages` with `markdown` content
   - ✅ Images cache should have `images` array
   - ✅ Structure should match expected format

## Test 7: Verify tool definitions are correct

**Goal:** Confirm the AI agent knows about both tools.

1. Ask about capabilities:
   ```
   You: What tools do you have available?
   ```

2. **What to check:**
   - ✅ Should mention `crawl_property_website` (for markdown)
   - ✅ Should mention `extract_website_images` (for images)
   - ✅ Should mention `extract_property_information`
   - ✅ Should explain when to use each tool

## Quick Test Checklist

Run through this checklist to verify everything works:

- [ ] `crawl_property_website` returns markdown only (no images)
- [ ] `extract_website_images` returns images list
- [ ] Markdown caching works independently
- [ ] Images caching works independently
- [ ] Both tools can be used together
- [ ] Error handling works (missing API keys, invalid URLs)
- [ ] Cache files are separate (`{domain}.json` vs `{domain}_images.json`)
- [ ] System prompt mentions all three tools correctly
- [ ] No console errors or warnings

## Common Issues and Solutions

### Issue: "APIFY_API_TOKEN not found"
**Solution:** Make sure you've set the Apify API token in your environment or `.env` file. The same token is used for both website crawling and image extraction.

### Issue: "No images found"
**Solution:** 
- Check that the website actually has images
- Verify Apify Actor ran successfully (check console output)
- Try a different website to test

### Issue: Cache not working
**Solution:**
- Check that cache directory exists and is writable
- Verify cache files are being created in `cache/` directory
- Check cache age (caches expire after 24 hours by default)

### Issue: Tools not found
**Solution:**
- Make sure you've restarted FionaFast after the changes
- Verify `tools/__init__.py` includes the new tool
- Check for any import errors in the console

## Success Criteria

The implementation is successful if:

1. ✅ `crawl_property_website` only returns markdown (no images)
2. ✅ `extract_website_images` successfully extracts images using Apify
3. ✅ Both tools cache independently
4. ✅ Both tools can be used together without conflicts
5. ✅ Error handling works gracefully
6. ✅ Cache files are separate and correct
7. ✅ System prompt correctly describes all tools

