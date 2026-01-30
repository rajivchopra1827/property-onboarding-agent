# Property Onboarding API Server

FastAPI server that runs Agno workflows for property onboarding.

## Running the Server

```bash
cd backend
python -m api.server
```

Or using uvicorn directly:

```bash
cd backend
uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
```

## Environment Variables

The server uses the same environment variables as the rest of the backend:
- `OPENAI_API_KEY` - Required for LLM extractions
- `APIFY_API_TOKEN` - Required for web crawling and image extraction
- `SUPABASE_URL` - Supabase database URL
- `SUPABASE_KEY` - Supabase API key

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
Get the status of an onboarding session.

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

### GET /health
Health check endpoint.

## Frontend Integration

The frontend should set `BACKEND_API_URL` environment variable to point to this server (defaults to `http://localhost:8000`).
