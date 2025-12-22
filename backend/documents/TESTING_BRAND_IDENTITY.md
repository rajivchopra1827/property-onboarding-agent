# Testing Guide for Brand Identity Extraction Tool

This guide will help you verify that the `extract_brand_identity` tool is working correctly.

## Prerequisites

Before testing, make sure you have:

1. **All dependencies installed:**
   ```bash
   cd backend
   pip3 install -r requirements.txt
   ```
   This should install `firecrawl-py` package.

2. **Firecrawl API key set:**
   ```bash
   export FIRECRAWL_API_KEY='your-firecrawl-api-key'
   ```
   
   Or in your `.env.local` or `.env` file:
   ```
   FIRECRAWL_API_KEY=your-firecrawl-api-key
   ```

3. **Database migration run:**
   ```bash
   # If using Supabase locally
   supabase migration up
   
   # Or apply the migration manually to your Supabase project
   ```

## Test 1: Basic Brand Identity Extraction

**Goal:** Verify the tool can extract branding data from a property website.

1. Start FionaFast:
   ```bash
   cd backend
   python3 fiona_fast.py
   ```

2. Test brand identity extraction:
   ```
   You: extract brand identity from https://www.villasattowngate.com
   ```
   Or:
   ```
   You: get brand colors and fonts from https://www.villasattowngate.com
   ```

3. **What to check:**
   - ✅ Tool should call Firecrawl API successfully
   - ✅ Console should show "🔄 EXTRACTING FRESH: Using Firecrawl to extract brand identity..."
   - ✅ Console should show "Calling Firecrawl API with branding format..."
   - ✅ Console should show "✓ Successfully extracted branding data"
   - ✅ Should return branding data with structure like:
     - `colorScheme` (light/dark)
     - `logo` (URL)
     - `colors` (primary, secondary, accent, background, textPrimary, etc.)
     - `fonts` (array of font families)
     - `typography` (fontFamilies, fontSizes, fontWeights)
     - `spacing` (baseUnit, borderRadius)
     - `components` (buttonPrimary, buttonSecondary, etc.)

4. **Expected output structure:**
   ```json
   {
     "branding_data": {
       "colorScheme": "light",
       "logo": "https://example.com/logo.svg",
       "colors": {
         "primary": "#FF6B35",
         "secondary": "#004E89",
         "background": "#FFFFFF",
         "textPrimary": "#000000"
       },
       "fonts": [{"family": "Inter"}],
       "typography": {...},
       "spacing": {...},
       "components": {...}
     },
     "cache_info": {
       "used_cache": false,
       "cached": true
     }
   }
   ```

## Test 2: Verify Caching Works

**Goal:** Confirm that branding data is cached and can be reused.

### Test 2a: First extraction (fresh)

1. Extract branding for the first time:
   ```
   You: extract brand identity from https://www.villasattowngate.com
   ```
   - Should extract fresh and cache branding
   - Console should show "✓ Cached branding data for {domain}"
   - Console should show "[Cache Status] ✓ Extracted fresh branding and saved to cache"

### Test 2b: Second extraction (should use cache)

1. Extract branding again (same URL):
   ```
   You: extract brand identity from https://www.villasattowngate.com
   ```
   - Should prompt about cache or use cache if `use_cache=True`
   - Console should show "Using cached branding (age: X.X hours)" or "USING CACHE"
   - Console should show "[Cache Status] ✓ Used cached branding (age: X.X hours)"

### Test 2c: Force refresh

1. Force fresh extraction:
   ```
   You: extract brand identity from https://www.villasattowngate.com with force refresh
   ```
   Or manually set `force_refresh=True` in tool call
   - Should ignore cache and extract fresh
   - Console should show "Force refresh requested - ignoring cache"

## Test 3: Verify Database Storage

**Goal:** Confirm branding data is saved to the database.

1. Extract branding for a property that exists in database:
   ```
   You: extract brand identity from https://www.villasattowngate.com
   ```

2. **What to check:**
   - ✅ Console should show "✓ Saved branding data to database for property"
   - ✅ If property doesn't exist, should show "ℹ No property found for URL - branding not saved to database (will be cached)"

3. **Verify in database:**
   ```sql
   -- Check if branding was saved
   SELECT * FROM property_branding 
   WHERE website_url LIKE '%villasattowngate%';
   
   -- Or check by property_id if you know it
   SELECT pb.*, p.property_name 
   FROM property_branding pb
   JOIN properties p ON pb.property_id = p.id
   WHERE p.website_url LIKE '%villasattowngate%';
   ```

4. **What to check in database:**
   - ✅ `property_id` should match an existing property
   - ✅ `branding_data` should contain the full Firecrawl response (JSONB)
   - ✅ `website_url` should be set
   - ✅ `created_at` and `updated_at` should be set

## Test 4: Verify Cache Independence

**Goal:** Confirm branding cache is separate from markdown and images cache.

1. Extract markdown:
   ```
   You: crawl https://www.villasattowngate.com
   ```

2. Extract images:
   ```
   You: extract images from https://www.villasattowngate.com
   ```

3. Extract branding:
   ```
   You: extract brand identity from https://www.villasattowngate.com
   ```

4. **What to check:**
   - ✅ All three caches should work independently
   - ✅ Each should have its own cache entry in `cache_entries` table with different `content_type`:
     - `content_type = 'markdown'` for crawl
     - `content_type = 'images'` for images
     - `content_type = 'branding'` for branding

5. **Verify in database:**
   ```sql
   SELECT domain, content_type, created_at 
   FROM cache_entries 
   WHERE domain = 'villasattowngate.com';
   ```
   Should show 3 separate entries with different content_types.

## Test 5: Verify Error Handling

### Test 5a: Missing Firecrawl API key

1. Temporarily unset Firecrawl API key:
   ```bash
   unset FIRECRAWL_API_KEY
   ```

2. Try to extract branding:
   ```
   You: extract brand identity from https://www.villasattowngate.com
   ```

3. **What to check:**
   - ✅ Should show clear error message: "FIRECRAWL_API_KEY not found"
   - ✅ Should NOT crash the application
   - ✅ Should return error in result, not raise exception

### Test 5b: Invalid URL

1. Try with invalid URL:
   ```
   You: extract brand identity from https://invalid-url-that-does-not-exist.com
   ```

2. **What to check:**
   - ✅ Should handle error gracefully
   - ✅ Should return error message, not crash
   - ✅ Should show error details in console

### Test 5c: Website with no branding data

1. Try with a website that might not return branding:
   ```
   You: extract brand identity from https://example.com
   ```

2. **What to check:**
   - ✅ Should handle gracefully if Firecrawl returns empty branding
   - ✅ Should show warning: "⚠ Warning: Firecrawl returned no branding data"
   - ✅ Should still cache empty result (or handle appropriately)

## Test 6: Verify Tool Integration

**Goal:** Confirm the tool works well with other tools.

1. Extract property information first:
   ```
   You: extract property information from https://www.villasattowngate.com
   ```
   This creates/updates the property in database.

2. Extract branding:
   ```
   You: extract brand identity from https://www.villasattowngate.com
   ```

3. **What to check:**
   - ✅ Branding should be linked to the property via `property_id`
   - ✅ Console should show "✓ Saved branding data to database for property"
   - ✅ Both tools should work without conflicts

## Test 7: Verify Tool Definition

**Goal:** Confirm the AI agent knows about the new tool.

1. Ask about capabilities:
   ```
   You: What tools do you have available?
   ```
   Or:
   ```
   You: Can you extract brand identity?
   ```

2. **What to check:**
   - ✅ Should mention `extract_brand_identity` tool
   - ✅ Should explain when to use it (brand colors, fonts, design system, etc.)
   - ✅ Should mention it uses Firecrawl
   - ✅ Should mention caching capability

## Test 8: Verify Frontend Types (Optional)

**Goal:** Confirm TypeScript types are correct for frontend integration.

1. Check TypeScript file:
   ```bash
   cat frontend/lib/types.ts
   ```

2. **What to check:**
   - ✅ Should have `PropertyBranding` interface
   - ✅ Should match the database schema:
     - `id: string`
     - `property_id: string | null`
     - `branding_data: Record<string, any>`
     - `website_url: string | null`
     - `created_at: string | null`
     - `updated_at: string | null`

3. **Test frontend query (if frontend is set up):**
   ```typescript
   const { data: brandingData } = await supabase
     .from('property_branding')
     .select('*')
     .eq('property_id', propertyId)
     .single();
   ```
   Should work without TypeScript errors.

## Quick Test Checklist

Run through this checklist to verify everything works:

- [ ] `extract_brand_identity` successfully calls Firecrawl API
- [ ] Returns branding data with expected structure (colors, fonts, typography, etc.)
- [ ] Branding caching works independently
- [ ] Database storage works (saves to `property_branding` table)
- [ ] Cache is separate from markdown and images cache
- [ ] Error handling works (missing API key, invalid URL)
- [ ] Tool integrates with other tools (property extraction)
- [ ] System prompt mentions the tool correctly
- [ ] TypeScript types are correct
- [ ] No console errors or warnings

## Common Issues and Solutions

### Issue: "FIRECRAWL_API_KEY not found"
**Solution:** Make sure you've set the Firecrawl API key in your environment or `.env` file.

### Issue: "ModuleNotFoundError: No module named 'firecrawl'"
**Solution:** 
- Make sure you've installed dependencies: `pip3 install -r backend/requirements.txt`
- Verify `firecrawl-py` is in `requirements.txt`

### Issue: "No branding data returned"
**Solution:**
- Check that Firecrawl API is working (try their API directly)
- Some websites might not have extractable branding data
- Check Firecrawl API response in console logs

### Issue: "Database error when saving branding"
**Solution:**
- Make sure database migration has been run
- Verify `property_branding` table exists
- Check that property exists in database first (run `extract_property_information` first)

### Issue: Cache not working
**Solution:**
- Check that `cache_entries` table exists
- Verify cache functions are being called (check console output)
- Check cache age (caches expire after 24 hours by default)

### Issue: Tool not found
**Solution:**
- Make sure you've restarted FionaFast after the changes
- Verify `backend/tools/__init__.py` includes `extract_brand_identity`
- Check for any import errors in the console

## Success Criteria

The implementation is successful if:

1. ✅ `extract_brand_identity` successfully extracts branding data using Firecrawl
2. ✅ Branding data includes colors, fonts, typography, spacing, components
3. ✅ Branding caching works independently from other caches
4. ✅ Branding data is saved to database when property exists
5. ✅ Error handling works gracefully
6. ✅ Tool integrates well with other tools
7. ✅ System prompt correctly describes the tool
8. ✅ TypeScript types are correct for frontend integration

## Example Test URLs

Here are some property websites you can use for testing:

- `https://www.villasattowngate.com` (if you've been using this)
- `https://www.firecrawl.dev` (Firecrawl's own site - should have good branding)
- Any property management company website

## Next Steps After Testing

Once testing is complete:

1. **Frontend Integration:** Update the property detail page to display branding data
2. **UI Components:** Create components to visualize:
   - Color palette
   - Typography samples
   - Logo display
   - Component styles
3. **Brand Guidelines Export:** Consider adding functionality to export branding as a style guide


