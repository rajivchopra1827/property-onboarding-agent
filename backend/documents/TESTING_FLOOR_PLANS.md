# Testing Guide for Floor Plan Extraction Tool

This guide will help you test the new floor plan extraction tool.

## Prerequisites

Before testing, make sure you have:

1. **Database migration run:**
   - The migration file `supabase/migrations/20251221180000_add_property_floor_plans_table.sql` should be applied
   - If using local Supabase, migrations run automatically when you start Supabase
   - To verify, check Supabase Studio at `http://127.0.0.1:54323` and look for the `property_floor_plans` table

2. **All dependencies installed:**
   ```bash
   cd backend
   pip3 install -r requirements.txt
   ```

3. **API keys set:**
   - `OPENAI_API_KEY` - Required for extraction
   - `APIFY_API_TOKEN` - Required for website crawling
   - `SUPABASE_URL` and `SUPABASE_KEY` - Required for database storage

## Test 1: Basic Floor Plan Extraction

**Goal:** Verify the tool can extract floor plans from a property website.

1. Start FionaFast:
   ```bash
   python3 fiona_fast.py
   ```

2. Test extracting floor plans:
   ```
   You: extract floor plans from https://www.villasattowngate.com
   ```
   
   (Replace with any property website URL that has floor plan information)

3. **What to check:**
   - ✅ Tool should crawl the website (or use cached markdown)
   - ✅ Should extract floor plan information
   - ✅ Console should show extracted floor plans with details
   - ✅ Should display: name, size, bedrooms, bathrooms, price, availability

4. **Expected console output:**
   ```
   [Extracted Floor Plans Information]
   ============================================================
   
   Floor Plans (3):
     1. Studio (450 sqft, 0BR, 1BA, $1,200-$1,400, 2 available)
     2. 1BR/1BA (750 sqft, 1BR, 1BA, $1,500-$1,700, 5 available)
     3. 2BR/2BA (1100 sqft, 2BR, 2BA, $2,000-$2,300, 1 available)
   ============================================================
   ✓ Saved 3 floor plans to database (Property ID: ...)
   ```

## Test 2: Verify Price Parsing

**Goal:** Confirm that price strings are correctly parsed into numeric values.

1. Extract floor plans from a website with various price formats:
   ```
   You: extract floor plans from https://example-property.com
   ```

2. **What to check:**
   - ✅ Price strings like "$1,200-$1,500" should be parsed
   - ✅ `min_price` and `max_price` should be numeric values
   - ✅ Single prices like "$1,200" should set both min and max to the same value
   - ✅ "Starting at $1,200" should set min_price but leave max_price as null

3. **Check the database:**
   - Open Supabase Studio: `http://127.0.0.1:54323`
   - Navigate to `property_floor_plans` table
   - Verify that:
     - `price_string` contains the original text
     - `min_price` and `max_price` contain numeric values (or null)

## Test 3: Verify Cache Integration

**Goal:** Confirm the tool uses cached markdown when available.

1. First extraction (fresh crawl):
   ```
   You: extract floor plans from https://www.villasattowngate.com
   ```
   - Should crawl the website first
   - Should cache the markdown

2. Second extraction (should use cache):
   ```
   You: extract floor plans from https://www.villasattowngate.com
   ```
   - Should prompt about cache or use cached markdown
   - Should be faster (no crawling needed)

3. **What to check:**
   - ✅ First run should crawl and cache
   - ✅ Second run should use cached markdown (faster)
   - ✅ Console should show "Using cached markdown" on second run

## Test 4: Verify Database Storage

**Goal:** Confirm floor plans are saved correctly to the database.

1. Extract floor plans:
   ```
   You: extract floor plans from https://www.villasattowngate.com
   ```

2. **Check Supabase Studio:**
   - Go to `http://127.0.0.1:54323`
   - Navigate to `property_floor_plans` table
   - Click "View data" or run a query

3. **What to verify:**
   - ✅ Each floor plan should be a separate row
   - ✅ `property_id` should match the property
   - ✅ `name` should be populated
   - ✅ `size_sqft`, `bedrooms`, `bathrooms` should have values (or null if not found)
   - ✅ `price_string`, `min_price`, `max_price` should be populated (or null)
   - ✅ `available_units` or `is_available` should be populated (or null)
   - ✅ `website_url` should match the source URL

4. **Run a query to verify:**
   ```sql
   SELECT 
     name, 
     size_sqft, 
     bedrooms, 
     bathrooms, 
     price_string, 
     min_price, 
     max_price, 
     available_units,
     is_available
   FROM property_floor_plans
   ORDER BY bedrooms, min_price;
   ```

## Test 5: Test with Different Price Formats

**Goal:** Verify the tool handles various price formats correctly.

Test with properties that have different price formats:

1. **Price range:**
   ```
   You: extract floor plans from https://property-with-ranges.com
   ```
   - Should parse "$1,200-$1,500" → min: 1200, max: 1500

2. **Single price:**
   ```
   You: extract floor plans from https://property-with-single-price.com
   ```
   - Should parse "$1,200" → min: 1200, max: 1200

3. **"Starting at" price:**
   ```
   You: extract floor plans from https://property-with-starting-at.com
   ```
   - Should parse "Starting at $1,200" → min: 1200, max: null

4. **"Call for pricing":**
   ```
   You: extract floor plans from https://property-call-for-pricing.com
   ```
   - Should store price_string: "Call for pricing"
   - min_price and max_price should be null

## Test 6: Test Availability Information

**Goal:** Verify availability information is extracted correctly.

1. Extract floor plans from a property with availability info:
   ```
   You: extract floor plans from https://property-with-availability.com
   ```

2. **What to check:**
   - ✅ If website shows "5 units available" → `available_units` should be 5
   - ✅ If website shows "Available" → `is_available` should be true
   - ✅ If website shows "Not available" → `is_available` should be false
   - ✅ If no availability info → both should be null

## Test 7: Test with Missing Information

**Goal:** Verify the tool handles missing data gracefully.

1. Extract floor plans from a property website that might not have all information:
   ```
   You: extract floor plans from https://minimal-property-site.com
   ```

2. **What to check:**
   - ✅ Tool should still extract what's available
   - ✅ Missing fields should be null (not cause errors)
   - ✅ At minimum, floor plan name should be extracted
   - ✅ Console should show what was found and what wasn't

## Test 8: Verify Tool Registration

**Goal:** Confirm the tool is available to the AI agent.

1. Ask about capabilities:
   ```
   You: What tools do you have available?
   ```

2. **What to check:**
   - ✅ Should mention `extract_floor_plans` tool
   - ✅ Should explain what it does
   - ✅ Should mention it extracts name, size, bedrooms, bathrooms, prices, availability

## Test 9: Test Error Handling

**Goal:** Verify the tool handles errors gracefully.

### Test 9a: Missing Property in Database

1. Extract floor plans from a URL that hasn't been crawled yet:
   ```
   You: extract floor plans from https://new-property.com
   ```

2. **What to check:**
   - ✅ Should crawl the website first
   - ✅ Should extract floor plans
   - ✅ Should show message: "No property found for URL - floor plans not saved to database"
   - ✅ Should still return extracted data

### Test 9b: Invalid URL

1. Try with invalid URL:
   ```
   You: extract floor plans from https://invalid-url-that-does-not-exist.com
   ```

2. **What to check:**
   - ✅ Should handle error gracefully
   - ✅ Should return error message, not crash
   - ✅ Should explain what went wrong

### Test 9c: Missing Database Table

1. If migration hasn't been run, try extracting:
   ```
   You: extract floor plans from https://www.villasattowngate.com
   ```

2. **What to check:**
   - ✅ Should extract floor plans successfully
   - ✅ Should show warning: "Database table 'property_floor_plans' not found"
   - ✅ Should provide instructions to run migration
   - ✅ Should still return extracted data (extraction works, just can't save)

## Quick Test Checklist

Run through this checklist to verify everything works:

- [ ] Tool extracts floor plans from a property website
- [ ] Floor plans are displayed in console with all details
- [ ] Price strings are parsed into min_price and max_price
- [ ] Cache integration works (uses cached markdown when available)
- [ ] Floor plans are saved to database as separate records
- [ ] Each floor plan has correct property_id
- [ ] All fields are populated correctly (or null if not found)
- [ ] Tool handles various price formats correctly
- [ ] Availability information is extracted correctly
- [ ] Tool handles missing information gracefully
- [ ] Error handling works (invalid URLs, missing property, etc.)
- [ ] Tool is registered and available to AI agent

## Common Issues and Solutions

### Issue: "Database table 'property_floor_plans' not found"
**Solution:** Run the migration:
```bash
# If using local Supabase, migrations run automatically
# To verify, check Supabase Studio and look for the table
# If table doesn't exist, you may need to reset migrations:
npx supabase db reset
```

### Issue: "No property found for URL"
**Solution:** 
- First extract property information to create the property record:
  ```
  You: extract property information from https://example.com
  ```
- Then extract floor plans - it will link to the existing property

### Issue: "No floor plans found"
**Solution:**
- Check that the website actually has floor plan information
- Try a different property website
- Some websites may not have floor plans listed publicly

### Issue: Prices not parsing correctly
**Solution:**
- Check the `price_string` field in the database - it should have the original text
- The parsing logic handles common formats, but unusual formats may not parse
- The original `price_string` is always preserved for display

### Issue: Tool not found
**Solution:**
- Make sure you've restarted FionaFast after the changes
- Verify `backend/tools/__init__.py` includes the new tool
- Check for any import errors in the console

## Success Criteria

The implementation is successful if:

1. ✅ Tool extracts floor plans from property websites
2. ✅ Floor plans are displayed with all available information
3. ✅ Prices are parsed correctly (both string and numeric values stored)
4. ✅ Floor plans are saved to database as separate records
5. ✅ Cache integration works (reuses cached markdown)
6. ✅ Tool handles missing information gracefully
7. ✅ Error handling works correctly
8. ✅ Tool is available to the AI agent

## Example Test Property URLs

Here are some example property websites you can use for testing:

- `https://www.villasattowngate.com` (if available)
- Any apartment complex website with a "Floor Plans" or "Apartments" section
- Property management websites typically have floor plan information

**Note:** Make sure you have permission to crawl/test these websites and that they have floor plan information available.


