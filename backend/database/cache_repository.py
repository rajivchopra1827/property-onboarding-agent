"""
Repository for cache-related database operations.

Handles database-based caching to replace file-based cache system.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from .supabase_client import get_supabase_client


class CacheRepository:
    """Repository for managing cache entries in the database."""
    
    def __init__(self, default_expiry_hours: int = 24):
        """
        Initialize cache repository.
        
        Args:
            default_expiry_hours: Default cache expiry time in hours
        """
        self.client = get_supabase_client()
        self.default_expiry_hours = default_expiry_hours
    
    def get_cache(self, domain: str, content_type: str = "markdown") -> Optional[Dict[str, Any]]:
        """
        Get cached data for a domain and content type.
        
        Args:
            domain: Domain name (e.g., "example.com")
            content_type: Type of cached content ('markdown', 'images', etc.)
            
        Returns:
            Dictionary with cache data, or None if cache doesn't exist
        """
        try:
            response = (
                self.client.table("cache_entries")
                .select("*")
                .eq("domain", domain)
                .eq("content_type", content_type)
                .execute()
            )
            
            if response.data and len(response.data) > 0:
                cache_entry = response.data[0]
                cached_data = cache_entry.get("cached_data", {})
                
                # Add metadata from cache entry
                cached_data["_cache_metadata"] = {
                    "created_at": cache_entry.get("created_at"),
                    "updated_at": cache_entry.get("updated_at")
                }
                
                return cached_data
            return None
        except Exception as e:
            print(f"Error getting cache for {domain}: {e}")
            return None
    
    def save_cache(
        self,
        domain: str,
        cached_data: Dict[str, Any],
        content_type: str = "markdown",
        expiry_hours: Optional[int] = None
    ) -> bool:
        """
        Save data to cache.
        
        Args:
            domain: Domain name (e.g., "example.com")
            cached_data: Data to cache (will be stored as JSONB)
            content_type: Type of cached content ('markdown', 'images', etc.)
            expiry_hours: Hours until cache expires (uses default if None)
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            expiry = expiry_hours if expiry_hours is not None else self.default_expiry_hours
            
            # Add expiry information to cached_data
            now = datetime.utcnow()
            expires_at = now + timedelta(hours=expiry)
            
            cache_entry = {
                "domain": domain,
                "content_type": content_type,
                "cached_data": cached_data
            }
            
            # Use upsert to update if exists, insert if not
            response = (
                self.client.table("cache_entries")
                .upsert(cache_entry, on_conflict="domain,content_type")
                .execute()
            )
            
            return response.data is not None
        except Exception as e:
            print(f"Error saving cache for {domain}: {e}")
            return False
    
    def is_cache_valid(self, domain: str, content_type: str = "markdown") -> bool:
        """
        Check if cache exists and is valid (not expired).
        
        Args:
            domain: Domain name
            content_type: Type of cached content
            
        Returns:
            True if cache exists and is valid, False otherwise
        """
        cache_data = self.get_cache(domain, content_type)
        if cache_data is None:
            return False
        
        # Check if cache has expiry information
        metadata = cache_data.get("_cache_metadata", {})
        created_at_str = metadata.get("created_at")
        
        if not created_at_str:
            # If no expiry info, assume cache is valid if it exists
            return True
        
        # Check expiration based on created_at and expiry_hours
        try:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            expires_at = created_at + timedelta(hours=self.default_expiry_hours)
            now = datetime.utcnow().replace(tzinfo=created_at.tzinfo)
            return now < expires_at
        except (ValueError, AttributeError):
            # If we can't parse the date, assume cache is valid
            return True
    
    def get_cache_age(self, domain: str, content_type: str = "markdown") -> Optional[float]:
        """
        Get the age of cache in hours.
        
        Args:
            domain: Domain name
            content_type: Type of cached content
            
        Returns:
            Age in hours (float), or None if cache doesn't exist
        """
        cache_data = self.get_cache(domain, content_type)
        if cache_data is None:
            return None
        
        metadata = cache_data.get("_cache_metadata", {})
        created_at_str = metadata.get("created_at")
        
        if not created_at_str:
            return None
        
        try:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            now = datetime.utcnow().replace(tzinfo=created_at.tzinfo)
            age = (now - created_at).total_seconds() / 3600  # Convert to hours
            return age
        except (ValueError, AttributeError):
            return None
    
    def clear_cache(self, domain: str, content_type: Optional[str] = None) -> bool:
        """
        Delete cache for a domain.
        
        Args:
            domain: Domain name
            content_type: Type of cached content (if None, deletes all types for domain)
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            query = self.client.table("cache_entries").delete().eq("domain", domain)
            
            if content_type:
                query = query.eq("content_type", content_type)
            
            response = query.execute()
            return True
        except Exception as e:
            print(f"Error clearing cache for {domain}: {e}")
            return False
    
    def get_cached_markdown(self, domain: str) -> Optional[str]:
        """
        Get combined markdown from cached pages.
        
        Args:
            domain: Domain name
            
        Returns:
            Combined markdown string with page separators, or None if cache invalid
        """
        cache_data = self.get_cache(domain, "markdown")
        if cache_data is None:
            return None
        
        # Extract pages from cached_data
        pages = cache_data.get("pages", [])
        if not pages:
            return None
        
        # Combine markdown from all pages with separators
        markdown_parts = [page.get("markdown", "") for page in pages if page.get("markdown")]
        return "\n\n---PAGE BREAK---\n\n".join(markdown_parts)
    
    def get_cached_images(self, domain: str) -> Optional[list]:
        """
        Get all images from cached data.
        
        Args:
            domain: Domain name
            
        Returns:
            List of image dictionaries, or None if cache invalid
        """
        cache_data = self.get_cache(domain, "images")
        if cache_data is None:
            return None
        
        return cache_data.get("images", [])

