"""
Agno Tool wrapper for extract_reviews.

Converts the existing extraction tool to an Agno-native Tool.
"""

from agno_tools.tool import Tool
from typing import Optional
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from tools.extract_reviews import execute as extract_reviews_execute


def extract_reviews(
    property_id: Optional[str] = None,
    url: Optional[str] = None,
    google_maps_url: Optional[str] = None,
    max_reviews: int = 100,
    use_cache: Optional[bool] = None,
    force_refresh: bool = False,
) -> dict:
    """
    Extract reviews from Google Maps for a property.
    
    Args:
        property_id: Property ID (preferred if available)
        url: Property website URL (will look up property)
        google_maps_url: Direct Google Maps URL/Place ID
        max_reviews: Maximum number of reviews to extract
        use_cache: Whether to use cached data
        force_refresh: Force fresh scrape
        
    Returns:
        Dictionary with reviews summary and count
    """
    arguments = {
        "max_reviews": max_reviews,
    }
    if property_id:
        arguments["property_id"] = property_id
    if url:
        arguments["url"] = url
    if google_maps_url:
        arguments["google_maps_url"] = google_maps_url
    if use_cache is not None:
        arguments["use_cache"] = use_cache
    if force_refresh:
        arguments["force_refresh"] = force_refresh
    
    return extract_reviews_execute(arguments)


# Create Agno Tool
extract_reviews_tool = Tool(
    name="extract_reviews",
    description="Extract reviews from Google Maps for a property. Requires property to exist in database (needs property_info extracted first).",
    func=extract_reviews,
)
