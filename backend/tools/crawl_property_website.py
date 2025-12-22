"""
Tool for crawling/scraping property websites and caching the content.

Primary function: Crawls/scrapes property websites to gather content from multiple pages.
Returns raw markdown content that can be used by other tools for extraction.
"""

import os
import json
from apify_client import ApifyClient
from .cache_manager import (
    get_domain_from_url,
    is_cache_valid,
    get_cache_age,
    get_cached_markdown,
    save_cache,
    clear_cache,
    is_html_cache_valid,
    get_html_cache_age,
    get_cached_html,
    save_html_cache
)


def get_apify_client():
    """Initialize and return Apify client with API token from environment."""
    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token:
        raise ValueError(
            "APIFY_API_TOKEN not found. Please set it in your environment variables."
        )
    return ApifyClient(token=api_token)


def should_include_page(url):
    """
    Filter out non-content pages like sitemaps, robots.txt, etc.
    
    Args:
        url: The URL to check
        
    Returns:
        True if the page should be included, False otherwise
    """
    if not url:
        return False
    
    url_lower = url.lower()
    
    # Filter out sitemap URLs (more specific patterns)
    if 'sitemap' in url_lower:
        return False
    
    # Filter out robots.txt and other common non-content files
    excluded_patterns = [
        '/robots.txt',
        '/favicon.ico',
        'sitemap.xml',
        'sitemap-general.xml',
        'sitemap-index.xml'
    ]
    for pattern in excluded_patterns:
        if pattern in url_lower:
            return False
    
    return True






def get_firecrawl_client():
    """Initialize and return Firecrawl client with API key from environment."""
    from firecrawl import Firecrawl
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
            "description": "Crawl/scrape a property website to gather content from multiple pages. Uses Firecrawl by default (with Apify option). Checks cache first - if cached data exists, will use it unless force_refresh is True. Returns raw markdown content from all crawled pages. This tool is used by other tools to get website content. For images, use the extract_website_images tool separately.",
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
                    },
                    "scraping_method": {
                        "type": "string",
                        "enum": ["firecrawl", "apify"],
                        "description": "Scraping method to use. Defaults to 'firecrawl'. Use 'apify' for Apify Website Content Crawler.",
                        "default": "firecrawl"
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
    2. If no cache or force_refresh, Apify Website Content Crawler crawls the website and returns clean markdown
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
    scraping_method = arguments.get("scraping_method", "firecrawl")  # Default to firecrawl
    
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
            if scraping_method == "firecrawl":
                print("🔄 CRAWLING FRESH: Crawling website with Firecrawl...")
                
                # Check for HTML cache first
                html_pages = None
                html_cache_valid = is_html_cache_valid(domain)
                
                if html_cache_valid and not force_refresh:
                    html_pages = get_cached_html(domain)
                    if html_pages:
                        print(f"  [Firecrawl] Using cached HTML ({len(html_pages)} pages)")
                
                if not html_pages:
                    # Crawl with Firecrawl
                    firecrawl_client = get_firecrawl_client()
                    
                    crawl_result = firecrawl_client.crawl(
                        url=url,
                        limit=50,  # Match Apify's default
                        scrape_options={
                            "formats": ["html", "markdown"],  # Get both HTML and markdown
                            "onlyMainContent": False
                        }
                    )
                    
                    # Handle Firecrawl response structure
                    pages_data = []
                    if hasattr(crawl_result, 'data'):
                        pages_data = crawl_result.data
                    elif isinstance(crawl_result, dict) and 'data' in crawl_result:
                        pages_data = crawl_result['data']
                    elif isinstance(crawl_result, list):
                        pages_data = crawl_result
                    
                    if not pages_data:
                        raise ValueError("Firecrawl returned no data")
                    
                    # Extract HTML and markdown pages
                    html_pages = []
                    pages_data_for_cache = []
                    seen_urls = set()
                    
                    for page_data in pages_data:
                        # Handle both object and dict response formats
                        if isinstance(page_data, dict):
                            page_url = page_data.get('metadata', {}).get('sourceURL') or page_data.get('metadata', {}).get('source_url') or url
                            html_content = page_data.get('html', '')
                            markdown_content_page = page_data.get('markdown', '')
                        else:
                            page_url = url
                            if hasattr(page_data, 'metadata'):
                                metadata = page_data.metadata
                                if hasattr(metadata, 'sourceURL'):
                                    page_url = metadata.sourceURL
                                elif hasattr(metadata, 'source_url'):
                                    page_url = metadata.source_url
                                elif isinstance(metadata, dict):
                                    page_url = metadata.get('sourceURL') or metadata.get('source_url') or url
                            html_content = getattr(page_data, 'html', '')
                            markdown_content_page = getattr(page_data, 'markdown', '')
                        
                        # Filter duplicates and non-content pages
                        normalized_url = page_url.rstrip('/').split('#')[0].split('?')[0]
                        if normalized_url in seen_urls:
                            continue
                        if not should_include_page(page_url):
                            continue
                        seen_urls.add(normalized_url)
                        
                        if html_content:
                            html_pages.append({
                                "url": page_url,
                                "html": html_content
                            })
                        
                        if markdown_content_page:
                            pages_data_for_cache.append({
                                "url": page_url,
                                "markdown": markdown_content_page
                            })
                    
                    # Cache HTML
                    if html_pages:
                        save_html_cache(domain, html_pages)
                        print(f"  [Firecrawl] Cached HTML ({len(html_pages)} pages)")
                    
                    # Cache markdown
                    if pages_data_for_cache:
                        save_cache(domain, pages_data_for_cache)
                        print(f"  [Firecrawl] Cached markdown ({len(pages_data_for_cache)} pages)")
                    
                    # Use markdown from Firecrawl
                    all_markdown_parts = [page.get("markdown", "") for page in pages_data_for_cache if page.get("markdown")]
                    markdown_content = "\n\n---PAGE BREAK---\n\n".join(all_markdown_parts)
                    
                    pages_crawled = len(pages_data_for_cache)
                    print(f"✓ Successfully crawled {pages_crawled} pages with Firecrawl, {len(markdown_content)} total characters")
                else:
                    # Use cached HTML, convert to markdown if needed
                    # For now, try to get markdown from cache
                    markdown_content = get_cached_markdown(domain)
                    if not markdown_content:
                        # If no markdown cache, we'd need to convert HTML to markdown
                        # For now, return empty and let user know
                        print("  ⚠ HTML cache exists but no markdown cache. Consider using force_refresh=True to regenerate markdown.")
                        markdown_content = ""
                
            else:
                # Use Apify method
                print("🔄 CRAWLING FRESH: Crawling website with Apify Website Content Crawler to find all pages...")
                apify_client = get_apify_client()
                
                # Prepare Actor input - comprehensive settings to capture all content including footer/header
                # Note: Using saveMarkdown=True and not using onlyMainContent ensures footer/header content is included
                actor_input = {
                "startUrls": [{"url": url}],
                "maxCrawlPages": 50,  # Maximum number of pages to crawl
                "crawlerType": "playwright:adaptive",  # Handles both static and dynamic pages
                "saveMarkdown": True,  # Enable markdown output
                "respectRobotsTxtFile": True,  # Respect robots.txt
                "excludeUrlGlobs": [
                    {"glob": "**/sitemap*.xml"},
                    {"glob": "**/robots.txt"},
                    {"glob": "**/favicon.ico"}
                ],
                "removeElementsCssSelector": "script, style, noscript, svg, img[src^='data:'], [role=\"alert\"], [role=\"banner\"], [role=\"dialog\"], [role=\"alertdialog\"], [role=\"region\"][aria-label*=\"skip\" i], [aria-modal=\"true\"]",
                    "htmlTransformer": "readableTextIfPossible"  # Extract readable text but fallback to original HTML for non-article pages
                }
                
                # Run the Apify Actor and wait for completion
                print("  [Apify] Starting crawl job...")
                run = apify_client.actor("apify/website-content-crawler").call(run_input=actor_input)
                
                # Check if run was successful
                if not run or "defaultDatasetId" not in run:
                    raise ValueError("Apify Actor run failed or returned no dataset")
                
                # Fetch dataset items
                print(f"  [Apify] Fetching results from dataset {run['defaultDatasetId']}...")
                dataset_items = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
                
                # Debug: Show total pages discovered
                total_docs = len(dataset_items) if dataset_items else 0
                print(f"  [Discovery] Apify discovered {total_docs} pages total")
                
                # Extract markdown from all crawled pages
                # dataset_items is a list of dictionaries with url, markdown, text, metadata fields
                all_markdown_parts = []
                pages_data = []  # For caching
                seen_urls = set()  # Track URLs to avoid duplicates
                
                for item in dataset_items:
                    # Get URL from item
                    doc_url = item.get("url", url)
                    
                    # Get markdown content (fallback to text if markdown not available)
                    markdown_text = item.get("markdown") or item.get("text", "")
                    
                    # Debug: Show all discovered URLs
                    if not markdown_text:
                        print(f"  [Skipped] {doc_url} (no markdown/text content)")
                        continue
                    
                    # Filter out non-content pages and duplicates
                    if not should_include_page(doc_url):
                        print(f"  [Filtered out] {doc_url} (non-content page)")
                        continue
                    
                    # Normalize URL (remove trailing slash, fragments, etc.) for duplicate detection
                    normalized_url = doc_url.rstrip('/').split('#')[0].split('?')[0]
                    if normalized_url in seen_urls:
                        print(f"  [Filtered out] {doc_url} (duplicate)")
                        continue
                    seen_urls.add(normalized_url)
                    
                    # Extract and include markdown content
                    all_markdown_parts.append(markdown_text)
                    
                    pages_data.append({
                        "url": doc_url,
                        "markdown": markdown_text
                    })
                    print(f"  [Including] {doc_url} ({len(markdown_text)} chars)")
                
                if not all_markdown_parts:
                    raise ValueError("No markdown content found in crawled pages from Apify")
                
                # Combine all markdown from all pages
                # Add page separators to help understand context
                markdown_content = "\n\n---PAGE BREAK---\n\n".join(all_markdown_parts)
                
                pages_crawled = len(all_markdown_parts)
                print(f"✓ Successfully crawled {pages_crawled} pages with Apify, {len(markdown_content)} total characters of markdown content")
                
                # Save to cache - always save when we have fresh crawl data
                if pages_data:
                    cache_saved = save_cache(domain, pages_data)
                    if cache_saved:
                        print(f"✓ Cached data for {domain} ({len(pages_data)} pages)")
                    else:
                        print(f"⚠ Warning: Failed to save cache for {domain}")
                else:
                    print(f"⚠ Warning: No pages data to cache (all pages may have been filtered out)")
        
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

