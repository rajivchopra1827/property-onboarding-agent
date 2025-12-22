"""
Cache manager for storing and retrieving crawled website data.

Caches raw markdown from crawled pages, keyed by domain name,
with time-based expiration support.

Now uses Supabase database instead of file-based cache.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse
from database import CacheRepository


# Initialize database cache repository
_cache_repo = None
DEFAULT_EXPIRY_HOURS = 24


def _get_cache_repo():
    """Get or create cache repository instance."""
    global _cache_repo
    if _cache_repo is None:
        _cache_repo = CacheRepository(default_expiry_hours=DEFAULT_EXPIRY_HOURS)
    return _cache_repo


def ensure_cache_dir():
    """Ensure the cache directory exists (kept for backward compatibility, but not used)."""
    # This function is kept for backward compatibility but no longer creates directories
    # Cache is now stored in database
    pass


def get_domain_from_url(url):
    """
    Extract domain name from URL.
    
    Args:
        url: Full URL (e.g., "https://www.villasattowngate.com")
        
    Returns:
        Domain name (e.g., "villasattowngate.com")
    """
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split('/')[0]
    # Remove www. prefix if present
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain


def get_cache_path(domain):
    """
    Get the file path for a domain's cache.
    
    DEPRECATED: This function is kept for backward compatibility but no longer used.
    Cache is now stored in database.
    
    Args:
        domain: Domain name (e.g., "villasattowngate.com")
        
    Returns:
        Path object for the cache file (for compatibility only)
    """
    # Return a dummy path for backward compatibility
    return Path(f"/tmp/{domain}.json")


def get_images_cache_path(domain):
    """
    Get the file path for a domain's images cache.
    
    DEPRECATED: This function is kept for backward compatibility but no longer used.
    Cache is now stored in database.
    
    Args:
        domain: Domain name (e.g., "villasattowngate.com")
        
    Returns:
        Path object for the images cache file (for compatibility only)
    """
    # Return a dummy path for backward compatibility
    return Path(f"/tmp/{domain}_images.json")


def load_cache(domain):
    """
    Load cached data for a domain from database.
    
    Args:
        domain: Domain name
        
    Returns:
        Dictionary with cache data, or None if cache doesn't exist
    """
    try:
        cache_repo = _get_cache_repo()
        cache_data = cache_repo.get_cache(domain, "markdown")
        return cache_data
    except Exception as e:
        print(f"Error loading cache for {domain}: {e}")
        return None


def save_cache(domain, pages_data, expiry_hours=DEFAULT_EXPIRY_HOURS):
    """
    Save crawled data to cache in database.
    
    Args:
        domain: Domain name
        pages_data: List of dictionaries with 'url', 'markdown', and optionally 'images' keys
        expiry_hours: Hours until cache expires (default: 24)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cache_repo = _get_cache_repo()
        
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=expiry_hours)
        
        # Calculate total characters
        total_chars = sum(len(page.get('markdown', '')) for page in pages_data)
        
        # Build pages with images if available
        pages_list = []
        for page in pages_data:
            page_entry = {
                "url": page.get("url", ""),
                "markdown": page.get("markdown", ""),
                "crawled_at": now.isoformat() + "Z"
            }
            # Add images if present
            if "images" in page:
                page_entry["images"] = page.get("images", [])
            pages_list.append(page_entry)
        
        cache_data = {
            "domain": domain,
            "crawled_at": now.isoformat() + "Z",
            "expires_at": expires_at.isoformat() + "Z",
            "pages": pages_list,
            "total_pages": len(pages_data),
            "total_chars": total_chars
        }
        
        return cache_repo.save_cache(domain, cache_data, "markdown", expiry_hours)
    except Exception as e:
        print(f"Error saving cache for {domain}: {e}")
        return False


def is_cache_valid(domain):
    """
    Check if cache exists and hasn't expired.
    
    Args:
        domain: Domain name
        
    Returns:
        True if cache exists and is valid, False otherwise
    """
    try:
        cache_repo = _get_cache_repo()
        return cache_repo.is_cache_valid(domain, "markdown")
    except Exception as e:
        print(f"Error checking cache validity for {domain}: {e}")
        return False


def get_cache_age(domain):
    """
    Get the age of cache in hours.
    
    Args:
        domain: Domain name
        
    Returns:
        Age in hours (float), or None if cache doesn't exist
    """
    try:
        cache_repo = _get_cache_repo()
        return cache_repo.get_cache_age(domain, "markdown")
    except Exception as e:
        print(f"Error getting cache age for {domain}: {e}")
        return None


def clear_cache(domain):
    """
    Delete cache for a domain from database.
    
    Args:
        domain: Domain name
        
    Returns:
        True if deleted, False if cache didn't exist
    """
    try:
        cache_repo = _get_cache_repo()
        return cache_repo.clear_cache(domain, "markdown")
    except Exception as e:
        print(f"Error clearing cache for {domain}: {e}")
        return False


def get_cached_markdown(domain):
    """
    Get combined markdown from cached pages.
    
    Args:
        domain: Domain name
        
    Returns:
        Combined markdown string with page separators, or None if cache invalid
    """
    try:
        cache_repo = _get_cache_repo()
        return cache_repo.get_cached_markdown(domain)
    except Exception as e:
        print(f"Error getting cached markdown for {domain}: {e}")
        return None


def get_cached_images(domain):
    """
    Get all images from cached pages.
    
    Args:
        domain: Domain name
        
    Returns:
        List of image dictionaries with url, alt, width, height, page_url, or None if cache invalid
    """
    try:
        cache_repo = _get_cache_repo()
        cache_data = cache_repo.get_cache(domain, "markdown")
        if cache_data is None:
            return None
        
        pages = cache_data.get("pages", [])
        if not pages:
            return None
        
        # Collect all images from all pages
        all_images = []
        for page in pages:
            page_url = page.get("url", "")
            images = page.get("images", [])
            # Ensure each image has page_url
            for image in images:
                if isinstance(image, dict):
                    image_with_page = image.copy()
                    image_with_page["page_url"] = page_url
                    all_images.append(image_with_page)
        
        return all_images
    except Exception as e:
        print(f"Error getting cached images for {domain}: {e}")
        return None


def save_images_cache(domain, images, expiry_hours=DEFAULT_EXPIRY_HOURS):
    """
    Save images to cache in database.
    
    Args:
        domain: Domain name
        images: List of image dictionaries with url, page_url, etc.
        expiry_hours: Hours until cache expires (default: 24)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cache_repo = _get_cache_repo()
        
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=expiry_hours)
        
        cache_data = {
            "domain": domain,
            "crawled_at": now.isoformat() + "Z",
            "expires_at": expires_at.isoformat() + "Z",
            "images": images,
            "total_images": len(images)
        }
        
        return cache_repo.save_cache(domain, cache_data, "images", expiry_hours)
    except Exception as e:
        print(f"Error saving images cache for {domain}: {e}")
        return False


def is_images_cache_valid(domain):
    """
    Check if images cache exists and hasn't expired.
    
    Args:
        domain: Domain name
        
    Returns:
        True if cache exists and is valid, False otherwise
    """
    try:
        cache_repo = _get_cache_repo()
        return cache_repo.is_cache_valid(domain, "images")
    except Exception as e:
        print(f"Error checking images cache validity for {domain}: {e}")
        return False


def get_images_cache_age(domain):
    """
    Get the age of images cache in hours.
    
    Args:
        domain: Domain name
        
    Returns:
        Age in hours (float), or None if cache doesn't exist
    """
    try:
        cache_repo = _get_cache_repo()
        return cache_repo.get_cache_age(domain, "images")
    except Exception as e:
        print(f"Error getting images cache age for {domain}: {e}")
        return None


def get_cached_images_from_cache(domain):
    """
    Get all images from images cache in database.
    
    Args:
        domain: Domain name
        
    Returns:
        List of image dictionaries, or None if cache invalid or doesn't exist
    """
    try:
        cache_repo = _get_cache_repo()
        return cache_repo.get_cached_images(domain)
    except Exception as e:
        print(f"Error getting cached images from cache for {domain}: {e}")
        return None


def save_branding_cache(domain, branding_data, expiry_hours=DEFAULT_EXPIRY_HOURS):
    """
    Save branding data to cache in database.
    
    Args:
        domain: Domain name
        branding_data: Dictionary containing branding information from Firecrawl
        expiry_hours: Hours until cache expires (default: 24)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cache_repo = _get_cache_repo()
        
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=expiry_hours)
        
        cache_data = {
            "domain": domain,
            "crawled_at": now.isoformat() + "Z",
            "expires_at": expires_at.isoformat() + "Z",
            "branding_data": branding_data
        }
        
        return cache_repo.save_cache(domain, cache_data, "branding", expiry_hours)
    except Exception as e:
        print(f"Error saving branding cache for {domain}: {e}")
        return False


def is_branding_cache_valid(domain):
    """
    Check if branding cache exists and hasn't expired.
    
    Args:
        domain: Domain name
        
    Returns:
        True if cache exists and is valid, False otherwise
    """
    try:
        cache_repo = _get_cache_repo()
        return cache_repo.is_cache_valid(domain, "branding")
    except Exception as e:
        print(f"Error checking branding cache validity for {domain}: {e}")
        return False


def get_branding_cache_age(domain):
    """
    Get the age of branding cache in hours.
    
    Args:
        domain: Domain name
        
    Returns:
        Age in hours (float), or None if cache doesn't exist
    """
    try:
        cache_repo = _get_cache_repo()
        return cache_repo.get_cache_age(domain, "branding")
    except Exception as e:
        print(f"Error getting branding cache age for {domain}: {e}")
        return None


def get_cached_branding_from_cache(domain):
    """
    Get branding data from branding cache in database.
    
    Args:
        domain: Domain name
        
    Returns:
        Dictionary containing branding data, or None if cache invalid or doesn't exist
    """
    try:
        cache_repo = _get_cache_repo()
        cache_data = cache_repo.get_cache(domain, "branding")
        if cache_data is None:
            return None
        
        return cache_data.get("branding_data")
    except Exception as e:
        print(f"Error getting cached branding from cache for {domain}: {e}")
        return None


def save_html_cache(domain, html_pages, expiry_hours=DEFAULT_EXPIRY_HOURS):
    """
    Save HTML pages to cache in database.
    
    Args:
        domain: Domain name
        html_pages: List of dictionaries with 'url' and 'html' keys
        expiry_hours: Hours until cache expires (default: 24)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cache_repo = _get_cache_repo()
        
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=expiry_hours)
        
        # Calculate total characters
        total_chars = sum(len(page.get('html', '')) for page in html_pages)
        
        # Build pages list
        pages_list = []
        for page in html_pages:
            page_entry = {
                "url": page.get("url", ""),
                "html": page.get("html", ""),
                "crawled_at": now.isoformat() + "Z"
            }
            pages_list.append(page_entry)
        
        cache_data = {
            "domain": domain,
            "crawled_at": now.isoformat() + "Z",
            "expires_at": expires_at.isoformat() + "Z",
            "pages": pages_list,
            "total_pages": len(html_pages),
            "total_chars": total_chars
        }
        
        return cache_repo.save_cache(domain, cache_data, "html", expiry_hours)
    except Exception as e:
        print(f"Error saving HTML cache for {domain}: {e}")
        return False


def get_cached_html(domain):
    """
    Get cached HTML pages from database.
    
    Args:
        domain: Domain name
        
    Returns:
        List of dictionaries with 'url' and 'html' keys, or None if cache invalid
    """
    try:
        cache_repo = _get_cache_repo()
        cache_data = cache_repo.get_cache(domain, "html")
        if cache_data is None:
            return None
        
        pages = cache_data.get("pages", [])
        if not pages:
            return None
        
        return pages
    except Exception as e:
        print(f"Error getting cached HTML for {domain}: {e}")
        return None


def is_html_cache_valid(domain):
    """
    Check if HTML cache exists and hasn't expired.
    
    Args:
        domain: Domain name
        
    Returns:
        True if cache exists and is valid, False otherwise
    """
    try:
        cache_repo = _get_cache_repo()
        return cache_repo.is_cache_valid(domain, "html")
    except Exception as e:
        print(f"Error checking HTML cache validity for {domain}: {e}")
        return False


def get_html_cache_age(domain):
    """
    Get the age of HTML cache in hours.
    
    Args:
        domain: Domain name
        
    Returns:
        Age in hours (float), or None if cache doesn't exist
    """
    try:
        cache_repo = _get_cache_repo()
        return cache_repo.get_cache_age(domain, "html")
    except Exception as e:
        print(f"Error getting HTML cache age for {domain}: {e}")
        return None

