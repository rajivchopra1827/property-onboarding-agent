# Migration Guide: Old System to Agno Workflows

This guide documents the migration from the old sequential orchestration system to the new Agno workflow-based system.

## What Changed

### Architecture Changes

**Old System:**
- Sequential tool execution via `onboard_property.py`
- Conversational CLI agent (`fiona_fast.py`)
- Python scripts called via subprocess from frontend
- Manual orchestration with progress callbacks

**New System:**
- Agno workflows with parallel execution
- FastAPI server for API access
- Workflow-based orchestration with built-in progress tracking
- Upfront cache decisions

### Removed Components

1. **`backend/fiona_fast.py`** - Conversational CLI agent (deprecated)
2. **`backend/scripts/onboard_property_api.py`** - Old API script (replaced by FastAPI)
3. **`backend/scripts/force_reonboard.py`** - Helper script (use API endpoint instead)
4. **`backend/scripts/resume_stone_canyon.py`** - Helper script (use API endpoint instead)
5. **`backend/scripts/check_missing_extractions.py`** - Helper script (use API endpoint instead)

### Deprecated Components

- **`backend/tools/onboard_property.py`** - Old orchestrator (marked deprecated, kept for transition)

### New Components

1. **`backend/workflows/onboard_property_workflow.py`** - Agno workflow for onboarding
2. **`backend/workflows/utils.py`** - Utility functions (get_missing_extractions, DEFAULT_EXTRACTIONS)
3. **`backend/agno_tools/`** - Agno-native tool wrappers
4. **`backend/api/server.py`** - FastAPI server

## Migration Steps

### For Frontend Developers

**Old way:**
```typescript
// Called Python script via subprocess
exec(`python3 onboard_property_api.py ${sessionId} ${url}`);
```

**New way:**
```typescript
// Call FastAPI endpoint
const response = await fetch('http://localhost:8000/api/onboard', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url, force_reonboard })
});
```

### For Backend Developers

**Old way:**
```python
from tools.onboard_property import execute as onboard_property

result = onboard_property({
    "url": url,
    "use_cache": use_cache,
    "force_refresh": force_refresh
})
```

**New way:**
```python
from workflows.onboard_property_workflow import create_onboard_property_workflow

workflow = create_onboard_property_workflow(
    url=url,
    session_id=session_id,
    use_cache=use_cache,
    force_refresh=force_refresh
)
result = workflow.run()
```

### For Script Writers

**Old helper scripts are replaced by API endpoints:**

1. **Check missing extractions:**
   ```bash
   # Old: python3 scripts/check_missing_extractions.py <url>
   # New:
   curl http://localhost:8000/api/properties/{property_id}/missing-extractions
   ```

2. **Force re-onboarding:**
   ```bash
   # Old: python3 scripts/force_reonboard.py <url>
   # New:
   curl -X POST http://localhost:8000/api/properties/{property_id}/force-reonboard
   ```

## API Endpoints

### POST /api/onboard
Start onboarding workflow for a property.

**Request:**
```json
{
  "url": "https://example.com",
  "force_reonboard": false
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "uuid",
  "property_id": null,
  "status": "started",
  "message": "Onboarding started"
}
```

### GET /api/onboard/{session_id}/status
Get workflow execution status.

**Response:**
```json
{
  "session_id": "uuid",
  "status": "in_progress",
  "current_step": "amenities",
  "completed_steps": ["property_info", "images"],
  "errors": [],
  "property_id": "uuid"
}
```

### GET /api/properties/{property_id}/missing-extractions
Get list of missing extraction types.

**Response:**
```json
{
  "property_id": "uuid",
  "missing_extractions": ["reviews", "competitors"],
  "all_complete": false
}
```

### POST /api/properties/{property_id}/force-reonboard
Force re-onboarding for existing property.

**Response:**
```json
{
  "success": true,
  "session_id": "uuid",
  "property_id": "uuid",
  "status": "started",
  "message": "Force re-onboarding started"
}
```

## Key Differences

### Execution Model

**Old:** Sequential execution (one step at a time)
- Step 1 → Step 2 → Step 3 → ... → Step 8
- Total time: Sum of all step times

**New:** Parallel execution (independent steps run simultaneously)
- Step 1 (property_info)
- Step 2 (parallel: images, brand_identity, amenities, floor_plans, special_offers)
- Step 3 (reviews, competitors)
- Total time: ~60% faster due to parallelization

### Cache Strategy

**Old:** Per-tool cache decisions with user prompts
- Each tool checked cache independently
- User prompted for cache decisions in CLI

**New:** Upfront cache decision at workflow start
- Workflow checks cache once at start
- Decision passed to all steps
- No user prompts (API-based)

### Progress Tracking

**Old:** Manual progress callbacks
- Callback function passed to tool
- Manual session updates

**New:** Built-in workflow progress tracking
- Workflow steps automatically update session
- Progress tracked via OnboardingRepository

## Benefits

1. **Performance:** ~60% faster due to parallel execution
2. **Maintainability:** Clear workflow structure, easier to modify
3. **Scalability:** Agno workflows support retries, error handling, monitoring
4. **Code Quality:** Separation of concerns, workflow vs tool logic
5. **API-First:** Better integration with frontend and external systems

## Troubleshooting

### Workflow not starting
- Check FastAPI server is running: `curl http://localhost:8000/health`
- Verify Agno is installed: `pip install agno`
- Check server logs for errors

### Parallel steps not running
- Verify Agno Tool wrappers are importing correctly
- Check workflow logs for errors
- Ensure all dependencies are installed

### Cache not working
- Verify cache decision logic in workflow
- Check `cache_entries` table in Supabase
- Review cache age and expiration settings

## Need Help?

- Check `backend/api/README.md` for API server documentation
- Review `backend/workflows/onboard_property_workflow.py` for workflow structure
- See `TESTING_GUIDE.md` for testing instructions
