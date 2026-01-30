"""
Utility functions for property onboarding workflows.

Contains shared utilities extracted from the old onboard_property tool.
"""

from typing import Optional, List
from database import PropertyRepository

# Default extraction order - property info should come first as it creates the property record
DEFAULT_EXTRACTIONS = [
    "property_info",
    "images",
    "brand_identity",
    "amenities",
    "floor_plans",
    "special_offers",
    "reviews",
    "competitors"
]


def get_missing_extractions(property_id: Optional[str] = None, url: Optional[str] = None) -> List[str]:
    """
    Check what data already exists for a property and return missing extraction types.
    
    This function checks the database to see which extraction types have already been
    completed for a property, and returns a list of extraction types that still need
    to be run. This is useful for resuming a partial onboarding.
    
    Args:
        property_id: Property ID (if known). If not provided, will try to find property by URL.
        url: Website URL of the property. Required if property_id is not provided.
        
    Returns:
        List of extraction type strings that are missing (e.g., ["reviews", "competitors"])
        Returns all DEFAULT_EXTRACTIONS if property not found.
        
    Example:
        # Check what's missing for a property
        missing = get_missing_extractions(url="https://example.com")
        if missing:
            # Resume onboarding with only missing extractions
            # Use FastAPI endpoint or workflow with specific extractions
    """
    repo = PropertyRepository()
    property_obj = None
    
    # Try to get property by ID or URL
    if property_id:
        property_obj = repo.get_property_by_id(property_id)
    elif url:
        property_obj = repo.get_property_by_website_url(url)
    
    # If property doesn't exist, return all extractions
    if not property_obj or not property_obj.id:
        return DEFAULT_EXTRACTIONS.copy()
    
    missing = []
    prop_id = property_obj.id
    
    # Check each extraction type (skip property_info as it's required and should already exist)
    # Check images
    images = repo.get_property_images(prop_id)
    if not images or len(images) == 0:
        missing.append("images")
    
    # Check brand identity
    branding = repo.get_branding_by_property_id(prop_id)
    if not branding:
        missing.append("brand_identity")
    
    # Check amenities
    amenities = repo.get_amenities_by_property_id(prop_id)
    if not amenities:
        missing.append("amenities")
    
    # Check floor plans
    floor_plans = repo.get_floor_plans_by_property_id(prop_id)
    if not floor_plans or len(floor_plans) == 0:
        missing.append("floor_plans")
    
    # Check special offers
    special_offers = repo.get_special_offers_by_property_id(prop_id)
    if not special_offers or len(special_offers) == 0:
        missing.append("special_offers")
    
    # Check reviews (check both summary and individual reviews)
    reviews_summary = repo.get_reviews_summary_by_property_id(prop_id)
    reviews = repo.get_reviews_by_property_id(prop_id, limit=1)  # Just check if any exist
    if not reviews_summary and (not reviews or len(reviews) == 0):
        missing.append("reviews")
    
    # Check competitors
    competitors = repo.get_competitors_by_property_id(prop_id)
    if not competitors or len(competitors) == 0:
        missing.append("competitors")
    
    # Return missing extractions in the correct order (matching DEFAULT_EXTRACTIONS order)
    ordered_missing = [ext for ext in DEFAULT_EXTRACTIONS if ext in missing]
    
    return ordered_missing
