"""
Agno Tool wrapper for extract_special_offers.

Converts the existing extraction tool to an Agno-native Tool.
"""

from agno_tools.tool import Tool
from typing import Optional
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from tools.extract_special_offers import execute as extract_special_offers_execute


def extract_special_offers(
    url: Optional[str] = None,
    markdown: Optional[str] = None,
    use_cache: Optional[bool] = None,
    force_refresh: bool = False,
) -> dict:
    """
    Extract special offers and promotions from a property website.
    
    Args:
        url: The URL of the property website (will crawl if provided)
        markdown: Raw markdown content (use if already crawled)
        use_cache: Whether to use cached markdown
        force_refresh: Force fresh crawl even if cache exists
        
    Returns:
        Dictionary with offers list
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
    
    return extract_special_offers_execute(arguments)


# Create Agno Tool
extract_special_offers_tool = Tool(
    name="extract_special_offers",
    description="Extract special offers and promotions from a property website. Returns offer descriptions, validity dates, and descriptive text.",
    func=extract_special_offers,
)
