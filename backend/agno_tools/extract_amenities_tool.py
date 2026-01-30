"""
Agno Tool wrapper for extract_amenities.

Converts the existing extraction tool to an Agno-native Tool.
"""

from agno_tools.tool import Tool
from typing import Optional
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from tools.extract_amenities import execute as extract_amenities_execute


def extract_amenities(
    url: Optional[str] = None,
    markdown: Optional[str] = None,
    use_cache: Optional[bool] = None,
    force_refresh: bool = False,
) -> dict:
    """
    Extract amenities information from a property website.
    
    Args:
        url: The URL of the property website (will crawl if provided)
        markdown: Raw markdown content (use if already crawled)
        use_cache: Whether to use cached markdown
        force_refresh: Force fresh crawl even if cache exists
        
    Returns:
        Dictionary with building_amenities and apartment_amenities
    """
    arguments = {}
    if url:
        arguments["url"] = url
    if markdown:
        arguments["markdown"] = markdown
    if use_cache is not None:
        arguments["use_cache"] = use_cache
    if force_refresh:
        arguments["force_refresh"] = force_refresh
    
    return extract_amenities_execute(arguments)


# Create Agno Tool
extract_amenities_tool = Tool(
    name="extract_amenities",
    description="Extract amenities information from a property website. Returns building amenities (pool, gym, etc.) and apartment amenities (appliances, features, etc.).",
    func=extract_amenities,
)
