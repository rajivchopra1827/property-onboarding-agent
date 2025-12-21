# FionaFast - Property Information Extraction Agent

FionaFast is a specialized AI agent designed to extract comprehensive information from property websites for apartment buildings and residential complexes.

## Setup

1. **Install Python dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```
   (or `pip install -r requirements.txt` if you have pip configured)

2. **Set your API keys:**
   
   You'll need both OpenAI and Firecrawl API keys:
   
   ```bash
   export OPENAI_API_KEY='your-openai-api-key-here'
   export FIRECRAWL_API_KEY='your-firecrawl-api-key-here'
   ```
   
   Or create a `.env.local` or `.env` file (if you prefer using python-dotenv):
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   FIRECRAWL_API_KEY=your-firecrawl-api-key-here
   ```
   
   **Getting your Firecrawl API key:**
   - Sign up at [firecrawl.dev](https://firecrawl.dev)
   - Get your API key from the dashboard
   - The API key should start with `fc-`

## Running FionaFast

Simply run:
```bash
python3 fiona_fast.py
```

Or make it executable and run directly:
```bash
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

FionaFast now has active tool calling capabilities! The `crawl_property_website` tool crawls/scrapes property websites (using Firecrawl) and extracts structured data including:
- Property name
- Address (street, city, state, ZIP code)
- Phone number
- Email address
- Office hours

The tool uses Firecrawl's Crawl endpoint to gather content from multiple pages across the website, then uses OpenAI to extract structured information. Crawled data is cached for faster subsequent requests.

