"""
Agno Tool wrapper for find_competitors.

Converts the existing extraction tool to an Agno-native Tool.
"""

from agno_tools.tool import Tool
from typing import Optional, List
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from tools.find_competitors import execute as find_competitors_execute


def find_competitors(
    property_id: Optional[str] = None,
    property_name: Optional[str] = None,
    radius_miles: float = 10,
    search_terms: Optional[List[str]] = None,
    max_results: int = 10,
) -> dict:
    """
    Find nearby luxury apartment competitors for a property.
    
    Args:
        property_id: Property ID (preferred if available)
        property_name: Property name (will look up in database)
        radius_miles: Search radius in miles
        search_terms: List of search terms for Google Maps
        max_results: Max results per search term
        
    Returns:
        Dictionary with competitor count and summary
    """
    arguments = {
        "radius_miles": radius_miles,
        "max_results": max_results,
    }
    if property_id:
        arguments["property_id"] = property_id
    if property_name:
        arguments["property_name"] = property_name
    if search_terms:
        arguments["search_terms"] = search_terms
    
    return find_competitors_execute(arguments)


# Create Agno Tool
find_competitors_tool = Tool(
    name="find_competitors",
    description="Find nearby luxury apartment competitors for a property using Google Maps. Requires property to exist in database with address (needs property_info extracted first).",
    func=find_competitors,
)
