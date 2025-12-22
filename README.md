# FionaFast - Property Information Extraction Agent

FionaFast is a specialized AI agent designed to extract comprehensive information from property websites for apartment buildings and residential complexes.

## Project Structure

This project is organized as a monorepo with:

- **Backend** (`backend/`): Python-based agent
  - `fiona_fast.py` - Main agent script
  - `tools/` - Tool modules for crawling and extraction
  - `cache/` - Cached website data
  - `requirements.txt` - Python dependencies
  
- **Frontend** (`frontend/`): Next.js application
  - React-based web interface (currently boilerplate)

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

## Running FionaFast

Navigate to the backend directory and run:
```bash
cd backend
python3 fiona_fast.py
```

Or run from the project root:
```bash
python3 backend/fiona_fast.py
```

You can also make it executable and run directly:
```bash
cd backend
chmod +x fiona_fast.py
./fiona_fast.py
```

**Note:** This is a Python script, not a Node.js project. Use `python3` (not `npm`) to run it.

## Usage

Once running, you can:
- Ask FionaFast about its capabilities
- Discuss how it would approach extracting information from property websites
- Have conversations about property data extraction

Type `quit`, `exit`, or `q` to end the conversation.

## Current Status

FionaFast now has active tool calling capabilities with three main tools:

1. **crawl_property_website**: Crawls/scrapes property websites using Apify's Website Content Crawler Actor to extract markdown content from multiple pages. Returns raw markdown content that can be used for information extraction.

2. **extract_website_images**: Extracts images from property websites using Apify's website-image-scraper Actor. Returns a list of image URLs found across the website, including images from CSS backgrounds.

3. **extract_property_information**: Extracts structured property information including:
   - Property name
   - Address (street, city, state, ZIP code)
   - Phone number
   - Email address
   - Office hours

Both crawling and image extraction tools use caching systems for faster subsequent requests. The tools can be used independently or together as needed.

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

