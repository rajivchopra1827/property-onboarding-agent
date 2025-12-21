"""
Tool for crawling/scraping property websites and caching the content.

Primary function: Crawls/scrapes property websites to gather content from multiple pages.
Returns raw markdown content that can be used by other tools for extraction.
"""

import os
from firecrawl import Firecrawl
from .cache_manager import (
    get_domain_from_url,
    is_cache_valid,
    get_cache_age,
    get_cached_markdown,
    save_cache,
    clear_cache
)


def get_firecrawl_client():
    """Initialize and return Firecrawl client with API key from environment."""
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError(
            "FIRECRAWL_API_KEY not found. Please set it in your environment variables."
        )
    return Firecrawl(api_key=api_key)




def get_tool_definition():
    """Returns the tool definition for OpenAI function calling."""
    return {
        "type": "function",
        "function": {
            "name": "crawl_property_website",
            "description": "Crawl/scrape a property website to gather content from multiple pages. Checks cache first - if cached data exists, will use it unless force_refresh is True. Returns raw markdown content from all crawled pages. This tool is used by other tools to get website content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the property website to crawl/scrape"
                    },
                    "use_cache": {
                        "type": "boolean",
                        "description": "Whether to use cached data if available. If None/not provided, the agent will prompt the user. If True, uses cache. If False, forces fresh crawl."
                    },
                    "force_refresh": {
                        "type": "boolean",
                        "description": "Force a fresh crawl even if cache exists. Defaults to False.",
                        "default": False
                    }
                },
                "required": ["url"]
            }
        }
    }


def execute(arguments):
    """
    Execute the crawl_property_website tool.
    
    Crawls/scrapes the website to gather content from multiple pages.
    Returns raw markdown content that can be used by other tools.
    
    Process:
    1. Checks cache first (if use_cache is True or None)
    2. If no cache or force_refresh, Firecrawl crawls the website and returns clean markdown
    3. Saves crawled data to cache
    4. Returns markdown content
    
    Args:
        arguments: Dictionary containing tool arguments
            - url (str): The URL of the property website
            - use_cache (bool, optional): Whether to use cached data. None = prompt user, True = use cache, False = fresh crawl
            - force_refresh (bool, optional): Force fresh crawl even if cache exists. Defaults to False.
        
    Returns:
        Dictionary with markdown content and cache_info
    """
    url = arguments.get("url", "")
    use_cache = arguments.get("use_cache")  # None, True, or False
    force_refresh = arguments.get("force_refresh", False)
    
    if not url:
        return {
            "error": "URL is required",
            "markdown": None
        }
    
    print(f"Crawling/scraping property website: {url}")
    
    # Get domain for cache lookup
    domain = get_domain_from_url(url)
    cache_valid = is_cache_valid(domain)
    cache_age = get_cache_age(domain) if cache_valid else None
    
    # Determine if we should use cache
    should_use_cache = False
    if force_refresh:
        should_use_cache = False
        print("Force refresh requested - ignoring cache")
    elif use_cache is True:
        if cache_valid:
            should_use_cache = True
            print(f"Using cached data (age: {cache_age:.1f} hours)")
        else:
            print("Cache requested but not valid - will crawl fresh")
    elif use_cache is False:
        should_use_cache = False
        print("Fresh crawl requested - ignoring cache")
    elif cache_valid:
        # use_cache is None - return cache info for agent to prompt user
        return {
            "cache_available": True,
            "cache_age_hours": cache_age,
            "domain": domain,
            "message": f"Cached data available from {cache_age:.1f} hours ago. Set use_cache=True to use cache, or force_refresh=True to crawl fresh.",
            "markdown": None
        }
    
    try:
        markdown_content = None
        
        # Try to use cache if requested
        if should_use_cache and cache_valid:
            markdown_content = get_cached_markdown(domain)
            if markdown_content:
                print(f"✓ USING CACHE: Loaded {len(markdown_content)} characters from cache (age: {cache_age:.1f} hours)")
            else:
                print("⚠ Cache exists but markdown is empty - will crawl fresh")
                should_use_cache = False
        
        # Crawl if not using cache
        if not should_use_cache or not markdown_content:
            print("🔄 CRAWLING FRESH: Crawling website with Firecrawl to find all pages...")
            firecrawl = get_firecrawl_client()
        
            # Crawl the website to get content from multiple pages (homepage, contact, about, etc.)
            crawl_response = firecrawl.crawl(
                url=url,
                limit=50,  # Maximum number of pages to crawl
                scrape_options={
                    "formats": ["markdown"],
                    "onlyMainContent": True  # Focus on main content, ignore navigation/footer
                },
                crawl_entire_domain=True,  # Crawl entire domain, not just children of the URL
                timeout=180000  # 3 minute timeout for crawling
            )
            
            # Check if crawl was successful
            if not crawl_response or not hasattr(crawl_response, 'data'):
                raise ValueError("Firecrawl crawl returned no data")
            
            # Extract markdown from all crawled pages
            # crawl_response.data is a list of Document objects
            all_markdown_parts = []
            pages_data = []  # For caching
            
            for doc in crawl_response.data:
                if hasattr(doc, 'markdown') and doc.markdown:
                    markdown_text = doc.markdown
                    all_markdown_parts.append(markdown_text)
                    # Get URL from metadata if available
                    doc_url = url
                    if hasattr(doc, 'metadata') and doc.metadata:
                        if hasattr(doc.metadata, 'sourceURL'):
                            doc_url = doc.metadata.sourceURL
                        elif isinstance(doc.metadata, dict) and 'sourceURL' in doc.metadata:
                            doc_url = doc.metadata['sourceURL']
                    pages_data.append({
                        "url": doc_url,
                        "markdown": markdown_text
                    })
            
            if not all_markdown_parts:
                raise ValueError("No markdown content found in crawled pages")
            
            # Combine all markdown from all pages
            # Add page separators to help understand context
            markdown_content = "\n\n---PAGE BREAK---\n\n".join(all_markdown_parts)
            
            pages_crawled = len(all_markdown_parts)
            print(f"✓ Successfully crawled {pages_crawled} pages, {len(markdown_content)} total characters of markdown content")
            
            # Save to cache
            if pages_data:
                save_cache(domain, pages_data)
                print(f"✓ Cached data for {domain}")
        
        # Return markdown content
        result = {
            "markdown": markdown_content
        }
        
        # Add cache info and show status
        if should_use_cache and cache_valid:
            result["cache_info"] = {
                "used_cache": True,
                "cache_age_hours": cache_age
            }
            print(f"\n[Cache Status] ✓ Used cached data (age: {cache_age:.1f} hours)")
        else:
            result["cache_info"] = {
                "used_cache": False,
                "cached": True  # Data was just cached
            }
            print(f"\n[Cache Status] ✓ Crawled fresh data and saved to cache")
        
        print(f"[Tool Execution Complete]")
        return result
    
    except ValueError as e:
        # API key missing or other value errors
        print(f"Error: {e}")
        return {
            "error": str(e),
            "markdown": None
        }
    
    except Exception as e:
        # Other errors (network, API, etc.)
        print(f"Error crawling/scraping property website: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to crawl/scrape property website: {str(e)}",
            "markdown": None
        }

