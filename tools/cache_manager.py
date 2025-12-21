"""
Cache manager for storing and retrieving crawled website data.

Caches raw markdown from crawled pages, keyed by domain name,
with time-based expiration support.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse


CACHE_DIR = Path(__file__).parent.parent / "cache"
DEFAULT_EXPIRY_HOURS = 24


def ensure_cache_dir():
    """Ensure the cache directory exists."""
    CACHE_DIR.mkdir(exist_ok=True)


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
    
    Args:
        domain: Domain name (e.g., "villasattowngate.com")
        
    Returns:
        Path object for the cache file
    """
    ensure_cache_dir()
    # Sanitize domain name for filename (replace dots and special chars)
    safe_domain = domain.replace('.', '_').replace('/', '_').replace('\\', '_')
    return CACHE_DIR / f"{safe_domain}.json"


def load_cache(domain):
    """
    Load cached data for a domain.
    
    Args:
        domain: Domain name
        
    Returns:
        Dictionary with cache data, or None if cache doesn't exist
    """
    cache_path = get_cache_path(domain)
    
    if not cache_path.exists():
        return None
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        return cache_data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading cache for {domain}: {e}")
        return None


def save_cache(domain, pages_data, expiry_hours=DEFAULT_EXPIRY_HOURS):
    """
    Save crawled data to cache.
    
    Args:
        domain: Domain name
        pages_data: List of dictionaries with 'url' and 'markdown' keys
        expiry_hours: Hours until cache expires (default: 24)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        ensure_cache_dir()
        cache_path = get_cache_path(domain)
        
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=expiry_hours)
        
        # Calculate total characters
        total_chars = sum(len(page.get('markdown', '')) for page in pages_data)
        
        cache_data = {
            "domain": domain,
            "crawled_at": now.isoformat() + "Z",
            "expires_at": expires_at.isoformat() + "Z",
            "pages": [
                {
                    "url": page.get("url", ""),
                    "markdown": page.get("markdown", ""),
                    "crawled_at": now.isoformat() + "Z"
                }
                for page in pages_data
            ],
            "total_pages": len(pages_data),
            "total_chars": total_chars
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        return True
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
    cache_data = load_cache(domain)
    
    if cache_data is None:
        return False
    
    # Check expiration
    expires_at_str = cache_data.get("expires_at")
    if not expires_at_str:
        return False
    
    try:
        expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
        now = datetime.utcnow().replace(tzinfo=expires_at.tzinfo)
        return now < expires_at
    except (ValueError, AttributeError):
        return False


def get_cache_age(domain):
    """
    Get the age of cache in hours.
    
    Args:
        domain: Domain name
        
    Returns:
        Age in hours (float), or None if cache doesn't exist
    """
    cache_data = load_cache(domain)
    
    if cache_data is None:
        return None
    
    crawled_at_str = cache_data.get("crawled_at")
    if not crawled_at_str:
        return None
    
    try:
        crawled_at = datetime.fromisoformat(crawled_at_str.replace('Z', '+00:00'))
        now = datetime.utcnow().replace(tzinfo=crawled_at.tzinfo)
        age = (now - crawled_at).total_seconds() / 3600  # Convert to hours
        return age
    except (ValueError, AttributeError):
        return None


def clear_cache(domain):
    """
    Delete cache for a domain.
    
    Args:
        domain: Domain name
        
    Returns:
        True if deleted, False if cache didn't exist
    """
    cache_path = get_cache_path(domain)
    
    if cache_path.exists():
        try:
            cache_path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting cache for {domain}: {e}")
            return False
    
    return False


def get_cached_markdown(domain):
    """
    Get combined markdown from cached pages.
    
    Args:
        domain: Domain name
        
    Returns:
        Combined markdown string with page separators, or None if cache invalid
    """
    if not is_cache_valid(domain):
        return None
    
    cache_data = load_cache(domain)
    if cache_data is None:
        return None
    
    pages = cache_data.get("pages", [])
    if not pages:
        return None
    
    # Combine markdown from all pages with separators
    markdown_parts = [page.get("markdown", "") for page in pages if page.get("markdown")]
    return "\n\n---PAGE BREAK---\n\n".join(markdown_parts)

