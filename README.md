# FionaFast - Property Information Extraction Agent

FionaFast is a specialized AI agent designed to extract comprehensive information from property websites for apartment buildings and residential complexes.

## Project Structure

This project is organized as a monorepo with:

- **Backend** (`backend/`): Python-based property onboarding system
  - `workflows/` - Agno workflows for orchestrating extractions
  - `agno_tools/` - Agno-native tool wrappers
  - `api/` - FastAPI server for workflow execution
  - `tools/` - Individual extraction tool modules
  - `database/` - Database repositories and models
  - `requirements.txt` - Python dependencies
  
- **Frontend** (`frontend/`): Next.js application
  - React-based web interface for property management
  - API routes that call FastAPI backend

## Setup

1. **Install Python dependencies:**
   ```bash
   cd backend
   pip3 install -r requirements.txt
   ```
   (or `pip install -r requirements.txt` if you have pip configured)

2. **Set up Supabase (Local Database):**
   
   FionaFast uses Supabase for database storage. You can run Supabase locally using Docker Desktop.
   
   **Prerequisites:**
   - Docker Desktop must be installed and running (the app with the whale icon)
   
   **Setup steps:**
   
   a. Start Supabase locally:
   ```bash
   npx supabase start
   ```
   
   This will start a local Supabase instance with PostgreSQL database. After running this command, you'll see connection details including:
   - API URL (typically `http://127.0.0.1:54321`)
   - Anon key (for client-side access)
   - Service role key (for server-side access)
   
   b. Add Supabase connection details to your `.env.local` file:
   ```bash
   SUPABASE_URL=http://127.0.0.1:54321
   SUPABASE_KEY=your-anon-key-from-supabase-start-output
   ```
   
   The database migrations will automatically run when you start Supabase, creating the necessary tables:
   - `properties` - Stores extracted property information
   - `property_images` - Stores property images
   - `cache_entries` - Stores cached website data (replaces file-based cache)
   - `extraction_sessions` - Tracks extraction runs
   
   **Note:** If you don't have Docker Desktop running, you'll see an error. Make sure Docker Desktop is started before running `supabase start`.
   
   **Accessing Supabase Studio:**
   - Local Supabase Studio (database UI) is available at: `http://127.0.0.1:54323`
   - You can view and manage your database tables, run queries, and more from this interface

3. **Set your API keys:**
   
   You'll need OpenAI and Apify API keys:
   
   ```bash
   export OPENAI_API_KEY='your-openai-api-key-here'
   export APIFY_API_TOKEN='your-apify-api-token-here'
   ```
   
   Or create a `.env.local` or `.env` file (if you prefer using python-dotenv):
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   APIFY_API_TOKEN=your-apify-api-token-here
   SUPABASE_URL=http://127.0.0.1:54321
   SUPABASE_KEY=your-anon-key-from-supabase-start-output
   ```
   
   **Getting your API keys:**
   - **Apify**: Sign up at [apify.com](https://apify.com), get your API token from Settings → Integrations → API tokens. The same token is used for both website crawling and image extraction.

## Running the System

### Start the FastAPI Server

The backend uses a FastAPI server to run Agno workflows:

```bash
cd backend
python -m api.server
```

Or using uvicorn directly:

```bash
cd backend
uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### Start the Frontend

In a separate terminal:

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage

### Onboarding a Property

**Via Frontend:**
1. Navigate to the properties page
2. Click "Add Property"
3. Enter the property website URL
4. The system will automatically start onboarding via the workflow

**Via API:**
```bash
curl -X POST http://localhost:8000/api/onboard \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "force_reonboard": false}'
```

**Check Status:**
```bash
curl http://localhost:8000/api/onboard/{session_id}/status
```

### Check Missing Extractions

```bash
curl http://localhost:8000/api/properties/{property_id}/missing-extractions
```

### Force Re-onboarding

```bash
curl -X POST http://localhost:8000/api/properties/{property_id}/force-reonboard
```

## Architecture

The system uses **Agno workflows** to orchestrate property onboarding with parallel execution:

1. **Workflow-based:** All onboarding goes through Agno workflows for better performance and maintainability
2. **Parallel execution:** Independent extractions run simultaneously (images, amenities, floor plans, etc.)
3. **FastAPI server:** Provides REST API for triggering and monitoring workflows
4. **Individual tools:** Each extraction type is a separate tool that can be used independently

### Extraction Types

The system extracts the following information from property websites:

1. **Property Information** - Name, address, phone, email, office hours
2. **Images** - All images from the website
3. **Brand Identity** - Colors, fonts, typography, design system
4. **Amenities** - Building and apartment amenities
5. **Floor Plans** - Unit types, sizes, prices, availability
6. **Special Offers** - Promotions and concessions
7. **Reviews** - Google Maps reviews and ratings
8. **Competitors** - Nearby competing properties

### Workflow Execution

The onboarding workflow runs in three phases:
1. **Step 1:** Extract property info (creates database record)
2. **Step 2:** Parallel extractions (5 steps run simultaneously)
3. **Step 3:** Sequential extractions (reviews and competitors, need property address)

## Database

FionaFast uses Supabase (PostgreSQL) for data storage. All extracted property information, images, and cache entries are stored in the database instead of files.

**Database Tables:**
- **properties**: Stores extracted property information (name, address, phone, email, office hours, etc.)
- **property_images**: Stores image URLs and metadata linked to properties
- **cache_entries**: Stores cached website data (markdown content and images) with expiration support
- **extraction_sessions**: Tracks extraction runs for auditing and history

**Database Features:**
- Automatic saving: When you extract property information or images, they're automatically saved to the database
- Cache replacement: The file-based cache system has been replaced with database cache for better performance and scalability
- Data persistence: All extracted data persists across sessions and can be queried via Supabase Studio or the API

**Viewing Data:**
- Access Supabase Studio at `http://127.0.0.1:54323` to view and query your database
- Use the SQL editor to run custom queries
- Browse tables and view extracted property data

