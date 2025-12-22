"""
Tool for extracting images from property websites using Firecrawl (primary) and Apify (fallback).

Primary function: Uses Firecrawl to crawl websites and OpenAI to extract image URLs from HTML.
Falls back to Apify website-image-scraper Actor if Firecrawl returns no images or fails.
Returns a list of images found across the website.
"""

import os
import json
import time
from typing import Dict, Any, List
from apify_client import ApifyClient
from firecrawl import Firecrawl
from openai import OpenAI
from .cache_manager import (
    get_domain_from_url,
    is_images_cache_valid,
    get_images_cache_age,
    get_cached_images_from_cache,
    save_images_cache,
    is_cache_valid,  # For markdown cache check
    load_cache,  # For loading markdown cache data
    is_html_cache_valid,
    get_html_cache_age,
    get_cached_html,
    save_html_cache
)
from database import PropertyRepository

# #region agent log
LOG_PATH = "/Users/rajivchopra/Property Onboarding Agent/.cursor/debug.log"
def _log(location, message, data=None, hypothesis_id=None):
    try:
        with open(LOG_PATH, "a") as f:
            log_entry = {
                "timestamp": int(time.time() * 1000),
                "location": location,
                "message": message,
                "data": data or {},
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": hypothesis_id
            }
            f.write(json.dumps(log_entry) + "\n")
    except:
        pass
# #endregion


def get_firecrawl_client():
    """Initialize and return Firecrawl client with API key from environment."""
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError(
            "FIRECRAWL_API_KEY not found. Please set it in your environment variables."
        )
    return Firecrawl(api_key=api_key)


def get_openai_client():
    """Initialize and return OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Please set it in your environment variables."
        )
    return OpenAI(api_key=api_key)


def get_image_extraction_schema():
    """Returns the JSON schema for image extraction."""
    return {
        "type": "object",
        "properties": {
            "images": {
                "type": "array",
                "description": "List of images found in the HTML",
                "items": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "Full URL of the image"
                        },
                        "alt": {
                            "type": "string",
                            "description": "Alt text of the image if available"
                        },
                        "width": {
                            "type": "integer",
                            "description": "Width of the image in pixels if available in HTML attributes"
                        },
                        "height": {
                            "type": "integer",
                            "description": "Height of the image in pixels if available in HTML attributes"
                        }
                    },
                    "required": ["url"]
                }
            }
        },
        "required": ["images"]
    }


def get_openai_json_schema():
    """Convert our JSON schema to OpenAI's JSON schema format for structured output."""
    base_schema = get_image_extraction_schema()
    return {
        "name": "extracted_images",
        "description": "Extracted image URLs and metadata from HTML content",
        "schema": base_schema,
        "strict": False  # Allow null values for missing fields
    }


def extract_images_with_openai(html_content: str, page_url: str, client: OpenAI) -> List[Dict[str, Any]]:
    """
    Use OpenAI to extract image URLs from HTML content.
    
    Args:
        html_content: The HTML content from Firecrawl
        page_url: The URL of the page being processed
        client: OpenAI client instance
        
    Returns:
        List of image dictionaries with url, page_url, alt, width, height
    """
    # #region agent log
    _log("extract_images_with_openai:entry", "OpenAI image extraction started", {
        "html_length": len(html_content) if html_content else 0,
        "page_url": page_url
    }, "H1")
    # #endregion
    
    try:
        # Truncate HTML if too long (OpenAI has token limits)
        max_html_length = 500000  # ~500KB of HTML
        if len(html_content) > max_html_length:
            html_content = html_content[:max_html_length]
            print(f"  ⚠ HTML truncated to {max_html_length} characters for OpenAI processing")
        
        # #region agent log
        _log("extract_images_with_openai:before_api_call", "Before OpenAI API call", {
            "html_length": len(html_content)
        }, "H1")
        # #endregion
        
        response = client.beta.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at extracting image URLs from HTML content. Extract all image URLs found in img tags, background-image CSS properties, and any other image references. Include alt text, width, and height attributes when available. Return absolute URLs (resolve relative URLs to the page URL provided)."
                },
                {
                    "role": "user",
                    "content": f"""Extract all image URLs from the following HTML content. The page URL is: {page_url}

HTML Content:
{html_content}

Extract all image URLs including:
- img src attributes
- background-image CSS properties
- Any other image references

For each image, include:
- Full absolute URL (resolve relative URLs)
- Alt text if available
- Width and height if specified in HTML attributes

Return only valid image URLs (jpg, jpeg, png, gif, webp, svg, bmp extensions or data URLs)."""
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": get_openai_json_schema()
            },
            temperature=0.1
        )
        
        # #region agent log
        _log("extract_images_with_openai:after_api_call", "OpenAI API call completed", {}, "H1")
        # #endregion
        
        # Extract response content
        if not response.choices or not response.choices[0].message.content:
            # #region agent log
            _log("extract_images_with_openai:no_content", "OpenAI response has no content", {}, "H1")
            # #endregion
            print("  ⚠ OpenAI returned no content")
            return []
        
        content = response.choices[0].message.content
        
        # #region agent log
        _log("extract_images_with_openai:before_json_parse", "Before JSON parsing", {
            "content_length": len(content)
        }, "H1")
        # #endregion
        
        # Parse JSON response
        try:
            extracted_data = json.loads(content)
            images = extracted_data.get("images", [])
            
            # Transform to our format and add page_url
            result = []
            for img in images:
                if img.get("url"):
                    result.append({
                        "url": img.get("url"),
                        "page_url": page_url,
                        "alt": img.get("alt"),
                        "width": img.get("width"),
                        "height": img.get("height")
                    })
            
            # #region agent log
            _log("extract_images_with_openai:after_json_parse", "JSON parsing successful", {
                "images_count": len(result)
            }, "H1")
            # #endregion
            
            return result
            
        except json.JSONDecodeError as e:
            # #region agent log
            _log("extract_images_with_openai:json_error", "JSON parsing failed", {
                "error": str(e)
            }, "H1")
            # #endregion
            print(f"  ⚠ Error parsing OpenAI response: {e}")
            return []
            
    except Exception as e:
        # #region agent log
        _log("extract_images_with_openai:exception", "Exception during OpenAI extraction", {
            "error": str(e),
            "error_type": type(e).__name__
        }, "H1")
        # #endregion
        if "rate_limit" in str(e).lower():
            print("  ⚠ OpenAI rate limit reached. Try using cached data (use_cache=True) to reduce API calls.")
        else:
            print(f"  ⚠ Error in OpenAI image extraction: {e}")
        return []


def get_apify_client():
    """Initialize and return Apify client with API token from environment."""
    token = os.getenv("APIFY_API_TOKEN")
    if not token:
        raise ValueError(
            "APIFY_API_TOKEN not found. Please set it in your environment variables."
        )
    return ApifyClient(token=token)


def transform_apify_image(apify_image):
    """
    Transform Apify Actor output format to our image format.
    
    Args:
        apify_image: Dictionary from Apify Actor with url, sourcePage, foundAt, and potentially alt text fields
        
    Returns:
        Dictionary with url, page_url, alt, width, height
    """
    # Extract alt text from common field names
    # Check multiple possible field names that Apify Actor might use
    alt_text = (
        apify_image.get("alt") or
        apify_image.get("altText") or
        apify_image.get("alt_text") or
        apify_image.get("title") or
        apify_image.get("description") or
        apify_image.get("name") or
        None
    )
    
    return {
        "url": apify_image.get("url", ""),
        "page_url": apify_image.get("sourcePage", ""),
        "alt": alt_text,  # Extract alt text from Apify Actor response
        "width": apify_image.get("width"),  # Extract width if available
        "height": apify_image.get("height")  # Extract height if available
    }


def get_tool_definition():
    """Returns the tool definition for OpenAI function calling."""
    return {
        "type": "function",
        "function": {
            "name": "extract_website_images",
            "description": "Extract images from a property website using Firecrawl and OpenAI (primary method), with Apify Actor as fallback. Checks cache first - if cached data exists, will use it unless force_refresh is True. Returns a list of image URLs found across the website.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the property website to extract images from"
                    },
                    "use_cache": {
                        "type": "boolean",
                        "description": "Whether to use cached data if available. If None/not provided, the agent will prompt the user. If True, uses cache. If False, forces fresh extraction."
                    },
                    "force_refresh": {
                        "type": "boolean",
                        "description": "Force a fresh extraction even if cache exists. Defaults to False.",
                        "default": False
                    }
                },
                "required": ["url"]
            }
        }
    }


def _try_firecrawl_extraction(url, domain, force_refresh):
    """
    Try to extract images using Firecrawl and OpenAI.
    
    Args:
        url: Website URL
        domain: Domain name
        force_refresh: Whether to force refresh
        
    Returns:
        Tuple of (images_list, success_flag, error_message)
    """
    try:
        print("  [Method: Firecrawl] Attempting Firecrawl extraction...")
        
        # Check for HTML cache first
        html_pages = None
        html_cache_valid = is_html_cache_valid(domain)
        
        if html_cache_valid and not force_refresh:
            html_pages = get_cached_html(domain)
            if html_pages:
                print(f"    ✓ Using cached HTML ({len(html_pages)} pages)")
        
        if not html_pages:
            # Need to crawl with Firecrawl
            print("    Crawling with Firecrawl...")
            firecrawl_client = get_firecrawl_client()
            
            crawl_result = firecrawl_client.crawl(
                url=url,
                limit=20,
                scrape_options={
                    "formats": ["html"],
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
                return [], False, "Firecrawl returned no data"
            
            # Extract HTML pages for caching
            html_pages = []
            for page_data in pages_data:
                if isinstance(page_data, dict):
                    page_url = page_data.get('metadata', {}).get('sourceURL') or page_data.get('metadata', {}).get('source_url') or url
                    html_content = page_data.get('html', '')
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
                
                if html_content:
                    html_pages.append({
                        "url": page_url,
                        "html": html_content
                    })
            
            # Cache HTML pages
            if html_pages:
                save_html_cache(domain, html_pages)
                print(f"    ✓ Cached HTML ({len(html_pages)} pages)")
        
        # Extract images from HTML using OpenAI
        openai_client = get_openai_client()
        all_images = []
        seen_urls = set()
        
        for html_page in html_pages:
            page_url = html_page.get("url", url)
            html_content = html_page.get("html", "")
            
            if html_content:
                page_images = extract_images_with_openai(html_content, page_url, openai_client)
                for img in page_images:
                    img_url = img.get("url", "")
                    if img_url and img_url not in seen_urls:
                        all_images.append(img)
                        seen_urls.add(img_url)
        
        if all_images:
            print(f"  ✓ Firecrawl extraction successful: {len(all_images)} images found")
            return all_images, True, None
        else:
            print(f"  ⚠ Firecrawl extraction returned no images")
            return [], False, "No images found"
            
    except Exception as e:
        error_msg = str(e)
        print(f"  ⚠ Firecrawl extraction failed: {error_msg}")
        return [], False, error_msg


def execute(arguments):
    """
    Execute the extract_website_images tool.
    
    Uses Firecrawl and OpenAI first, falls back to Apify if needed.
    Returns a list of images found across the website.
    
    Process:
    1. Checks cache first (if use_cache is True or None)
    2. If no cache or force_refresh, tries Firecrawl method first
    3. Falls back to Apify if Firecrawl returns no images or fails
    4. Saves extracted images to cache
    5. Returns list of images
    
    Args:
        arguments: Dictionary containing tool arguments
            - url (str): The URL of the property website
            - use_cache (bool, optional): Whether to use cached data. None = prompt user, True = use cache, False = fresh extraction
            - force_refresh (bool, optional): Force fresh extraction even if cache exists. Defaults to False.
        
    Returns:
        Dictionary with images list and cache_info
    """
    url = arguments.get("url", "")
    use_cache = arguments.get("use_cache")  # None, True, or False
    force_refresh = arguments.get("force_refresh", False)
    
    if not url:
        return {
            "error": "URL is required",
            "images": []
        }
    
    print(f"Extracting images from property website: {url}")
    
    # Get domain for cache lookup
    domain = get_domain_from_url(url)
    cache_valid = is_images_cache_valid(domain)
    cache_age = get_images_cache_age(domain) if cache_valid else None
    
    # Determine if we should use cache
    should_use_cache = False
    if force_refresh:
        should_use_cache = False
        print("Force refresh requested - ignoring cache")
    elif use_cache is True:
        if cache_valid:
            should_use_cache = True
            print(f"Using cached images (age: {cache_age:.1f} hours)")
        else:
            print("Cache requested but not valid - will extract fresh")
    elif use_cache is False:
        should_use_cache = False
        print("Fresh extraction requested - ignoring cache")
    elif cache_valid:
        # use_cache is None - return cache info for agent to prompt user
        return {
            "cache_available": True,
            "cache_age_hours": cache_age,
            "domain": domain,
            "message": f"Cached images available from {cache_age:.1f} hours ago. Set use_cache=True to use cache, or force_refresh=True to extract fresh.",
            "images": []
        }
    
    try:
        images = []
        
        # Try to use cache if requested
        if should_use_cache and cache_valid:
            images = get_cached_images_from_cache(domain) or []
            if images:
                print(f"✓ USING CACHE: Loaded {len(images)} images from cache (age: {cache_age:.1f} hours)")
            else:
                print("⚠ Cache exists but images list is empty - will extract fresh")
                should_use_cache = False
        
        # Extract images if not using cache
        if not should_use_cache or not images:
            print("🔄 EXTRACTING FRESH: Trying Firecrawl first, then Apify fallback...")
            
            # Try Firecrawl method first
            firecrawl_images, firecrawl_success, firecrawl_error = _try_firecrawl_extraction(url, domain, force_refresh)
            
            if firecrawl_success and firecrawl_images:
                images = firecrawl_images
                print(f"✓ Using Firecrawl results: {len(images)} images")
            else:
                # Fallback to Apify
                print(f"  [Fallback: Apify] Firecrawl {'returned no images' if firecrawl_success else 'failed'}, trying Apify...")
                
                # STEP 1: Get page URLs (independent of image cache settings)
                # Check markdown cache first - reuse if available, regardless of image cache settings
                discovered_pages = []
                markdown_cache_valid = is_cache_valid(domain)  # Check markdown cache (independent)
                
                if markdown_cache_valid:
                    # Extract page URLs from markdown cache
                    cache_data = load_cache(domain)
                    if cache_data and cache_data.get("pages"):
                        discovered_pages = [page.get("url") for page in cache_data["pages"] if page.get("url")]
                        if discovered_pages:
                            print(f"  [Step 1] Reusing {len(discovered_pages)} pages from markdown cache")
                
                if not discovered_pages:
                    # Only run crawler if markdown cache doesn't exist or is invalid
                    print("  [Step 1] Discovering pages using website-content-crawler (handles JavaScript)...")
                    from .crawl_property_website import get_apify_client as get_crawl_apify_client
                    crawl_apify_client = get_crawl_apify_client()
                    
                    crawl_actor_input = {
                        "startUrls": [{"url": url}],
                        "maxCrawlPages": 20,
                        "crawlerType": "playwright:adaptive",  # Handles JavaScript-rendered pages
                        "respectRobotsTxtFile": True,
                    }
                    
                    crawl_run = crawl_apify_client.actor("apify/website-content-crawler").call(run_input=crawl_actor_input)
                    crawl_dataset = crawl_apify_client.dataset(crawl_run["defaultDatasetId"])
                    for page_item in crawl_dataset.iterate_items():
                        page_url = page_item.get("url", "")
                        if page_url and page_url not in discovered_pages:
                            discovered_pages.append(page_url)
                    
                    print(f"  [Step 1] Discovered {len(discovered_pages)} pages")
                
                # Now extract images from all discovered pages
                # Call the Actor once per page since it may only support startUrl (singular)
                print(f"  [Step 2] Extracting images from {len(discovered_pages)} pages...")
                apify_client = get_apify_client()
                
                # Transform Apify results to our format
                images = []
                seen_urls = set()  # Track URLs to avoid duplicates
                raw_items_count = 0
                filtered_duplicates_count = 0
                filtered_empty_url_count = 0
                unique_pages = set()
                
                # Process each discovered page separately
                for page_idx, page_url in enumerate(discovered_pages, 1):
                    print(f"  [Step 2.{page_idx}] Extracting images from: {page_url}")
                    
                    # Prepare Actor input for this single page
                    actor_input = {
                        "startUrl": page_url,  # Use singular startUrl (Actor may not support startUrls array)
                        "maxCrawlDepth": 1,  # Only crawl this specific page (depth 1 = just this page)
                        "maxCrawlPages": 1,  # Only this one page
                        "maxConcurrency": 10,
                        "imageExtensions": ["jpg", "jpeg", "png", "gif", "webp", "svg", "bmp"],
                        "respectRobotsTxt": True,
                        "useScope": True,
                        "scope": [domain],
                        "includeSubdomains": False,
                        "userAgent": "Mozilla/5.0 (compatible; ApifyBot/1.0; +https://apify.com/bot)"
                    }
                    
                    try:
                        # Run the Actor for this page
                        run = apify_client.actor("gomorrhadev/website-image-scraper").call(run_input=actor_input)
                        
                        # Fetch results from the dataset
                        dataset = apify_client.dataset(run["defaultDatasetId"])
                        
                        # Apify Actor returns dataset items directly as image objects: {url, sourcePage, foundAt}
                        # iterate_items() handles pagination and returns items one by one
                        page_images_count = 0
                        for item in dataset.iterate_items():
                            raw_items_count += 1
                            # Each item is a direct image object
                            transformed = transform_apify_image(item)
                            if transformed.get("page_url"):
                                unique_pages.add(transformed["page_url"])
                            
                            if not transformed["url"]:
                                filtered_empty_url_count += 1
                                continue
                            
                            if transformed["url"] in seen_urls:
                                filtered_duplicates_count += 1
                                continue
                            
                            images.append(transformed)
                            seen_urls.add(transformed["url"])
                            page_images_count += 1
                        
                        print(f"    ✓ Found {page_images_count} images on {page_url}")
                    except Exception as page_error:
                        print(f"    ⚠ Error extracting images from {page_url}: {page_error}")
                        continue  # Continue with next page
                
                print(f"✓ Successfully extracted {len(images)} images using Apify fallback")
            
            # Set total_images after both paths so it's always available
            total_images = len(images)
            
            # Save to cache - always save when we have fresh extraction data
            if images:
                cache_saved = save_images_cache(domain, images)
                if cache_saved:
                    print(f"✓ Cached images for {domain} ({total_images} images)")
                else:
                    print(f"⚠ Warning: Failed to save images cache for {domain}")
            else:
                print(f"⚠ Warning: No images found to cache")
        
        # Save images to database if we have a property for this URL
        try:
            property_repo = PropertyRepository()
            # Try to find property by website URL
            property_obj = property_repo.get_property_by_website_url(url)
            
            if property_obj and property_obj.id:
                # Add images to property
                images_added = property_repo.add_property_images(property_obj.id, images)
                if images_added > 0:
                    print(f"✓ Saved {images_added} images to database for property")
        except Exception as db_error:
            print(f"⚠ Warning: Error saving images to database: {db_error}")
            # Don't fail the extraction if database save fails
        
        # Return images
        result = {
            "images": images
        }
        
        # Add cache info and show status
        if should_use_cache and cache_valid:
            result["cache_info"] = {
                "used_cache": True,
                "cache_age_hours": cache_age
            }
            print(f"\n[Cache Status] ✓ Used cached images (age: {cache_age:.1f} hours)")
        else:
            result["cache_info"] = {
                "used_cache": False,
                "cached": True  # Data was just cached
            }
            print(f"\n[Cache Status] ✓ Extracted fresh images and saved to cache")
        
        print(f"[Tool Execution Complete]")
        return result
    
    except ValueError as e:
        # API key missing or other value errors
        print(f"Error: {e}")
        return {
            "error": str(e),
            "images": []
        }
    
    except Exception as e:
        # Other errors (network, API, etc.)
        print(f"Error extracting images from property website: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to extract images from property website: {str(e)}",
            "images": []
        }

