"""
Tool for extracting images from property websites using Firecrawl (primary) and Apify (fallback).

Primary function: Uses Firecrawl to crawl websites and OpenAI to extract image URLs from HTML.
Falls back to Apify website-image-scraper Actor if Firecrawl returns no images or fails.
Returns a list of images found across the website.
"""

import os
import json
import re
import time
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
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


# Minimum dimensions for images to be considered useful for content generation
MIN_IMAGE_WIDTH = 200
MIN_IMAGE_HEIGHT = 200

# Known CDN transform parameter patterns to strip for normalization
# These are parameters that only affect size/quality/format, not the actual image content
CLOUDINARY_TRANSFORM_PATTERN = re.compile(
    r'/image/upload/'           # Cloudinary upload path prefix
    r'(?:[^/]+/)*'              # One or more transform segments (e.g., q_auto,f_auto,c_fill,w_175/)
    r'(?=s3/|v\d+/)'           # Until we hit the actual asset path (s3/ or version like v1234/)
)

# Common CDN resize query parameters to strip
CDN_RESIZE_PARAMS = {
    'w', 'h', 'width', 'height', 'resize', 'fit', 'crop', 'quality', 'q',
    'dpr', 'ar', 'c', 'f', 'g', 'e', 'fl', 'auto', 'format', 'fm',
    'sharp', 'blur', 'sat', 'bri', 'con', 'hue',
}


def normalize_image_url(url: str) -> str:
    """
    Normalize a CDN image URL to its canonical base form for deduplication.

    Strips CDN transform parameters (resize, crop, quality, format) so that
    the same image served at different resolutions maps to the same key.

    Supports:
    - RentCafe/Cloudinary (resource.rentcafe.com/image/upload/...)
    - Cloudinary direct (res.cloudinary.com/.../image/upload/...)
    - Generic CDN query parameter stripping

    Args:
        url: The full image URL

    Returns:
        Normalized URL string suitable for dedup comparison
    """
    if not url:
        return url

    # Handle Cloudinary-style URLs (RentCafe uses Cloudinary CDN)
    # Pattern: .../image/upload/{transforms}/s3/{actual_path}
    # We want to extract just the base image path after transforms
    if '/image/upload/' in url:
        # Find the base image path - everything after transform segments
        # Transforms are comma-separated params like q_auto,f_auto,c_fill,w_175
        # The actual path starts with s3/ or after all transform segments

        parts = url.split('/image/upload/')
        if len(parts) == 2:
            base_domain = parts[0] + '/image/upload/'
            rest = parts[1]

            # Split remaining path into segments
            segments = rest.split('/')

            # Find where the actual image path starts
            # Transform segments contain underscores with params like w_175, c_fill, etc.
            # OR they look like x_0,y_0,w_3240,h_2160,c_crop (crop coordinates)
            image_path_start = 0
            for i, segment in enumerate(segments):
                # If segment starts with s3 or v followed by digits, it's the real path
                if segment.startswith('s3') or re.match(r'^v\d+$', segment):
                    image_path_start = i
                    break
                # If segment contains a dot and looks like a filename, it's the real path
                if '.' in segment and not any(p in segment for p in ['c_', 'w_', 'h_', 'f_', 'q_', 'g_', 'ar_', 'dpr_', 'fl_', 'e_', 'x_', 'y_']):
                    image_path_start = i
                    break
                # If segment doesn't look like a transform param, assume it's path
                if not re.match(r'^[a-z_]+[,]', segment) and not re.match(r'^[a-z]_', segment) and segment not in ('dpr_2',):
                    # Check if it contains typical transform patterns
                    has_transform = any(
                        re.search(rf'(?:^|,){p}', segment)
                        for p in ['c_', 'w_', 'h_', 'f_', 'q_', 'g_', 'ar_', 'dpr_', 'fl_', 'e_', 'x_', 'y_']
                    )
                    if not has_transform:
                        image_path_start = i
                        break

            # Reconstruct with just base + actual path (no transforms)
            actual_path = '/'.join(segments[image_path_start:])
            if actual_path:
                return base_domain + actual_path

    # For non-Cloudinary URLs, strip common resize query parameters
    parsed = urlparse(url)
    if parsed.query:
        params = parse_qs(parsed.query, keep_blank_values=True)
        filtered_params = {
            k: v for k, v in params.items()
            if k.lower() not in CDN_RESIZE_PARAMS
        }
        new_query = urlencode(filtered_params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    return url


def get_cloudinary_delivery_width(url: str) -> int:
    """
    Extract the actual delivery width from a Cloudinary transform URL.

    Cloudinary URLs can chain multiple transforms:
      x_0,y_0,w_3240,h_2160,c_crop / q_auto,f_auto,c_limit,w_576 / s3/...
    The first w_3240 is the crop region (source), not the output.
    The delivery width is the w_ in the segment with c_limit, c_fill, or c_lfill.

    Returns:
        Delivery width in pixels, or 0 if not a Cloudinary URL / not found
    """
    if '/image/upload/' not in url:
        return 0

    parts = url.split('/image/upload/')
    if len(parts) != 2:
        return 0

    # Split the transform chain into segments
    segments = parts[1].split('/')

    for segment in segments:
        # Look for delivery commands (c_limit, c_fill, c_lfill)
        if any(cmd in segment for cmd in ['c_limit', 'c_fill', 'c_lfill']):
            # Extract w_ from this delivery segment
            w_match = re.search(r'(?:^|,)w_(\d+)', segment)
            if w_match:
                return int(w_match.group(1))

    return 0


def get_best_resolution_image(images: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Given a list of image variants (same content, different resolutions),
    return the one with the highest resolution.

    For Cloudinary URLs, uses the delivery width (from c_limit/c_fill/c_lfill)
    as the primary signal, since DB dimensions can be unreliable (they may
    reflect crop regions or HTML attribute values rather than actual image size).

    Args:
        images: List of image dicts with url, width, height fields

    Returns:
        The image dict with the highest resolution
    """
    if not images:
        return {}
    if len(images) == 1:
        return images[0]

    def resolution_score(img):
        url = img.get("url", "")

        # Priority 1: Cloudinary delivery width (most reliable for CDN variants)
        cdn_width = get_cloudinary_delivery_width(url)
        if cdn_width > 0:
            return cdn_width * 1000

        # Priority 2: DB dimensions (but only if no CDN URL hints)
        w = img.get("width") or 0
        h = img.get("height") or 0
        if w > 0 and h > 0:
            return w * h
        if w > 0:
            return w * 1000
        if h > 0:
            return h * 1000

        # Priority 3: Generic URL width hints (non-Cloudinary)
        width_match = re.search(r'w[_=](\d+)', url)
        if width_match:
            return int(width_match.group(1)) * 1000

        return 0  # Unknown resolution

    return max(images, key=resolution_score)


def is_image_too_small(img: Dict[str, Any]) -> bool:
    """
    Check if an image is below minimum dimensions for content generation.

    Dimensions below 10px are treated as unknown/placeholder values (common in
    lazy-loading patterns where HTML attributes are set to 1x1 or 3x3).

    Args:
        img: Image dict with optional width/height fields

    Returns:
        True if the image is too small to be useful
    """
    # Minimum plausible dimension - anything below this is a placeholder, not a real size
    PLACEHOLDER_THRESHOLD = 10

    width = img.get("width") or 0
    height = img.get("height") or 0

    # Treat very small values (0, 1, 2, 3...) as unknown/placeholder, not as actual dimensions
    # These are commonly set by lazy-loading libraries or CSS tricks
    if 0 < width < PLACEHOLDER_THRESHOLD:
        width = 0  # Treat as unknown
    if 0 < height < PLACEHOLDER_THRESHOLD:
        height = 0  # Treat as unknown

    # If both dimensions known (and plausible) and both are tiny, skip it
    if width >= PLACEHOLDER_THRESHOLD and height >= PLACEHOLDER_THRESHOLD:
        return width < MIN_IMAGE_WIDTH and height < MIN_IMAGE_HEIGHT

    # If only width known (and plausible) and it's tiny
    if width >= PLACEHOLDER_THRESHOLD and width < MIN_IMAGE_WIDTH:
        return True

    # If only height known (and plausible) and it's tiny
    if height >= PLACEHOLDER_THRESHOLD and height < MIN_IMAGE_HEIGHT:
        return True

    # No reliable dimensions known - check URL for width hints
    url = img.get("url", "")
    width_match = re.search(r'w[_=](\d+)', url)
    if width_match:
        url_width = int(width_match.group(1))
        if url_width >= PLACEHOLDER_THRESHOLD and url_width < MIN_IMAGE_WIDTH:
            return True

    # When dimensions are unknown, give the benefit of the doubt
    return False


def is_junk_image(img: Dict[str, Any]) -> bool:
    """
    Check if an image is likely junk (tracking pixel, widget, icon, etc.)
    based on URL patterns and metadata.

    Args:
        img: Image dict with url, alt, width, height

    Returns:
        True if the image should be filtered out
    """
    url = (img.get("url") or "").lower()
    alt = (img.get("alt") or "").lower()

    # Known junk URL patterns
    junk_patterns = [
        'userway.org',          # Accessibility widget
        'tracking', 'pixel',    # Tracking pixels
        'spacer', 'blank',      # Spacer images
        'favicon', 'icon',      # Icons
        '/spinner',             # Loading spinners
        'data:image/gif',       # 1px tracking GIFs
        'data:image/png;base64,iVBOR',  # Tiny base64 images
        'googletagmanager',     # Analytics
        'facebook.com/tr',      # FB pixel
        'doubleclick.net',      # Ad tracking
        'google-analytics',     # Analytics
    ]

    for pattern in junk_patterns:
        if pattern in url:
            return True

    # SVG files are usually icons/decorative (not property photos)
    if url.endswith('.svg'):
        return True

    return False


def deduplicate_images(images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate images by normalizing CDN URLs and keeping the highest-resolution
    variant for each unique image.

    Also filters out images that are too small or are junk.

    Args:
        images: List of image dicts

    Returns:
        Deduplicated and filtered list of images
    """
    # Group by normalized URL
    groups: Dict[str, List[Dict[str, Any]]] = {}

    filtered_junk = 0
    filtered_small = 0

    for img in images:
        url = img.get("url", "")
        if not url:
            continue

        # Filter junk images
        if is_junk_image(img):
            filtered_junk += 1
            continue

        # Filter tiny images
        if is_image_too_small(img):
            filtered_small += 1
            continue

        normalized = normalize_image_url(url)
        if normalized not in groups:
            groups[normalized] = []
        groups[normalized].append(img)

    # Pick best resolution from each group
    result = []
    dedup_count = 0
    for normalized_url, variants in groups.items():
        best = get_best_resolution_image(variants)
        result.append(best)
        if len(variants) > 1:
            dedup_count += len(variants) - 1

    if filtered_junk > 0:
        print(f"  Filtered {filtered_junk} junk images (tracking, icons, SVGs)")
    if filtered_small > 0:
        print(f"  Filtered {filtered_small} images below {MIN_IMAGE_WIDTH}x{MIN_IMAGE_HEIGHT}px")
    if dedup_count > 0:
        print(f"  Deduplicated {dedup_count} resolution variants (kept highest-res)")

    return result


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
                    "content": """You are an expert at extracting property photography URLs from HTML content. Your goal is to find HIGH-QUALITY PROPERTY PHOTOS suitable for marketing content generation.

EXTRACTION RULES:
1. For <img> tags with srcset attributes, ONLY return the HIGHEST resolution URL from the srcset. Do NOT return multiple sizes of the same image.
2. For <picture> elements with multiple <source> tags, ONLY return the largest/highest-quality source.
3. SKIP these types of images entirely:
   - Logos, brand marks, and watermarks
   - Icons, social media badges, and navigation UI elements
   - Tracking pixels, spacers, and 1x1 images
   - Decorative textures, patterns, and background overlays
   - Loading spinners and placeholder images
   - SVG files (usually icons/decorative)
   - Images smaller than 200px in either dimension
4. FOCUS on property-related photography: interiors, exteriors, amenities, lifestyle shots, aerial views, floor plans, neighborhood scenes.
5. Return absolute URLs (resolve relative URLs to the page URL provided).
6. Include alt text, width, and height attributes when available in HTML."""
                },
                {
                    "role": "user",
                    "content": f"""Extract property photography URLs from the following HTML content. The page URL is: {page_url}

HTML Content:
{html_content}

Remember:
- Only return the HIGHEST resolution variant when multiple sizes exist (srcset, picture elements)
- Skip logos, icons, SVGs, tracking pixels, decorative textures, and tiny images
- Focus on actual property photographs and floor plans"""
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
            raw_count = len(all_images)
            # Deduplicate resolution variants and filter junk/tiny images
            all_images = deduplicate_images(all_images)
            print(f"  ✓ Firecrawl extraction successful: {len(all_images)} images (from {raw_count} raw)")
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
                
                raw_count = len(images)
                # Deduplicate resolution variants and filter junk/tiny images
                images = deduplicate_images(images)
                print(f"✓ Successfully extracted {len(images)} images using Apify fallback (from {raw_count} raw)")
            
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

