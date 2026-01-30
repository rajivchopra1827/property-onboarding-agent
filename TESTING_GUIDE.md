# Testing Guide for Property Onboarding System

This guide will help you verify that the Agno workflow-based onboarding system is working correctly.

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

## Test 1: Start the FastAPI Server

**Goal:** Verify the API server starts correctly.

1. Start the FastAPI server:
   ```bash
   cd backend
   python -m api.server
   ```
   Or:
   ```bash
   uvicorn api.server:app --reload
   ```

2. **What to check:**
   - ✅ Server should start without errors
   - ✅ Should see "Uvicorn running on http://0.0.0.0:8000"
   - ✅ Health check should work: `curl http://localhost:8000/health`

## Test 2: Onboard a Property via API

**Goal:** Verify the onboarding workflow executes successfully.

1. Start onboarding:
   ```bash
   curl -X POST http://localhost:8000/api/onboard \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.villasattowngate.com", "force_reonboard": false}'
   ```

2. **What to check:**
   - ✅ Should return `session_id` immediately
   - ✅ Status should be "started"
   - ✅ Response should include `success: true`

3. Check status:
   ```bash
   curl http://localhost:8000/api/onboard/{session_id}/status
   ```

4. **What to check:**
   - ✅ Status should progress through steps
   - ✅ `completed_steps` should grow as workflow progresses
   - ✅ Should eventually reach "completed" status
   - ✅ `property_id` should be populated after step 1

## Test 3: Verify Parallel Execution

**Goal:** Confirm that parallel extractions run simultaneously.

1. Start onboarding and monitor status:
   ```bash
   # Start onboarding
   SESSION_ID=$(curl -s -X POST http://localhost:8000/api/onboard \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.villasattowngate.com"}' | jq -r '.session_id')
   
   # Monitor status
   watch -n 2 "curl -s http://localhost:8000/api/onboard/$SESSION_ID/status | jq"
   ```

2. **What to check:**
   - ✅ After `property_info` completes, multiple steps should appear in `completed_steps` quickly
   - ✅ Steps 2-6 (parallel group) should complete around the same time
   - ✅ Total time should be faster than sequential execution

## Test 4: Verify Cache Strategy

**Goal:** Confirm upfront cache decision works correctly.

1. First onboarding (fresh):
   ```bash
   curl -X POST http://localhost:8000/api/onboard \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.villasattowngate.com", "force_reonboard": false}'
   ```
   - Should crawl fresh (no cache exists)

2. Second onboarding (should use cache if < 12 hours old):
   ```bash
   curl -X POST http://localhost:8000/api/onboard \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.villasattowngate.com", "force_reonboard": false}'
   ```
   - Should use cached markdown (faster)

3. Force refresh:
   ```bash
   curl -X POST http://localhost:8000/api/onboard \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.villasattowngate.com", "force_reonboard": true}'
   ```
   - Should ignore cache and crawl fresh

## Test 5: Check Missing Extractions

**Goal:** Verify the missing extractions endpoint works.

1. Get missing extractions for a property:
   ```bash
   curl http://localhost:8000/api/properties/{property_id}/missing-extractions
   ```

2. **What to check:**
   - ✅ Should return list of missing extraction types
   - ✅ `all_complete` should be `false` if extractions are missing
   - ✅ Should return empty list if all extractions complete

## Test 6: Force Re-onboarding

**Goal:** Verify force re-onboarding endpoint works.

1. Force re-onboard an existing property:
   ```bash
   curl -X POST http://localhost:8000/api/properties/{property_id}/force-reonboard
   ```

2. **What to check:**
   - ✅ Should create new session
   - ✅ Should run all extractions even if data exists
   - ✅ Should use `force_refresh=True` (ignore cache)

## Quick Test Checklist

Run through this checklist to verify everything works:

- [ ] FastAPI server starts without errors
- [ ] Health check endpoint returns "healthy"
- [ ] Onboarding workflow starts successfully
- [ ] Session status updates correctly
- [ ] Parallel extractions complete faster than sequential
- [ ] Cache strategy works (uses cache when appropriate)
- [ ] Missing extractions endpoint returns correct data
- [ ] Force re-onboarding works
- [ ] Error handling works (invalid URLs, missing properties)
- [ ] No console errors or warnings

## Common Issues and Solutions

### Issue: "APIFY_API_TOKEN not found"
**Solution:** Make sure you've set the Apify API token in your environment or `.env.local` file. The same token is used for both website crawling and image extraction.

### Issue: FastAPI server won't start
**Solution:**
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify Agno is installed: `pip install agno`
- Check for import errors in the console

### Issue: Workflow not progressing
**Solution:**
- Check session status endpoint to see current step
- Verify database connection (Supabase)
- Check for errors in session.errors array
- Review FastAPI server logs

### Issue: Parallel steps not running
**Solution:**
- Verify Agno is installed correctly
- Check workflow logs for errors
- Ensure all Agno Tool wrappers are importing correctly

## Success Criteria

The implementation is successful if:

1. ✅ FastAPI server starts and responds to requests
2. ✅ Onboarding workflow executes successfully
3. ✅ Parallel extractions complete faster than sequential
4. ✅ Cache strategy works correctly (uses cache when appropriate)
5. ✅ Session status updates in real-time
6. ✅ Missing extractions endpoint returns correct data
7. ✅ Force re-onboarding works correctly
8. ✅ Error handling works gracefully
9. ✅ All 8 extraction types complete successfully

