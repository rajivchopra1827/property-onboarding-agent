"""
Agno Tool wrapper for classify_images.

Converts the existing bulk classification tool to an Agno-native Tool.
"""

from agno_tools.tool import Tool
from typing import Optional, Dict, Any
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from tools.bulk_classify_images import execute as bulk_classify_images_execute
from database import PropertyRepository


def classify_images(
    property_id: Optional[str] = None,
    url: Optional[str] = None,
    force_reclassify: bool = False,
    batch_size: int = 5,
    max_images: Optional[int] = None,
) -> dict:
    """
    Classify property images using AI vision to assign tags.
    
    Args:
        property_id: Property ID (UUID) to classify images for
        url: Property website URL (alternative to property_id)
        force_reclassify: If True, re-classify images that already have classifications
        batch_size: Number of images to process per batch (default: 5)
        max_images: Maximum number of images to process (None for all)
        
    Returns:
        Dictionary with classification statistics and results
    """
    arguments = {
        "force_reclassify": force_reclassify,
        "batch_size": batch_size,
    }
    
    if property_id:
        arguments["property_id"] = property_id
    if url:
        arguments["url"] = url
    if max_images:
        arguments["max_images"] = max_images
    
    # Get amenities data for better classification accuracy
    # This is optional - classification works without it, but is more accurate with it
    amenities_data = None
    try:
        repo = PropertyRepository()
        resolved_property_id = property_id
        
        # Resolve property_id from URL if needed
        if url and not property_id:
            property_obj = repo.get_property_by_website_url(url)
            if property_obj and property_obj.id:
                resolved_property_id = property_obj.id
        
        if resolved_property_id:
            amenities = repo.get_property_amenities(resolved_property_id)
            if amenities:
                amenities_data = {
                    "building_amenities": amenities.building_amenities or [],
                    "apartment_amenities": amenities.apartment_amenities or [],
                }
    except Exception as e:
        # Don't fail if we can't get amenities - classification works without it
        print(f"Note: Could not fetch amenities data for context: {e}")
    
    # Note: The bulk_classify_images tool doesn't currently accept amenities_data
    # as a parameter, but the underlying classify_images function does.
    # For now, we'll call it without amenities_data. If needed, we can enhance
    # bulk_classify_images to accept and pass through amenities_data.
    
    return bulk_classify_images_execute(arguments)


# Create Agno Tool
classify_images_tool = Tool(
    name="classify_images",
    description="Classify property images using AI vision to assign tags (exterior, interior, amenities, etc.). Processes images in batches to respect rate limits. Can optionally re-classify existing images.",
    func=classify_images,
)
