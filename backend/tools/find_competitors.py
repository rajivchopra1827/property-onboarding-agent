"""
Tool for finding nearby luxury apartment competitors for a property.

Uses Apify Google Maps Scraper Actor to search for competitors within a specified radius.
Stores competitor information in the database.
"""

import os
import math
from typing import List, Optional
from datetime import datetime
from apify_client import ApifyClient
from database import PropertyRepository, Competitor
from utils.geocoding import geocode_address


def get_apify_client():
    """Initialize and return Apify client with API token from environment."""
    token = os.getenv("APIFY_API_TOKEN")
    if not token:
        raise ValueError(
            "APIFY_API_TOKEN not found. Please set it in your environment variables."
        )
    return ApifyClient(token=token)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth using Haversine formula.
    
    Args:
        lat1, lon1: Latitude and longitude of first point in decimal degrees
        lat2, lon2: Latitude and longitude of second point in decimal degrees
        
    Returns:
        Distance in miles
    """
    # Radius of Earth in miles
    R = 3959.0
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance


def is_same_property(property_name: str, property_address: str, competitor_name: str, competitor_address: str) -> bool:
    """
    Check if competitor is actually the same as the target property.
    
    Args:
        property_name: Name of target property
        property_address: Address of target property
        competitor_name: Name of competitor
        competitor_address: Address of competitor
        
    Returns:
        True if they appear to be the same property
    """
    # Normalize strings for comparison
    prop_name_norm = property_name.lower().strip() if property_name else ""
    comp_name_norm = competitor_name.lower().strip() if competitor_name else ""
    prop_addr_norm = property_address.lower().strip() if property_address else ""
    comp_addr_norm = competitor_address.lower().strip() if competitor_address else ""
    
    # Check if names are very similar (allowing for minor variations)
    if prop_name_norm and comp_name_norm:
        # Remove common words and compare
        common_words = {"apartments", "apartment", "apartments", "complex", "community", "residence", "residences", "the"}
        prop_words = set(prop_name_norm.split()) - common_words
        comp_words = set(comp_name_norm.split()) - common_words
        
        if prop_words and comp_words and prop_words == comp_words:
            return True
    
    # Check if addresses match (allowing for minor variations)
    if prop_addr_norm and comp_addr_norm:
        # Extract street number and name
        prop_street = prop_addr_norm.split(",")[0].strip() if "," in prop_addr_norm else prop_addr_norm
        comp_street = comp_addr_norm.split(",")[0].strip() if "," in comp_addr_norm else comp_addr_norm
        
        if prop_street == comp_street:
            return True
    
    return False


def transform_competitor_data(
    apify_result: dict,
    target_property_name: str,
    target_property_address: str,
    target_lat: float,
    target_lon: float
) -> Optional[Competitor]:
    """
    Transform Apify Actor output format to our Competitor format.
    
    Args:
        apify_result: Dictionary from Apify Actor with place data
        target_property_name: Name of target property (to filter out)
        target_property_address: Address of target property (to filter out)
        target_lat: Latitude of target property
        target_lon: Longitude of target property
        
    Returns:
        Competitor instance if valid, None if should be filtered out
    """
    competitor_name = (apify_result.get("title") or "").strip()
    competitor_address = (apify_result.get("address") or "").strip()
    
    # Filter out the target property itself
    if is_same_property(target_property_name, target_property_address, competitor_name, competitor_address):
        return None
    
    # Extract location coordinates
    location = apify_result.get("location", {})
    lat = location.get("lat") if location else None
    lon = location.get("lng") if location else None
    
    # Calculate distance if we have coordinates
    distance_miles = None
    if lat and lon and target_lat and target_lon:
        distance_miles = haversine_distance(target_lat, target_lon, lat, lon)
    
    # Extract address components
    street_address = apify_result.get("street")
    city = apify_result.get("city")
    state = apify_result.get("state")
    zip_code = apify_result.get("postalCode")
    
    # Build full address if not provided
    if not competitor_address and (street_address or city or state):
        address_parts = []
        if street_address:
            address_parts.append(street_address)
        if city:
            address_parts.append(city)
        if state:
            address_parts.append(state)
        if zip_code:
            address_parts.append(zip_code)
        competitor_address = ", ".join(address_parts) if address_parts else None
    
    return Competitor(
        property_id="",  # Will be set by caller
        competitor_name=competitor_name,
        address=competitor_address,
        street_address=street_address,
        city=city,
        state=state,
        zip_code=zip_code,
        phone=apify_result.get("phone"),
        website=apify_result.get("website"),
        google_maps_url=apify_result.get("url"),
        place_id=apify_result.get("placeId"),
        rating=apify_result.get("totalScore"),
        review_count=apify_result.get("reviewsCount"),
        latitude=lat,
        longitude=lon,
        distance_miles=distance_miles,
        scraped_at=datetime.now()
    )


def get_tool_definition():
    """Returns the tool definition for OpenAI function calling."""
    return {
        "type": "function",
        "function": {
            "name": "find_competitors",
            "description": "Find nearby luxury apartment competitors for a property using Google Maps. Geocodes the property address, searches for luxury apartments within a configurable radius (default 10 miles), and stores competitor information in the database. Can accept either property_id or property_name - if property_name is provided, will look up the property in the database automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "string",
                        "description": "Property ID to find competitors for. Either property_id or property_name must be provided."
                    },
                    "property_name": {
                        "type": "string",
                        "description": "Property name to find competitors for (e.g., 'Villas at Towngate'). Will look up property in database if property_id is not provided. Either property_id or property_name must be provided."
                    },
                    "radius_miles": {
                        "type": "number",
                        "description": "Search radius in miles. Defaults to 10 miles.",
                        "default": 10
                    },
                    "search_terms": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Search terms to use. Defaults to ['luxury apartments', 'luxury apartment complex'].",
                        "default": ["luxury apartments", "luxury apartment complex"]
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of competitors to find per search term. Defaults to 10.",
                        "default": 10
                    }
                },
                "required": []
            }
        }
    }


def execute(arguments):
    """
    Execute the find_competitors tool.
    
    Finds nearby luxury apartment competitors for a property using Google Maps.
    
    Args:
        arguments: Dictionary containing tool arguments
            - property_id (str, optional): Property ID to find competitors for
            - property_name (str, optional): Property name to find competitors for (will look up in database)
            - radius_miles (float, optional): Search radius in miles (default: 10)
            - search_terms (list, optional): Search terms (default: ["luxury apartments", "luxury apartment complex"])
            - max_results (int, optional): Max results per search term (default: 10)
            
    Returns:
        Dictionary with competitor count and summary
    """
    property_id = arguments.get("property_id")
    property_name = arguments.get("property_name")
    radius_miles = arguments.get("radius_miles", 10)
    search_terms = arguments.get("search_terms", ["luxury apartments", "luxury apartment complex"])
    max_results = arguments.get("max_results", 10)
    
    # Validate that at least one identifier is provided
    if not property_id and not property_name:
        return {
            "error": "Either property_id or property_name must be provided",
            "competitors_found": 0,
            "competitors_added": 0
        }
    
    # Get property from database
    property_repo = PropertyRepository()
    property_obj = None
    
    if property_id:
        # Try to get by ID first
        property_obj = property_repo.get_property_by_id(property_id)
        if not property_obj:
            return {
                "error": f"Property with ID {property_id} not found",
                "competitors_found": 0,
                "competitors_added": 0
            }
    elif property_name:
        # Look up by name
        print(f"Looking up property '{property_name}' in database...")
        property_obj = property_repo.get_property_by_name(property_name)
        if not property_obj:
            return {
                "error": f"Property '{property_name}' not found in database. Please extract property information first using extract_property_information tool.",
                "competitors_found": 0,
                "competitors_added": 0
            }
        property_id = property_obj.id
        print(f"✓ Found property: {property_obj.property_name} (ID: {property_id})")
    
    if not property_obj:
        return {
            "error": "Could not find property",
            "competitors_found": 0,
            "competitors_added": 0
        }
    
    # Check if property has address information
    if not property_obj.street_address or not property_obj.city or not property_obj.state:
        return {
            "error": "Property address information is incomplete. Please extract property information first.",
            "competitors_found": 0,
            "competitors_added": 0
        }
    
    # Geocode property address
    print(f"Geocoding property address...")
    coordinates = geocode_address(
        street=property_obj.street_address,
        city=property_obj.city,
        state=property_obj.state,
        zip_code=property_obj.zip_code
    )
    
    if not coordinates:
        return {
            "error": "Failed to geocode property address. Please verify the address is correct.",
            "competitors_found": 0,
            "competitors_added": 0
        }
    
    target_lat, target_lon = coordinates
    print(f"✓ Geocoded to coordinates: ({target_lat}, {target_lon})")
    
    # Build property address string for filtering
    property_address_parts = []
    if property_obj.street_address:
        property_address_parts.append(property_obj.street_address)
    if property_obj.city:
        property_address_parts.append(property_obj.city)
    if property_obj.state:
        property_address_parts.append(property_obj.state)
    property_address = ", ".join(property_address_parts)
    
    # Call Apify Google Maps Scraper Actor
    try:
        print(f"Searching for competitors using Apify Google Maps Scraper...")
        apify_client = get_apify_client()
        
        # Build location query
        location_query = f"{property_obj.city}, {property_obj.state}"
        if property_obj.zip_code:
            location_query = f"{property_obj.street_address}, {location_query} {property_obj.zip_code}"
        
        # Convert radius from miles to kilometers for Apify
        radius_km = radius_miles * 1.60934
        
        # Prepare Actor input
        actor_input = {
            "searchStringsArray": search_terms,
            "locationQuery": location_query,
            "maxCrawledPlacesPerSearch": max_results,
            "scrapePlaceDetailPage": False,  # We only need basic info
            "skipClosedPlaces": True,
            "language": "en",
            "customGeolocation": {
                "type": "Point",
                "coordinates": [target_lon, target_lat],  # Note: longitude first in GeoJSON
                "radiusKm": radius_km
            }
        }
        
        # Run the Actor and wait for it to finish
        print(f"Running Apify Actor: compass/crawler-google-places...")
        run = apify_client.actor("compass/crawler-google-places").call(run_input=actor_input)
        
        # Fetch results from the dataset
        print(f"Fetching results from dataset {run['defaultDatasetId']}...")
        dataset = apify_client.dataset(run["defaultDatasetId"])
        
        # Process results
        all_competitors = []
        seen_place_ids = set()
        
        for item in dataset.iterate_items():
            # Skip if no title (invalid result)
            if not item.get("title"):
                continue
            
            # Transform to Competitor format
            competitor = transform_competitor_data(
                item,
                property_obj.property_name or "",
                property_address,
                target_lat,
                target_lon
            )
            
            if competitor:
                # Skip duplicates by place_id
                if competitor.place_id:
                    if competitor.place_id in seen_place_ids:
                        continue
                    seen_place_ids.add(competitor.place_id)
                
                competitor.property_id = property_id
                all_competitors.append(competitor)
        
        print(f"✓ Found {len(all_competitors)} unique competitors")
        
        if not all_competitors:
            return {
                "competitors_found": 0,
                "competitors_added": 0,
                "message": "No competitors found within the specified radius."
            }
        
        # Store competitors in database
        competitors_added = property_repo.add_competitors(property_id, all_competitors)
        
        print(f"✓ Added {competitors_added} competitors to database")
        
        # Display summary
        print(f"\n[Competitor Search Results]")
        print("=" * 60)
        print(f"Property: {property_obj.property_name}")
        print(f"Search Radius: {radius_miles} miles")
        print(f"Competitors Found: {len(all_competitors)}")
        print(f"Competitors Added: {competitors_added}")
        print("\nTop Competitors (by distance):")
        sorted_competitors = sorted(all_competitors, key=lambda c: c.distance_miles if c.distance_miles else float('inf'))
        for i, comp in enumerate(sorted_competitors[:10], 1):
            distance_str = f"{comp.distance_miles:.2f} miles" if comp.distance_miles else "Unknown"
            rating_str = f" ({comp.rating:.1f}★)" if comp.rating else ""
            print(f"  {i}. {comp.competitor_name} - {distance_str}{rating_str}")
        print("=" * 60)
        
        return {
            "competitors_found": len(all_competitors),
            "competitors_added": competitors_added,
            "property_id": property_id,
            "search_radius_miles": radius_miles,
            "top_competitors": [
                {
                    "name": c.competitor_name,
                    "distance_miles": c.distance_miles,
                    "rating": c.rating,
                    "review_count": c.review_count
                }
                for c in sorted_competitors[:10]
            ]
        }
    
    except ValueError as e:
        # API key missing or other value errors
        print(f"Error: {e}")
        return {
            "error": str(e),
            "competitors_found": 0,
            "competitors_added": 0
        }
    
    except Exception as e:
        # Other errors (network, API, etc.)
        print(f"Error finding competitors: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to find competitors: {str(e)}",
            "competitors_found": 0,
            "competitors_added": 0
        }

