# Testing Guide for Google Maps Reviews Scraper

This guide will help you verify that the reviews extraction tool is working correctly.

## Prerequisites

Before testing, make sure you have:

1. **Database migration applied:**
   ```bash
   # Make sure Supabase is running
   npx supabase start
   
   # The migration should run automatically, but you can verify:
   npx supabase migration list
   ```
   - ✅ Should see `20251221180852_add_property_reviews_tables.sql` in the list

2. **All dependencies installed:**
   ```bash
   cd backend
   pip3 install -r requirements.txt
   ```
   - ✅ Should include `python-dateutil>=2.8.0`

3. **All API keys set:**
   ```bash
   export OPENAI_API_KEY='your-openai-api-key'
   export APIFY_API_TOKEN='your-apify-api-token'
   ```
   
   Or in your `.env.local` or `.env` file:
   ```
   OPENAI_API_KEY=your-openai-api-key
   APIFY_API_TOKEN=your-apify-api-token
   ```

4. **Property already onboarded:**
   - The reviews tool needs a property in the database with at least a name
   - If testing standalone, make sure you've run `extract_property_information` first

## Test 1: Verify Database Tables Exist

**Goal:** Confirm the migration created the necessary tables.

1. Check Supabase Studio (http://127.0.0.1:54323) or use SQL:
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name IN ('property_reviews_summary', 'property_reviews');
   ```

2. **What to check:**
   - ✅ Both `property_reviews_summary` and `property_reviews` tables should exist
   - ✅ `property_reviews` should have unique constraint on `(property_id, review_id)`
   - ✅ Indexes should be created for performance

## Test 2: Extract Reviews for Existing Property (Standalone)

**Goal:** Test the reviews tool directly with a property that exists in the database.

1. **First, ensure you have a property in the database:**
   ```bash
   # Start onboarding workflow via API
   curl -X POST http://localhost:8000/api/onboard \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.villasattowngate.com"}'
   ```
   - This creates the property record needed for reviews
   - Wait for onboarding to complete, or use individual extraction endpoint

2. **Extract reviews via API:**
   ```bash
   # Use the individual extraction endpoint (if available)
   # Or wait for full onboarding workflow to complete reviews step
   ```

3. **What to check:**
   - ✅ Tool should search Google Maps using property name/address
   - ✅ Console should show "Constructed Google Maps search URL: ..."
   - ✅ Console should show "Running Apify Actor: compass/google-maps-reviews-scraper..."
   - ✅ Console should show "Found X reviews from Apify Actor"
   - ✅ Console should show "Added X new reviews to database"
   - ✅ Should display overall rating and review count

4. **Expected output structure:**
   ```json
   {
     "overall_rating": 4.5,
     "review_count": 150,
     "reviews_added": 100,
     "reviews_scraped": 100,
     "google_maps_place_id": "ChIJ...",
     "google_maps_url": "https://www.google.com/maps/..."
   }
   ```

## Test 3: Extract Reviews Through Onboarding Flow

**Goal:** Verify reviews are extracted as part of the full onboarding workflow.

1. Start onboarding workflow:
   ```bash
   curl -X POST http://localhost:8000/api/onboard \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.villasattowngate.com"}'
   ```

2. Monitor workflow progress:
   ```bash
   # Get session_id from response, then check status
   curl http://localhost:8000/api/onboard/{session_id}/status
   ```

3. **What to check:**
   - ✅ Reviews extraction should run automatically
   - ✅ Should appear in the extraction sequence
   - ✅ Summary should include review count and rating
   - ✅ Console should show review extraction progress

4. **Expected summary output:**
   ```
   Statistics:
     • Property information extracted
     • X images extracted
     • X reviews (rating: 4.5/5.0)
     ...
   ```

## Test 4: Verify Database Records

**Goal:** Confirm data is correctly stored in the database.

1. **Check reviews summary:**
   ```sql
   SELECT * FROM property_reviews_summary 
   WHERE property_id = 'your-property-id';
   ```
   or in Supabase Studio, navigate to `property_reviews_summary` table

2. **What to check:**
   - ✅ Should have one record per property
   - ✅ `overall_rating` should be a number between 0-5
   - ✅ `review_count` should match the number of reviews
   - ✅ `google_maps_place_id` and `google_maps_url` should be populated

3. **Check individual reviews:**
   ```sql
   SELECT 
     reviewer_name, 
     stars, 
     review_text, 
     published_at,
     is_local_guide
   FROM property_reviews 
   WHERE property_id = 'your-property-id'
   ORDER BY published_at DESC
   LIMIT 10;
   ```

4. **What to check:**
   - ✅ Should have multiple review records
   - ✅ Each review should have `review_id` (unique)
   - ✅ `reviewer_name`, `stars`, `review_text` should be populated
   - ✅ `published_at` should be a valid date
   - ✅ Reviews should be ordered by date (newest first)

## Test 5: Test Incremental Updates (No Duplicates)

**Goal:** Verify that running the tool twice doesn't create duplicate reviews.

1. **First run:**
   ```
   You: extract reviews from https://www.villasattowngate.com
   ```
   - Note the number of reviews added

2. **Second run (immediately after):**
   ```
   You: extract reviews from https://www.villasattowngate.com
   ```

3. **What to check:**
   - ✅ Console should show "Added 0 new reviews to database (skipped X duplicates)"
   - ✅ Database should NOT have duplicate reviews
   - ✅ Review count should remain the same

4. **Verify in database:**
   ```sql
   SELECT COUNT(*) as total_reviews,
          COUNT(DISTINCT review_id) as unique_reviews
   FROM property_reviews 
   WHERE property_id = 'your-property-id';
   ```
   - ✅ `total_reviews` should equal `unique_reviews`

## Test 6: Test with Direct Google Maps URL

**Goal:** Verify the tool works when providing a direct Google Maps URL.

1. Find a property's Google Maps URL (e.g., from Google Maps search)

2. Extract reviews with direct URL:
   ```
   You: extract reviews with Google Maps URL https://www.google.com/maps/place/...
   ```
   (The tool should accept `google_maps_url` parameter)

3. **What to check:**
   - ✅ Should skip the search step
   - ✅ Console should show "Using provided Google Maps URL: ..."
   - ✅ Should scrape reviews directly from that URL

## Test 7: Test Error Handling

### Test 7a: Property Not Found

1. Try extracting reviews without a property in database:
   ```
   You: extract reviews from https://nonexistent-property.com
   ```

2. **What to check:**
   - ✅ Should return error: "Property not found. Please provide either property_id or url..."
   - ✅ Should NOT crash

### Test 7b: Property Without Name

1. Create a property record without a name (manually in database or via incomplete extraction)

2. Try extracting reviews:
   ```
   You: extract reviews from [url]
   ```

3. **What to check:**
   - ✅ Should return error: "Property name is required to search Google Maps..."
   - ✅ Should suggest extracting property information first

### Test 7c: Property Not on Google Maps

1. Try with a property that doesn't exist on Google Maps (or use a test property)

2. **What to check:**
   - ✅ Should handle gracefully
   - ✅ Should return: "No reviews found for this property on Google Maps."
   - ✅ Should NOT crash

### Test 7d: Missing Apify API Token

1. Temporarily unset Apify token:
   ```bash
   unset APIFY_API_TOKEN
   ```

2. Try extracting reviews:
   ```
   You: extract reviews from https://www.villasattowngate.com
   ```

3. **What to check:**
   - ✅ Should show clear error about missing APIFY_API_TOKEN
   - ✅ Should NOT crash

## Test 8: Verify Review Data Quality

**Goal:** Check that review data is complete and accurate.

1. Query a sample review:
   ```sql
   SELECT 
     reviewer_name,
     stars,
     LEFT(review_text, 100) as review_preview,
     published_at,
     is_local_guide,
     response_from_owner_text IS NOT NULL as has_response
   FROM property_reviews 
   WHERE property_id = 'your-property-id'
   LIMIT 5;
   ```

2. **What to check:**
   - ✅ `reviewer_name` should be populated (if personalData=true)
   - ✅ `stars` should be between 1-5
   - ✅ `review_text` should contain actual review content
   - ✅ `published_at` should be a valid date
   - ✅ `is_local_guide` should be boolean
   - ✅ Some reviews may have `response_from_owner_text`

3. **Check review images:**
   ```sql
   SELECT 
     review_id,
     review_image_urls
   FROM property_reviews 
   WHERE review_image_urls IS NOT NULL 
   AND jsonb_array_length(review_image_urls) > 0
   LIMIT 5;
   ```
   - ✅ Reviews with images should have URLs in `review_image_urls` array

## Test 9: Test with Different max_reviews Values

**Goal:** Verify the max_reviews parameter works correctly.

1. Extract with limit:
   ```
   You: extract 50 reviews from https://www.villasattowngate.com
   ```
   (The tool should accept `max_reviews` parameter)

2. **What to check:**
   - ✅ Should only scrape up to the specified number
   - ✅ Console should show the correct count

## Test 10: Verify Tool Integration

**Goal:** Confirm the tool is properly registered and available.

1. Ask about capabilities:
   ```
   You: What tools do you have available?
   ```

2. **What to check:**
   - ✅ Should mention `extract_reviews` or "Google Maps reviews"
   - ✅ Should explain when to use it

3. Check tool definition:
   ```python
   # In Python console or test script
   from backend.tools.extract_reviews import get_tool_definition
   print(get_tool_definition())
   ```
   - ✅ Should return valid tool definition with correct parameters

## Quick Test Checklist

Run through this checklist to verify everything works:

- [ ] Database tables exist (`property_reviews_summary`, `property_reviews`)
- [ ] Can extract reviews standalone for existing property
- [ ] Reviews are extracted during full onboarding
- [ ] Reviews summary is saved to database
- [ ] Individual reviews are saved to database
- [ ] No duplicate reviews on second run (incremental updates work)
- [ ] Overall rating and review count are correct
- [ ] Review data is complete (name, text, stars, date)
- [ ] Error handling works (missing property, no Google Maps listing)
- [ ] Tool is registered and available to agent

## Common Issues and Solutions

### Issue: "Property not found"
**Solution:** 
- Make sure you've run `extract_property_information` first
- Verify the property exists in the `properties` table
- Check that the URL matches the `website_url` in the database

### Issue: "Property name is required"
**Solution:**
- The property must have a `property_name` field populated
- Run `extract_property_information` to populate property data first

### Issue: "No reviews found"
**Solution:**
- Verify the property actually exists on Google Maps
- Check that the property has reviews on Google Maps
- Try searching manually on Google Maps to confirm
- The property might not be listed or might have zero reviews

### Issue: "APIFY_API_TOKEN not found"
**Solution:** 
- Make sure you've set the Apify API token in your environment
- Verify the token is valid and has credits
- Check that `python-dateutil` is installed: `pip3 install python-dateutil`

### Issue: Database migration not applied
**Solution:**
- Run `npx supabase start` to apply migrations
- Check migration status: `npx supabase migration list`
- Manually apply if needed: `npx supabase db reset`

### Issue: Duplicate reviews appearing
**Solution:**
- Check that the unique constraint exists: `UNIQUE(property_id, review_id)`
- Verify the `review_id` field is being populated correctly
- The tool should skip duplicates automatically - check console output

### Issue: Reviews not showing in onboarding summary
**Solution:**
- Verify reviews extraction ran successfully (check console)
- Check that `onboard_property` includes "reviews" in extraction list
- Verify statistics extraction includes review counts

## Success Criteria

The implementation is successful if:

1. ✅ Database tables are created correctly
2. ✅ Reviews can be extracted standalone
3. ✅ Reviews are extracted during onboarding
4. ✅ Summary data (rating, count) is stored correctly
5. ✅ Individual reviews are stored with all fields
6. ✅ Incremental updates prevent duplicates
7. ✅ Error handling works gracefully
8. ✅ Tool is registered and available
9. ✅ Review data quality is good (complete fields)
10. ✅ Integration with onboarding flow works

## Sample Test Property

For testing, you can use properties that are known to have Google Maps listings:

- **Villas at Towngate**: https://www.villasattowngate.com
- Or search for any apartment complex on Google Maps and use its website URL

Make sure the property:
- Has a Google Maps listing
- Has reviews on Google Maps
- Has complete address information in your database


