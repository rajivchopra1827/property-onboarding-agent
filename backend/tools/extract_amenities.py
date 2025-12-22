"""
Tool for extracting amenities from property websites.

Extracts:
- Building amenities (pool, gym, business center, etc.)
- Apartment amenities (appliances, features, etc.)

Can accept either a URL (will call crawl_property_website internally) or markdown content directly.
"""

import os
import json
import time
from openai import OpenAI
from .crawl_property_website import execute as crawl_property_website
from .cache_manager import (
    get_domain_from_url,
    is_cache_valid,
    get_cache_age,
    get_cached_markdown
)
from database import PropertyRepository

# #region agent log
LOG_PATH = "/Users/rajivchopra/Property Onboarding Agent/.cursor/debug.log"
def _log(location, message, data=None, hypothesis_id=None):
    try:
        with open(LOG_PATH, "a") as f:
            log_entry = {
                "timestamp": int(time.time() * 1000),
                "location": location,
                "message": message,
                "data": data or {},
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": hypothesis_id
            }
            f.write(json.dumps(log_entry) + "\n")
    except:
        pass
# #endregion


def get_openai_client():
    """Initialize and return OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Please set it in your environment variables."
        )
    return OpenAI(api_key=api_key)


def get_amenities_schema():
    """Returns the JSON schema for amenities extraction."""
    return {
        "type": "object",
        "properties": {
            "building_amenities": {
                "type": "array",
                "description": "Building-level amenities available to all residents (e.g., pool, gym, business center, parking, etc.)",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the amenity"
                        },
                        "description": {
                            "type": "string",
                            "description": "Optional description or details about the amenity"
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional category (e.g., 'recreation', 'business', 'parking', 'outdoor', etc.)"
                        }
                    },
                    "required": ["name"]
                }
            },
            "apartment_amenities": {
                "type": "array",
                "description": "Apartment/unit-level amenities and features (e.g., appliances, in-unit features, etc.)",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the amenity"
                        },
                        "description": {
                            "type": "string",
                            "description": "Optional description or details about the amenity"
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional category (e.g., 'appliances', 'features', 'technology', etc.)"
                        }
                    },
                    "required": ["name"]
                }
            }
        },
        "required": ["building_amenities", "apartment_amenities"]
    }


def get_openai_json_schema():
    """Convert our JSON schema to OpenAI's JSON schema format for structured output."""
    base_schema = get_amenities_schema()
    return {
        "name": "amenities_information",
        "description": "Extracted amenities information from a property website",
        "schema": base_schema,
        "strict": False  # Allow null values for missing fields
    }


def extract_with_openai(markdown_content, client):
    """
    Use OpenAI to extract structured amenities information from markdown content.
    
    Args:
        markdown_content: The markdown content scraped from the website
        client: OpenAI client instance
        
    Returns:
        Dictionary with extracted amenities information
    """
    # #region agent log
    _log("extract_with_openai:entry", "OpenAI extraction started", {
        "markdown_length": len(markdown_content) if markdown_content else 0
    }, "H1")
    # #endregion
    
    try:
        # #region agent log
        _log("extract_with_openai:before_api_call", "Before OpenAI API call", {}, "H1")
        # #endregion
        
        response = client.beta.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at extracting amenities information from property websites. Extract building amenities (available to all residents) and apartment amenities (in-unit features) accurately. If information is not found, use empty arrays for those fields."
                },
                {
                    "role": "user",
                    "content": f"""Extract amenities information from the following website content (which may span multiple pages):

{markdown_content}

Extract the following information:
- Building amenities: Amenities available to all residents (e.g., pool, gym, business center, parking, clubhouse, dog park, etc.)
- Apartment amenities: In-unit features and appliances (e.g., dishwasher, washer/dryer, air conditioning, hardwood floors, etc.)

The content may be from multiple pages separated by "---PAGE BREAK---". Look through all pages to find the complete information. For each amenity, include the name and optionally a description or category if available. If any category of amenities is not found, use an empty array for that field."""
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": get_openai_json_schema()
            },
            temperature=0.1  # Low temperature for more consistent extraction
        )
        
        # #region agent log
        _log("extract_with_openai:after_api_call", "OpenAI API call completed", {
            "has_response": bool(response),
            "has_choices": bool(response.choices) if response else False,
            "choices_count": len(response.choices) if response and response.choices else 0
        }, "H1")
        # #endregion
        
        # Parse the response
        content = response.choices[0].message.content
        
        # #region agent log
        _log("extract_with_openai:before_json_parse", "Before JSON parsing", {
            "has_content": bool(content),
            "content_length": len(content) if content else 0,
            "content_preview": content[:200] if content else None
        }, "H2")
        # #endregion
        
        if content:
            extracted_data = json.loads(content)
            
            # #region agent log
            _log("extract_with_openai:after_json_parse", "JSON parsing successful", {
                "has_building_amenities": "building_amenities" in extracted_data,
                "has_apartment_amenities": "apartment_amenities" in extracted_data,
                "building_count": len(extracted_data.get("building_amenities", [])),
                "apartment_count": len(extracted_data.get("apartment_amenities", []))
            }, "H2")
            # #endregion
            
            return extracted_data
        else:
            # #region agent log
            _log("extract_with_openai:no_content", "OpenAI response has no content", {}, "H1")
            # #endregion
            return None
            
    except json.JSONDecodeError as e:
        # #region agent log
        _log("extract_with_openai:json_error", "JSON parsing failed", {
            "error": str(e),
            "error_type": type(e).__name__
        }, "H2")
        # #endregion
        print(f"Error parsing OpenAI response: {e}")
        return None
    except Exception as e:
        error_str = str(e)
        # #region agent log
        _log("extract_with_openai:exception", "Exception during OpenAI extraction", {
            "error": error_str,
            "error_type": type(e).__name__,
            "is_rate_limit": "429" in error_str or "rate_limit" in error_str.lower() or "Rate limit" in error_str
        }, "H1")
        # #endregion
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
            "name": "extract_amenities",
            "description": "Extract amenities information from a property website. Can accept either a URL (will crawl/scrape the site first) or markdown content directly. Returns building amenities (pool, gym, etc.) and apartment amenities (appliances, features, etc.). Checks cache first - if cached data exists, will use it unless force_refresh is True.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the property website to extract amenities from. If provided, will call crawl_property_website internally to get the content."
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
    Execute the extract_amenities tool.
    
    Extracts amenities information from website content.
    Can accept either a URL (calls crawl_property_website internally) or markdown content directly.
    
    Args:
        arguments: Dictionary containing tool arguments
            - url (str, optional): The URL of the property website
            - markdown (str, optional): Raw markdown content from the website
            - use_cache (bool, optional): When url provided, whether to use cached data. Passed to crawl_property_website.
            - force_refresh (bool, optional): When url provided, force fresh crawl. Passed to crawl_property_website.
        
    Returns:
        Dictionary with extracted amenities information
    """
    # #region agent log
    _log("extract_amenities.py:execute:entry", "Amenities extraction started", {
        "has_url": bool(arguments.get("url")),
        "has_markdown": bool(arguments.get("markdown")),
        "use_cache": arguments.get("use_cache"),
        "force_refresh": arguments.get("force_refresh", False)
    }, "H1")
    # #endregion
    
    url = arguments.get("url")
    markdown = arguments.get("markdown")
    use_cache = arguments.get("use_cache")
    force_refresh = arguments.get("force_refresh", False)
    
    # Validate that at least one input is provided
    if not url and not markdown:
        return {
            "error": "Either 'url' or 'markdown' must be provided",
            "building_amenities": [],
            "apartment_amenities": []
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
                "building_amenities": [],
                "apartment_amenities": []
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
                    "building_amenities": [],
                    "apartment_amenities": []
                }
            
            if "cache_available" in crawl_result and crawl_result["cache_available"]:
                # Cache prompting needed - return the cache info
                return {
                    "cache_available": True,
                    "cache_age_hours": crawl_result.get("cache_age_hours"),
                    "domain": crawl_result.get("domain"),
                    "message": crawl_result.get("message"),
                    "building_amenities": [],
                    "apartment_amenities": []
                }
            
            # Get markdown from crawl result
            markdown = crawl_result.get("markdown")
            if not markdown:
                # #region agent log
                _log("extract_amenities.py:execute:no_markdown", "No markdown from crawl", {
                    "crawl_result_keys": list(crawl_result.keys()) if crawl_result else []
                }, "H3")
                # #endregion
                return {
                    "error": "No markdown content returned from crawl",
                    "building_amenities": [],
                    "apartment_amenities": []
                }
    
    # Extract structured data from markdown
    print("Extracting amenities information from content...")
    
    # #region agent log
    _log("extract_amenities.py:execute:before_openai", "Before OpenAI extraction", {
        "markdown_length": len(markdown) if markdown else 0,
        "markdown_preview": markdown[:200] if markdown else None,
        "markdown_is_empty": not markdown or len(markdown.strip()) == 0
    }, "H3")
    # #endregion
    
    try:
        openai_client = get_openai_client()
        extracted_data = extract_with_openai(markdown, openai_client)
        
        if not extracted_data:
            # #region agent log
            _log("extract_amenities.py:execute:no_extracted_data", "OpenAI returned no data", {}, "H1")
            # #endregion
            return {
                "error": "OpenAI extraction returned no data",
                "building_amenities": [],
                "apartment_amenities": []
            }
        
        # Ensure we have the expected structure
        building_amenities = extracted_data.get("building_amenities", [])
        apartment_amenities = extracted_data.get("apartment_amenities", [])
        
        # #region agent log
        _log("extract_amenities.py:execute:extracted_data", "Extracted data received", {
            "building_count": len(building_amenities) if building_amenities else 0,
            "apartment_count": len(apartment_amenities) if apartment_amenities else 0
        }, "H1")
        # #endregion
        
        final_result = {
            "building_amenities": building_amenities if building_amenities else [],
            "apartment_amenities": apartment_amenities if apartment_amenities else []
        }
        
        # Display extracted information
        print(f"\n[Extracted Amenities Information]")
        print("=" * 60)
        
        if final_result.get("building_amenities"):
            print(f"\nBuilding Amenities ({len(building_amenities)}):")
            for i, amenity in enumerate(building_amenities, 1):
                name = amenity.get("name", "Unknown")
                desc = amenity.get("description", "")
                category = amenity.get("category", "")
                if desc or category:
                    details = []
                    if category:
                        details.append(f"Category: {category}")
                    if desc:
                        details.append(f"Description: {desc}")
                    print(f"  {i}. {name} ({', '.join(details)})")
                else:
                    print(f"  {i}. {name}")
        else:
            print(f"\nBuilding Amenities: Not found")
        
        if final_result.get("apartment_amenities"):
            print(f"\nApartment Amenities ({len(apartment_amenities)}):")
            for i, amenity in enumerate(apartment_amenities, 1):
                name = amenity.get("name", "Unknown")
                desc = amenity.get("description", "")
                category = amenity.get("category", "")
                if desc or category:
                    details = []
                    if category:
                        details.append(f"Category: {category}")
                    if desc:
                        details.append(f"Description: {desc}")
                    print(f"  {i}. {name} ({', '.join(details)})")
                else:
                    print(f"  {i}. {name}")
        else:
            print(f"\nApartment Amenities: Not found")
        
        print("=" * 60)
        
        # Save to database
        try:
            property_repo = PropertyRepository()
            
            # Try to find property by website URL
            property_obj = None
            if url:
                property_obj = property_repo.get_property_by_website_url(url)
            
            # #region agent log
            _log("extract_amenities.py:execute:before_db_save", "Before database save", {
                "has_url": bool(url),
                "has_property_obj": bool(property_obj),
                "property_id": property_obj.id if property_obj else None,
                "final_result_keys": list(final_result.keys())
            }, "H4")
            # #endregion
            
            if property_obj and property_obj.id:
                # Save amenities to database
                amenities_id = property_repo.create_or_update_amenities(
                    property_obj.id,
                    final_result,
                    url if url else None
                )
                
                # #region agent log
                _log("extract_amenities.py:execute:after_db_save", "After database save", {
                    "amenities_id": amenities_id,
                    "save_success": bool(amenities_id)
                }, "H4")
                # #endregion
                
                if amenities_id:
                    print(f"✓ Saved amenities information to database (ID: {amenities_id})")
                else:
                    print("⚠ Warning: Failed to save amenities information to database")
            else:
                # #region agent log
                _log("extract_amenities.py:execute:no_property", "No property found for URL", {
                    "url": url
                }, "H4")
                # #endregion
                print(f"ℹ No property found for URL - amenities not saved to database")
        except Exception as db_error:
            error_msg = str(db_error)
            # #region agent log
            _log("extract_amenities.py:execute:db_exception", "Database save exception", {
                "error": error_msg,
                "error_type": type(db_error).__name__,
                "is_table_not_found": "property_amenities" in error_msg.lower() or "PGRST205" in error_msg
            }, "H4")
            # #endregion
            # Check if it's a table not found error
            if "property_amenities" in error_msg.lower() or "PGRST205" in error_msg:
                print(f"⚠ Warning: Database table 'property_amenities' not found.")
                print(f"   Please run the migration: supabase/migrations/20251221170000_add_property_amenities_table.sql")
                print(f"   Amenities data was extracted but not saved to database.")
            else:
                print(f"⚠ Warning: Error saving to database: {db_error}")
            # Don't fail the extraction if database save fails
        
        print(f"[Tool Execution Complete]")
        
        # #region agent log
        _log("extract_amenities.py:execute:success", "Amenities extraction completed successfully", {
            "building_count": len(final_result.get("building_amenities", [])),
            "apartment_count": len(final_result.get("apartment_amenities", []))
        }, "H1")
        # #endregion
        
        return final_result
    
    except ValueError as e:
        # API key missing or other value errors
        # #region agent log
        _log("extract_amenities.py:execute:value_error", "ValueError exception", {
            "error": str(e),
            "error_type": type(e).__name__
        }, "H5")
        # #endregion
        print(f"Error: {e}")
        return {
            "error": str(e),
            "building_amenities": [],
            "apartment_amenities": []
        }
    
    except Exception as e:
        # Other errors (network, API, etc.)
        # #region agent log
        _log("extract_amenities.py:execute:exception", "Exception during extraction", {
            "error": str(e),
            "error_type": type(e).__name__
        }, "H5")
        # #endregion
        print(f"Error extracting amenities information: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to extract amenities information: {str(e)}",
            "building_amenities": [],
            "apartment_amenities": []
        }

