"""
Tool for extracting structured property information from property websites.

Extracts:
- Property name
- Address (street, city, state, ZIP code)
- Phone number
- Email address
- Office hours

Can accept either a URL (will call crawl_property_website internally) or markdown content directly.
"""

import os
import json
from openai import OpenAI
from .crawl_property_website import execute as crawl_property_website
from database import PropertyRepository, Property


def get_openai_client():
    """Initialize and return OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Please set it in your environment variables."
        )
    return OpenAI(api_key=api_key)


def get_property_schema():
    """Returns the JSON schema for property information extraction."""
    return {
        "type": "object",
        "properties": {
            "property_name": {
                "type": "string",
                "description": "The name of the apartment complex or property"
            },
            "address": {
                "type": "object",
                "properties": {
                    "street": {
                        "type": "string",
                        "description": "Street address"
                    },
                    "city": {
                        "type": "string",
                        "description": "City name"
                    },
                    "state": {
                        "type": "string",
                        "description": "State abbreviation (e.g., CA, NY, TX)"
                    },
                    "zip_code": {
                        "type": "string",
                        "description": "ZIP code"
                    }
                },
                "required": ["street", "city", "state", "zip_code"]
            },
            "phone_number": {
                "type": "string",
                "description": "Contact phone number"
            },
            "email_address": {
                "type": "string",
                "description": "Contact email address"
            },
            "office_hours": {
                "type": "object",
                "properties": {
                    "monday_friday": {
                        "type": "string",
                        "description": "Office hours for Monday through Friday"
                    },
                    "saturday": {
                        "type": "string",
                        "description": "Office hours for Saturday"
                    },
                    "sunday": {
                        "type": "string",
                        "description": "Office hours for Sunday"
                    }
                },
                "required": []
            }
        },
        "required": ["property_name", "address"]
    }


def get_openai_json_schema():
    """Convert our JSON schema to OpenAI's JSON schema format for structured output."""
    base_schema = get_property_schema()
    return {
        "name": "property_information",
        "description": "Extracted property information from a property website",
        "schema": base_schema,
        "strict": False  # Allow null values for missing fields
    }


def extract_with_openai(markdown_content, client):
    """
    Use OpenAI to extract structured property information from markdown content.
    
    Args:
        markdown_content: The markdown content scraped from the website
        client: OpenAI client instance
        
    Returns:
        Dictionary with extracted property information
    """
    try:
        response = client.beta.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at extracting structured information from property websites. Extract the requested information accurately. If information is not found, use null for that field."
                },
                {
                    "role": "user",
                    "content": f"""Extract property information from the following website content (which may span multiple pages):

{markdown_content}

Extract the following information:
- Property name (name of the apartment complex or property)
- Full address (street, city, state, ZIP code)
- Phone number (often found on Contact Us or About pages)
- Email address (often found on Contact Us or About pages)
- Office hours (Monday-Friday, Saturday, Sunday)

The content may be from multiple pages separated by "---PAGE BREAK---". Look through all pages to find the complete information. If any information is not found, use null for that field."""
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
            "name": "extract_property_information",
            "description": "Extract structured property information from a property website. Can accept either a URL (will crawl/scrape the site first) or markdown content directly. Returns property name, address, phone number, email address, and office hours.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the property website to extract information from. If provided, will call crawl_property_website internally to get the content."
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
    Execute the extract_property_information tool.
    
    Extracts structured property information from website content.
    Can accept either a URL (calls crawl_property_website internally) or markdown content directly.
    
    Args:
        arguments: Dictionary containing tool arguments
            - url (str, optional): The URL of the property website
            - markdown (str, optional): Raw markdown content from the website
            - use_cache (bool, optional): When url provided, whether to use cached data. Passed to crawl_property_website.
            - force_refresh (bool, optional): When url provided, force fresh crawl. Passed to crawl_property_website.
        
    Returns:
        Dictionary with extracted property information
    """
    url = arguments.get("url")
    markdown = arguments.get("markdown")
    use_cache = arguments.get("use_cache")
    force_refresh = arguments.get("force_refresh", False)
    
    # Validate that at least one input is provided
    if not url and not markdown:
        return {
            "error": "Either 'url' or 'markdown' must be provided",
            "property_name": None,
            "address": None,
            "phone_number": None,
            "email_address": None,
            "office_hours": None,
            "property_id": None
        }
    
    # If URL is provided, get markdown by calling crawl_property_website
    if url:
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
                "property_name": None,
                "address": None,
                "phone_number": None,
                "email_address": None,
                "office_hours": None,
                "property_id": None
            }
        
        if "cache_available" in crawl_result and crawl_result["cache_available"]:
            # Cache prompting needed - return the cache info
            return {
                "cache_available": True,
                "cache_age_hours": crawl_result.get("cache_age_hours"),
                "domain": crawl_result.get("domain"),
                "message": crawl_result.get("message"),
                "property_name": None,
                "address": None,
                "phone_number": None,
                "email_address": None,
                "office_hours": None,
                "property_id": None
            }
        
        # Get markdown from crawl result
        markdown = crawl_result.get("markdown")
        if not markdown:
            return {
                "error": "No markdown content returned from crawl",
                "property_name": None,
                "address": None,
                "phone_number": None,
                "email_address": None,
                "office_hours": None,
                "property_id": None
            }
    
    # Extract structured data from markdown
    print("Extracting structured property information from content...")
    try:
        openai_client = get_openai_client()
        extracted_data = extract_with_openai(markdown, openai_client)
        
        if not extracted_data:
            return {
                "error": "OpenAI extraction returned no data",
                "property_name": None,
                "address": None,
                "phone_number": None,
                "email_address": None,
                "office_hours": None,
                "property_id": None
            }
        
        # Ensure we have the expected structure
        final_result = {
            "property_name": extracted_data.get("property_name"),
            "address": extracted_data.get("address"),
            "phone_number": extracted_data.get("phone_number"),
            "email_address": extracted_data.get("email_address"),
            "office_hours": extracted_data.get("office_hours")
        }
        
        # Display extracted information
        print(f"\n[Extracted Property Information]")
        print("=" * 60)
        if final_result.get("property_name"):
            print(f"Property Name: {final_result['property_name']}")
        else:
            print(f"Property Name: Not found")
        
        if final_result.get("address"):
            addr = final_result["address"]
            address_parts = []
            if addr.get("street"):
                address_parts.append(addr["street"])
            if addr.get("city"):
                address_parts.append(addr["city"])
            if addr.get("state"):
                address_parts.append(addr["state"])
            if addr.get("zip_code"):
                address_parts.append(addr["zip_code"])
            if address_parts:
                print(f"Address: {', '.join(address_parts)}")
            else:
                print(f"Address: Not found")
        else:
            print(f"Address: Not found")
        
        if final_result.get("phone_number"):
            print(f"Phone: {final_result['phone_number']}")
        else:
            print(f"Phone: Not found")
        
        if final_result.get("email_address"):
            print(f"Email: {final_result['email_address']}")
        else:
            print(f"Email: Not found")
        
        if final_result.get("office_hours"):
            hours = final_result["office_hours"]
            print(f"Office Hours:")
            if hours.get("monday_friday"):
                print(f"  Mon-Fri: {hours['monday_friday']}")
            if hours.get("saturday"):
                print(f"  Saturday: {hours['saturday']}")
            if hours.get("sunday"):
                print(f"  Sunday: {hours['sunday']}")
            if not any([hours.get("monday_friday"), hours.get("saturday"), hours.get("sunday")]):
                print(f"  Not found")
        else:
            print(f"Office Hours: Not found")
        
        print("=" * 60)
        
        # Save to database
        property_id = None
        try:
            property_repo = PropertyRepository()
            
            # Create Property model from extracted data
            address = final_result.get("address", {})
            property_model = Property(
                property_name=final_result.get("property_name"),
                street_address=address.get("street") if address else None,
                city=address.get("city") if address else None,
                state=address.get("state") if address else None,
                zip_code=address.get("zip_code") if address else None,
                phone=final_result.get("phone_number"),
                email=final_result.get("email_address"),
                office_hours=final_result.get("office_hours"),
                website_url=url if url else None
            )
            
            # Create or update property in database
            property_id = property_repo.create_or_update_property(property_model)
            
            if property_id:
                print(f"✓ Saved property information to database (ID: {property_id})")
                
                # Create extraction session record
                property_repo.create_extraction_session(
                    property_id=property_id,
                    website_url=url if url else "unknown",
                    status="completed"
                )
            else:
                print("⚠ Warning: Failed to save property information to database")
        except Exception as db_error:
            print(f"⚠ Warning: Error saving to database: {db_error}")
            # Don't fail the extraction if database save fails
        
        print(f"[Tool Execution Complete]")
        
        # Include property_id in the return value so other tools can use it
        return {
            **final_result,
            "property_id": property_id
        }
    
    except ValueError as e:
        # API key missing or other value errors
        print(f"Error: {e}")
        return {
            "error": str(e),
            "property_name": None,
            "address": None,
            "phone_number": None,
            "email_address": None,
            "office_hours": None,
            "property_id": None
        }
    
    except Exception as e:
        # Other errors (network, API, etc.)
        print(f"Error extracting property information: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to extract property information: {str(e)}",
            "property_name": None,
            "address": None,
            "phone_number": None,
            "email_address": None,
            "office_hours": None,
            "property_id": None
        }

