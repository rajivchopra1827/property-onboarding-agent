"""
Geocoding utility for converting addresses to coordinates.

Uses OpenStreetMap Nominatim API (free, no API key required).
"""

import requests
from typing import Optional, Tuple
import time


def geocode_address(
    street: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None
) -> Optional[Tuple[float, float]]:
    """
    Geocode an address to get latitude and longitude coordinates.
    
    Uses OpenStreetMap Nominatim API (free, no API key required).
    
    Args:
        street: Street address (optional)
        city: City name (optional)
        state: State abbreviation (optional)
        zip_code: ZIP code (optional)
        
    Returns:
        Tuple of (latitude, longitude) if geocoding successful, None otherwise
    """
    # Build address string from available components
    address_parts = []
    if street:
        address_parts.append(street)
    if city:
        address_parts.append(city)
    if state:
        address_parts.append(state)
    if zip_code:
        address_parts.append(zip_code)
    
    if not address_parts:
        print("Error: No address components provided for geocoding")
        return None
    
    address_query = ", ".join(address_parts)
    
    try:
        # Use Nominatim API (OpenStreetMap)
        # Rate limit: 1 request per second (we'll add a small delay)
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address_query,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        headers = {
            "User-Agent": "FionaFast-PropertyAgent/1.0"  # Required by Nominatim
        }
        
        # Add delay to respect rate limits (1 request per second)
        time.sleep(1)
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data and len(data) > 0:
            result = data[0]
            lat = float(result.get("lat", 0))
            lon = float(result.get("lon", 0))
            
            if lat != 0 and lon != 0:
                print(f"Geocoded address '{address_query}' to coordinates: ({lat}, {lon})")
                return (lat, lon)
            else:
                print(f"Warning: Geocoding returned invalid coordinates for '{address_query}'")
                return None
        else:
            print(f"Warning: No geocoding results found for '{address_query}'")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error geocoding address '{address_query}': {e}")
        return None
    except (ValueError, KeyError) as e:
        print(f"Error parsing geocoding response for '{address_query}': {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during geocoding for '{address_query}': {e}")
        return None


