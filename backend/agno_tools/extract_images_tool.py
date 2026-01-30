"""
Agno-native tool for extracting images from property websites.

Uses Firecrawl (primary) and Apify (fallback) to extract images.
"""

import os
import json
import time
from typing import Optional, Dict, Any, List
from apify_client import ApifyClient
from firecrawl import Firecrawl
from openai import OpenAI
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from tools.cache_manager import (
    get_domain_from_url,
    is_images_cache_valid,
    get_images_cache_age,
    get_cached_images_from_cache,
    save_images_cache,
    is_cache_valid,
    load_cache,
    is_html_cache_valid,
    get_html_cache_age,
    get_cached_html,
    save_html_cache
)
from database import PropertyRepository
from agno_tools.tool import Tool

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
        "strict": False
    }


def extract_images_with_openai(html_content: str, page_url: str, client: OpenAI) -> List[Dict[str, Any]]:
    """Use OpenAI to extract image URLs from HTML content."""
    _log("extract_images_with_openai:entry", "OpenAI image extraction started", {
        "html_length": len(html_content) if html_content else 0,
        "page_url": page_url
    }, "H1")
    
    try:
        max_html_length = 500000
        if len(html_content) > max_html_length:
            html_content = html_content[:max_html_length]
            print(f"  ⚠ HTML truncated to {max_html_length} characters for OpenAI processing")
        
        _log("extract_images_with_openai:before_api_call", "Before OpenAI API call", {
            "html_length": len(html_content)
        }, "H1")
        
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
        
        _log("extract_images_with_openai:after_api_call", "OpenAI API call completed", {}, "H1")
        
        if not response.choices or not response.choices[0].message.content:
            _log("extract_images_with_openai:no_content", "OpenAI response has no content", {}, "H1")
            print("  ⚠ OpenAI returned no content")
            return []
        
        content = response.choices[0].message.content
        
        _log("extract_images_with_openai:before_json_parse", "Before JSON parsing", {
            "content_length": len(content)
        }, "H1")
        
        try:
            extracted_data = json.loads(content)
            images = extracted_data.get("images", [])
            
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
            
            _log("extract_images_with_openai:after_json_parse", "JSON parsing successful", {
                "images_count": len(result)
            }, "H1")
            
            return result
            
        except json.JSONDecodeError as e:
            _log("extract_images_with_openai:json_error", "JSON parsing failed", {
                "error": str(e)
            }, "H1")
            print(f"  ⚠ Error parsing OpenAI response: {e}")
            return []
            
    except Exception as e:
        _log("extract_images_with_openai:exception", "Exception during OpenAI extraction", {
            "error": str(e),
            "error_type": type(e).__name__
        }, "H1")
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
    """Transform Apify Actor output format to our image format."""
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
        "alt": alt_text,
        "width": apify_image.get("width"),
        "height": apify_image.get("height")
    }


def _try_firecrawl_extraction(url, domain, force_refresh):
    """Try to extract images using Firecrawl and OpenAI."""
    try:
        print("  [Method: Firecrawl] Attempting Firecrawl extraction...")
        
        html_pages = None
        html_cache_valid = is_html_cache_valid(domain)
        
        if html_cache_valid and not force_refresh:
            html_pages = get_cached_html(domain)
            if html_pages:
                print(f"    ✓ Using cached HTML ({len(html_pages)} pages)")
        
        if not html_pages:
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
            
            pages_data = []
            if hasattr(crawl_result, 'data'):
                pages_data = crawl_result.data
            elif isinstance(crawl_result, dict) and 'data' in crawl_result:
                pages_data = crawl_result['data']
            elif isinstance(crawl_result, list):
                pages_data = crawl_result
            
            if not pages_data:
                return [], False, "Firecrawl returned no data"
            
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
            
            if html_pages:
                save_html_cache(domain, html_pages)
                print(f"    ✓ Cached HTML ({len(html_pages)} pages)")
        
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


def extract_images(
    url: str,
    use_cache: Optional[bool] = None,
    force_refresh: bool = False,
) -> dict:
    """
    Extract images from a property website.
    
    Uses Firecrawl and OpenAI first, falls back to Apify if needed.
    """
    if not url:
        return {
            "error": "URL is required",
            "images": []
        }
    
    print(f"Extracting images from property website: {url}")
    
    domain = get_domain_from_url(url)
    cache_valid = is_images_cache_valid(domain)
    cache_age = get_images_cache_age(domain) if cache_valid else None
    
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
        return {
            "cache_available": True,
            "cache_age_hours": cache_age,
            "domain": domain,
            "message": f"Cached images available from {cache_age:.1f} hours ago. Set use_cache=True to use cache, or force_refresh=True to extract fresh.",
            "images": []
        }
    
    try:
        images = []
        
        if should_use_cache and cache_valid:
            images = get_cached_images_from_cache(domain) or []
            if images:
                print(f"✓ USING CACHE: Loaded {len(images)} images from cache (age: {cache_age:.1f} hours)")
            else:
                print("⚠ Cache exists but images list is empty - will extract fresh")
                should_use_cache = False
        
        if not should_use_cache or not images:
            print("🔄 EXTRACTING FRESH: Trying Firecrawl first, then Apify fallback...")
            
            firecrawl_images, firecrawl_success, firecrawl_error = _try_firecrawl_extraction(url, domain, force_refresh)
            
            if firecrawl_success and firecrawl_images:
                images = firecrawl_images
                print(f"✓ Using Firecrawl results: {len(images)} images")
            else:
                print(f"  [Fallback: Apify] Firecrawl {'returned no images' if firecrawl_success else 'failed'}, trying Apify...")
                
                discovered_pages = []
                markdown_cache_valid = is_cache_valid(domain)
                
                if markdown_cache_valid:
                    cache_data = load_cache(domain)
                    if cache_data and cache_data.get("pages"):
                        discovered_pages = [page.get("url") for page in cache_data["pages"] if page.get("url")]
                        if discovered_pages:
                            print(f"  [Step 1] Reusing {len(discovered_pages)} pages from markdown cache")
                
                if not discovered_pages:
                    print("  [Step 1] Discovering pages using website-content-crawler (handles JavaScript)...")
                    from tools.crawl_property_website import get_apify_client as get_crawl_apify_client
                    crawl_apify_client = get_crawl_apify_client()
                    
                    crawl_actor_input = {
                        "startUrls": [{"url": url}],
                        "maxCrawlPages": 20,
                        "crawlerType": "playwright:adaptive",
                        "respectRobotsTxtFile": True,
                    }
                    
                    crawl_run = crawl_apify_client.actor("apify/website-content-crawler").call(run_input=crawl_actor_input)
                    crawl_dataset = crawl_apify_client.dataset(crawl_run["defaultDatasetId"])
                    for page_item in crawl_dataset.iterate_items():
                        page_url = page_item.get("url", "")
                        if page_url and page_url not in discovered_pages:
                            discovered_pages.append(page_url)
                    
                    print(f"  [Step 1] Discovered {len(discovered_pages)} pages")
                
                print(f"  [Step 2] Extracting images from {len(discovered_pages)} pages...")
                apify_client = get_apify_client()
                
                images = []
                seen_urls = set()
                
                for page_idx, page_url in enumerate(discovered_pages, 1):
                    print(f"  [Step 2.{page_idx}] Extracting images from: {page_url}")
                    
                    actor_input = {
                        "startUrl": page_url,
                        "maxCrawlDepth": 1,
                        "maxCrawlPages": 1,
                        "maxConcurrency": 10,
                        "imageExtensions": ["jpg", "jpeg", "png", "gif", "webp", "svg", "bmp"],
                        "respectRobotsTxt": True,
                        "useScope": True,
                        "scope": [domain],
                        "includeSubdomains": False,
                        "userAgent": "Mozilla/5.0 (compatible; ApifyBot/1.0; +https://apify.com/bot)"
                    }
                    
                    try:
                        run = apify_client.actor("gomorrhadev/website-image-scraper").call(run_input=actor_input)
                        dataset = apify_client.dataset(run["defaultDatasetId"])
                        
                        page_images_count = 0
                        for item in dataset.iterate_items():
                            transformed = transform_apify_image(item)
                            
                            if not transformed["url"]:
                                continue
                            
                            if transformed["url"] in seen_urls:
                                continue
                            
                            images.append(transformed)
                            seen_urls.add(transformed["url"])
                            page_images_count += 1
                        
                        print(f"    ✓ Found {page_images_count} images on {page_url}")
                    except Exception as page_error:
                        print(f"    ⚠ Error extracting images from {page_url}: {page_error}")
                        continue
                
                print(f"✓ Successfully extracted {len(images)} images using Apify fallback")
            
            if images:
                cache_saved = save_images_cache(domain, images)
                if cache_saved:
                    print(f"✓ Cached images for {domain} ({len(images)} images)")
                else:
                    print(f"⚠ Warning: Failed to save images cache for {domain}")
            else:
                print(f"⚠ Warning: No images found to cache")
        
        try:
            property_repo = PropertyRepository()
            property_obj = property_repo.get_property_by_website_url(url)
            
            if property_obj and property_obj.id:
                images_added = property_repo.add_property_images(property_obj.id, images)
                if images_added > 0:
                    print(f"✓ Saved {images_added} images to database for property")
        except Exception as db_error:
            print(f"⚠ Warning: Error saving images to database: {db_error}")
        
        result = {
            "images": images
        }
        
        if should_use_cache and cache_valid:
            result["cache_info"] = {
                "used_cache": True,
                "cache_age_hours": cache_age
            }
            print(f"\n[Cache Status] ✓ Used cached images (age: {cache_age:.1f} hours)")
        else:
            result["cache_info"] = {
                "used_cache": False,
                "cached": True
            }
            print(f"\n[Cache Status] ✓ Extracted fresh images and saved to cache")
        
        print(f"[Tool Execution Complete]")
        return result
    
    except ValueError as e:
        print(f"Error: {e}")
        return {
            "error": str(e),
            "images": []
        }
    
    except Exception as e:
        print(f"Error extracting images from property website: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to extract images from property website: {str(e)}",
            "images": []
        }


# Create Agno Tool
extract_images_tool = Tool(
    name="extract_images",
    description="Extract all images from a property website using Apify and Firecrawl. Returns list of image URLs with metadata.",
    func=extract_images,
)
