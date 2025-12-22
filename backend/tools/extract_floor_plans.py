"""
Tool for extracting floor plans from property websites.

Extracts:
- Floor plan name
- Size (square feet)
- Bedrooms/bathrooms count
- Price/price range
- Unit availability

Can accept either a URL (will call crawl_property_website internally) or markdown content directly.
"""

import os
import json
import re
from openai import OpenAI
from .crawl_property_website import execute as crawl_property_website
from .cache_manager import (
    get_domain_from_url,
    is_cache_valid,
    get_cache_age,
    get_cached_markdown
)
from database import PropertyRepository


def get_openai_client():
    """Initialize and return OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Please set it in your environment variables."
        )
    return OpenAI(api_key=api_key)


def parse_price_string(price_string):
    """
    Parse a price string into min_price and max_price numeric values.
    
    Handles formats like:
    - "$1,200-$1,500" -> min: 1200, max: 1500
    - "$1,200" -> min: 1200, max: 1200
    - "Starting at $1,200" -> min: 1200, max: None
    - "$1,200+" -> min: 1200, max: None
    - "Call for pricing" -> min: None, max: None
    
    Args:
        price_string: String containing price information
        
    Returns:
        Tuple of (min_price, max_price) as floats, or (None, None) if not parseable
    """
    if not price_string:
        return None, None
    
    # Remove common prefixes
    price_str = price_string.strip()
    price_str = re.sub(r'^(starting\s+at|from|as\s+low\s+as)\s+', '', price_str, flags=re.IGNORECASE)
    
    # Extract all numbers (with commas)
    numbers = re.findall(r'\$?([\d,]+)', price_str)
    
    if not numbers:
        return None, None
    
    # Convert to integers (remove commas)
    prices = [int(num.replace(',', '')) for num in numbers]
    
    if len(prices) == 1:
        # Single price
        return float(prices[0]), float(prices[0])
    elif len(prices) >= 2:
        # Price range - take first and last
        return float(prices[0]), float(prices[-1])
    else:
        return None, None


def get_floor_plans_schema():
    """Returns the JSON schema for floor plans extraction."""
    return {
        "type": "object",
        "properties": {
            "floor_plans": {
                "type": "array",
                "description": "List of floor plans available at the property",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the floor plan (e.g., '1BR/1BA', 'Studio', 'A1', 'One Bedroom')"
                        },
                        "size_sqft": {
                            "type": "integer",
                            "description": "Square footage of the floor plan"
                        },
                        "bedrooms": {
                            "type": "integer",
                            "description": "Number of bedrooms"
                        },
                        "bathrooms": {
                            "type": "number",
                            "description": "Number of bathrooms (supports decimals for half baths, e.g., 1.5, 2.5)"
                        },
                        "price_string": {
                            "type": "string",
                            "description": "Original price text from the website (e.g., '$1,200-$1,500', 'Starting at $1,200', 'Call for pricing')"
                        },
                        "available_units": {
                            "type": "integer",
                            "description": "Number of available units for this floor plan"
                        },
                        "is_available": {
                            "type": "boolean",
                            "description": "Availability status (true if available, false if not available, null if unknown)"
                        }
                    },
                    "required": ["name"]
                }
            }
        },
        "required": ["floor_plans"]
    }


def get_openai_json_schema():
    """Convert our JSON schema to OpenAI's JSON schema format for structured output."""
    base_schema = get_floor_plans_schema()
    return {
        "name": "floor_plans_information",
        "description": "Extracted floor plans information from a property website",
        "schema": base_schema,
        "strict": False  # Allow null values for missing fields
    }


def extract_with_openai(markdown_content, client):
    """
    Use OpenAI to extract structured floor plans information from markdown content.
    
    Args:
        markdown_content: The markdown content scraped from the website
        client: OpenAI client instance
        
    Returns:
        Dictionary with extracted floor plans information
    """
    try:
        response = client.beta.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at extracting floor plan information from property websites. Extract floor plan details including name, size, bedrooms, bathrooms, prices, and availability accurately. If information is not found, use null for that field."
                },
                {
                    "role": "user",
                    "content": f"""Extract floor plans information from the following website content (which may span multiple pages):

{markdown_content}

Extract the following information for each floor plan:
- Name of the floor plan (e.g., "1BR/1BA", "Studio", "A1", "One Bedroom")
- Size in square feet
- Number of bedrooms
- Number of bathrooms (include decimals for half baths, e.g., 1.5, 2.5)
- Price information (store the original text as price_string, e.g., "$1,200-$1,500", "Starting at $1,200", "Call for pricing")
- Availability information (number of available units if specified, or availability status)

The content may be from multiple pages separated by "---PAGE BREAK---". Look through all pages to find floor plan information, especially on pages like "Floor Plans", "Apartments", "Availability", or similar sections. If no floor plans are found, return an empty array."""
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": get_openai_json_schema()
            },
            temperature=0.1  # Low temperature for more consistent extraction
        )
        
        # Parse the response
        content = response.choices[0].message.content
        if content:
            extracted_data = json.loads(content)
            return extracted_data
        else:
            return None
            
    except json.JSONDecodeError as e:
        print(f"Error parsing OpenAI response: {e}")
        return None
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "rate_limit" in error_str.lower() or "Rate limit" in error_str:
            print(f"\n⚠️  Rate Limit Error during extraction:")
            print("OpenAI rate limit reached. Try using cached data (use_cache=True) to reduce API calls.")
            print(f"Error details: {error_str[:200]}...")
        else:
            print(f"Error in OpenAI extraction: {e}")
        raise


def get_tool_definition():
    """Returns the tool definition for OpenAI function calling."""
    return {
        "type": "function",
        "function": {
            "name": "extract_floor_plans",
            "description": "Extract floor plans information from a property website. Can accept either a URL (will crawl/scrape the site first) or markdown content directly. Returns floor plan details including name, size, bedrooms, bathrooms, prices, and availability. Checks cache first - if cached data exists, will use it unless force_refresh is True.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the property website to extract floor plans from. If provided, will call crawl_property_website internally to get the content."
                    },
                    "markdown": {
                        "type": "string",
                        "description": "Raw markdown content from a property website. Use this if you already have the crawled content. Either url or markdown must be provided."
                    },
                    "use_cache": {
                        "type": "boolean",
                        "description": "When url is provided, whether to use cached data if available. Passed through to crawl_property_website."
                    },
                    "force_refresh": {
                        "type": "boolean",
                        "description": "When url is provided, force a fresh crawl even if cache exists. Passed through to crawl_property_website."
                    }
                },
                "required": []
            }
        }
    }


def execute(arguments):
    """
    Execute the extract_floor_plans tool.
    
    Extracts floor plans information from website content.
    Can accept either a URL (calls crawl_property_website internally) or markdown content directly.
    
    Args:
        arguments: Dictionary containing tool arguments
            - url (str, optional): The URL of the property website
            - markdown (str, optional): Raw markdown content from the website
            - use_cache (bool, optional): When url provided, whether to use cached data. Passed to crawl_property_website.
            - force_refresh (bool, optional): When url provided, force fresh crawl. Passed to crawl_property_website.
        
    Returns:
        Dictionary with extracted floor plans information
    """
    url = arguments.get("url")
    markdown = arguments.get("markdown")
    use_cache = arguments.get("use_cache")
    force_refresh = arguments.get("force_refresh", False)
    
    # Validate that at least one input is provided
    if not url and not markdown:
        return {
            "error": "Either 'url' or 'markdown' must be provided",
            "floor_plans": []
        }
    
    # If URL is provided, check cache first or get markdown by calling crawl_property_website
    if url:
        domain = get_domain_from_url(url)
        cache_valid = is_cache_valid(domain)
        cache_age = get_cache_age(domain) if cache_valid else None
        
        # Determine if we should use cache
        should_use_cache = False
        if force_refresh:
            should_use_cache = False
            print("Force refresh requested - ignoring cache")
        elif use_cache is True:
            if cache_valid:
                should_use_cache = True
                print(f"Using cached markdown (age: {cache_age:.1f} hours)")
            else:
                print("Cache requested but not valid - will crawl fresh")
        elif use_cache is False:
            should_use_cache = False
            print("Fresh crawl requested - ignoring cache")
        elif cache_valid and cache_age is not None:
            # use_cache is None - return cache info for agent to prompt user
            return {
                "cache_available": True,
                "cache_age_hours": cache_age,
                "domain": domain,
                "message": f"Cached markdown available from {cache_age:.1f} hours ago. Set use_cache=True to use cache, or force_refresh=True to extract fresh.",
                "floor_plans": []
            }
        
        # Get markdown content
        if should_use_cache and cache_valid:
            markdown = get_cached_markdown(domain)
            if not markdown:
                print("⚠ Cache exists but markdown is empty - will crawl fresh")
                should_use_cache = False
        
        if not should_use_cache or not markdown:
            print(f"Getting website content from: {url}")
            crawl_args = {"url": url}
            if use_cache is not None:
                crawl_args["use_cache"] = use_cache
            if force_refresh:
                crawl_args["force_refresh"] = force_refresh
            crawl_result = crawl_property_website(crawl_args)
            
            # Check if crawl returned an error or cache prompt
            if "error" in crawl_result:
                return {
                    "error": f"Failed to crawl website: {crawl_result.get('error')}",
                    "floor_plans": []
                }
            
            if "cache_available" in crawl_result and crawl_result["cache_available"]:
                # Cache prompting needed - return the cache info
                return {
                    "cache_available": True,
                    "cache_age_hours": crawl_result.get("cache_age_hours"),
                    "domain": crawl_result.get("domain"),
                    "message": crawl_result.get("message"),
                    "floor_plans": []
                }
            
            # Get markdown from crawl result
            markdown = crawl_result.get("markdown")
            if not markdown:
                return {
                    "error": "No markdown content returned from crawl",
                    "floor_plans": []
                }
    
    # Extract structured data from markdown
    print("Extracting floor plans information from content...")
    try:
        openai_client = get_openai_client()
        extracted_data = extract_with_openai(markdown, openai_client)
        
        if not extracted_data:
            return {
                "error": "OpenAI extraction returned no data",
                "floor_plans": []
            }
        
        # Ensure we have the expected structure
        floor_plans = extracted_data.get("floor_plans", [])
        
        # Parse prices for each floor plan
        for fp in floor_plans:
            price_string = fp.get("price_string")
            if price_string:
                min_price, max_price = parse_price_string(price_string)
                fp["min_price"] = min_price
                fp["max_price"] = max_price
        
        final_result = {
            "floor_plans": floor_plans if floor_plans else []
        }
        
        # Display extracted information
        print(f"\n[Extracted Floor Plans Information]")
        print("=" * 60)
        
        if final_result.get("floor_plans"):
            print(f"\nFloor Plans ({len(floor_plans)}):")
            for i, fp in enumerate(floor_plans, 1):
                name = fp.get("name", "Unknown")
                size = fp.get("size_sqft")
                beds = fp.get("bedrooms")
                baths = fp.get("bathrooms")
                price_str = fp.get("price_string", "")
                min_price = fp.get("min_price")
                max_price = fp.get("max_price")
                avail_units = fp.get("available_units")
                is_avail = fp.get("is_available")
                
                details = []
                if size:
                    details.append(f"{size} sqft")
                if beds is not None:
                    details.append(f"{beds}BR")
                if baths is not None:
                    bath_str = str(baths) if baths % 1 != 0 else str(int(baths))
                    details.append(f"{bath_str}BA")
                if price_str:
                    details.append(price_str)
                if avail_units is not None:
                    details.append(f"{avail_units} available")
                elif is_avail is not None:
                    details.append("Available" if is_avail else "Not available")
                
                detail_str = f" ({', '.join(details)})" if details else ""
                print(f"  {i}. {name}{detail_str}")
        else:
            print(f"\nFloor Plans: Not found")
        
        print("=" * 60)
        
        # Save to database
        try:
            property_repo = PropertyRepository()
            
            # Try to find property by website URL
            property_obj = None
            if url:
                property_obj = property_repo.get_property_by_website_url(url)
            
            if property_obj and property_obj.id:
                # Save floor plans to database
                floor_plans_added = property_repo.add_property_floor_plans(
                    property_obj.id,
                    floor_plans,
                    url if url else None
                )
                if floor_plans_added > 0:
                    print(f"✓ Saved {floor_plans_added} floor plans to database (Property ID: {property_obj.id})")
                else:
                    print("⚠ Warning: Failed to save floor plans to database")
            else:
                print(f"ℹ No property found for URL - floor plans not saved to database")
        except Exception as db_error:
            error_msg = str(db_error)
            # Check if it's a table not found error
            if "property_floor_plans" in error_msg.lower() or "PGRST205" in error_msg:
                print(f"⚠ Warning: Database table 'property_floor_plans' not found.")
                print(f"   Please run the migration: supabase/migrations/20251221180000_add_property_floor_plans_table.sql")
                print(f"   Floor plans data was extracted but not saved to database.")
            else:
                print(f"⚠ Warning: Error saving to database: {db_error}")
            # Don't fail the extraction if database save fails
        
        print(f"[Tool Execution Complete]")
        return final_result
    
    except ValueError as e:
        # API key missing or other value errors
        print(f"Error: {e}")
        return {
            "error": str(e),
            "floor_plans": []
        }
    
    except Exception as e:
        # Other errors (network, API, etc.)
        print(f"Error extracting floor plans information: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to extract floor plans information: {str(e)}",
            "floor_plans": []
        }


