"""
Agno Tool wrapper for extract_floor_plans.

Converts the existing extraction tool to an Agno-native Tool.
"""

from agno_tools.tool import Tool
from typing import Optional
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from tools.extract_floor_plans import execute as extract_floor_plans_execute


def extract_floor_plans(
    url: Optional[str] = None,
    markdown: Optional[str] = None,
    use_cache: Optional[bool] = None,
    force_refresh: bool = False,
) -> dict:
    """
    Extract floor plan information from a property website.
    
    Args:
        url: The URL of the property website (will crawl if provided)
        markdown: Raw markdown content (use if already crawled)
        use_cache: Whether to use cached markdown
        force_refresh: Force fresh crawl even if cache exists
        
    Returns:
        Dictionary with floor_plans list
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
    
    return extract_floor_plans_execute(arguments)


# Create Agno Tool
extract_floor_plans_tool = Tool(
    name="extract_floor_plans",
    description="Extract floor plan information from a property website. Returns floor plan details including name, size, bedrooms, bathrooms, prices, and availability.",
    func=extract_floor_plans,
)
