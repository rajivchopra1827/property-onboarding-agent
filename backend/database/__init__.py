"""
Database module for FionaFast.

Provides database access through Supabase for storing properties, images, and cache entries.
"""

from .supabase_client import get_supabase_client
from .property_repository import PropertyRepository
from .cache_repository import CacheRepository
from .models import Property, PropertyImage, PropertyBranding, Competitor, PropertySocialPost

__all__ = [
    "get_supabase_client",
    "PropertyRepository",
    "CacheRepository",
    "Property",
    "PropertyImage",
    "PropertyBranding",
    "Competitor",
    "PropertySocialPost",
]

