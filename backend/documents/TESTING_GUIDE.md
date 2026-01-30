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

## Test 1: Start FastAPI Server and Verify Health

**Goal:** Verify the API server is running correctly.

1. Start the FastAPI server:
   ```bash
   cd backend
   python -m api.server
   ```

2. Test health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status": "healthy"}`

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

1. Test image extraction via onboarding workflow:
   ```bash
   curl -X POST http://localhost:8000/api/onboard \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.villasattowngate.com"}'
   ```
   Images extraction runs automatically as part of the workflow (parallel step 2).

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

1. First onboarding (fresh):
   ```bash
   curl -X POST http://localhost:8000/api/onboard \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.villasattowngate.com"}'
   ```
   - Should crawl fresh and cache markdown

2. Second onboarding (should use cache if < 12 hours old):
   ```bash
   curl -X POST http://localhost:8000/api/onboard \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.villasattowngate.com"}'
   ```
   - Should use cached markdown (faster)
   - Workflow makes cache decision upfront

### Test 3b: Force refresh

1. Force refresh (ignore cache):
   ```bash
   curl -X POST http://localhost:8000/api/onboard \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.villasattowngate.com", "force_reonboard": true}'
   ```
   - Should ignore cache and crawl fresh

### Test 3c: Independent caches

1. Clear markdown cache but keep images cache (or vice versa)
2. Verify that:
   - If markdown cache is cleared, `crawl_property_website` crawls fresh
   - If images cache exists, `extract_website_images` can still use it
   - Caches don't affect each other

## Test 4: Verify workflow execution

**Goal:** Confirm the full onboarding workflow executes all steps correctly.

1. Start onboarding:
   ```bash
   curl -X POST http://localhost:8000/api/onboard \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.villasattowngate.com"}'
   ```

2. Monitor progress:
   ```bash
   # Get session_id from response, then check status
   curl http://localhost:8000/api/onboard/{session_id}/status
   ```

3. **What to check:**
   - ✅ All 8 extraction steps should complete
   - ✅ Parallel steps (images, amenities, etc.) should complete around the same time
   - ✅ Sequential steps (reviews, competitors) should run after parallel group
   - ✅ Final status should be "completed"
   - ✅ Property ID should be populated

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

## Test 7: Verify API endpoints

**Goal:** Confirm all API endpoints work correctly.

1. **Health check:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Missing extractions:**
   ```bash
   curl http://localhost:8000/api/properties/{property_id}/missing-extractions
   ```

3. **Force re-onboarding:**
   ```bash
   curl -X POST http://localhost:8000/api/properties/{property_id}/force-reonboard
   ```

4. **What to check:**
   - ✅ All endpoints should return valid JSON
   - ✅ Missing extractions should return correct list
   - ✅ Force re-onboarding should create new session

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

