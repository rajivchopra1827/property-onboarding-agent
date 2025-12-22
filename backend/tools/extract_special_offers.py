"""
Tool for extracting special offers from property websites.

Extracts:
- Offer description (what the offer is)
- Validity date (when it expires)
- Descriptive text (additional details)
- Optional floor plan association

Can accept either a URL (will call crawl_property_website internally) or markdown content directly.
"""

import os
import json
from datetime import datetime, date
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


def get_special_offers_schema():
    """Returns the JSON schema for special offers extraction."""
    return {
        "type": "object",
        "properties": {
            "offers": {
                "type": "array",
                "description": "List of special offers available at the property",
                "items": {
                    "type": "object",
                    "properties": {
                        "offer_description": {
                            "type": "string",
                            "description": "Description of the offer (e.g., 'First month free', '$500 off moving costs', 'Get $200 off your first month')"
                        },
                        "valid_until": {
                            "type": "string",
                            "description": "Expiration date of the offer in YYYY-MM-DD format, or null if no expiration date is specified"
                        },
                        "descriptive_text": {
                            "type": "string",
                            "description": "Additional descriptive text or details about the offer, terms and conditions, etc."
                        },
                        "floor_plan_name": {
                            "type": "string",
                            "description": "Optional: Name of the floor plan this offer applies to (e.g., '1BR/1BA', 'Studio'). Leave null if the offer applies to all units."
                        }
                    },
                    "required": ["offer_description"]
                }
            }
        },
        "required": ["offers"]
    }


def get_openai_json_schema():
    """Convert our JSON schema to OpenAI's JSON schema format for structured output."""
    base_schema = get_special_offers_schema()
    return {
        "name": "special_offers_information",
        "description": "Extracted special offers information from a property website",
        "schema": base_schema,
        "strict": False  # Allow null values for missing fields
    }


def extract_with_openai(markdown_content, client):
    """
    Use OpenAI to extract structured special offers information from markdown content.
    
    Args:
        markdown_content: The markdown content scraped from the website
        client: OpenAI client instance
        
    Returns:
        Dictionary with extracted special offers information
    """
    try:
        response = client.beta.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at extracting special offers and promotions from property websites. Extract promotional offers, move-in specials, discounts, and other special deals accurately. Look for offers like 'first month free', 'move-in specials', 'discounts', 'promotions', etc. If information is not found, use an empty array for offers."
                },
                {
                    "role": "user",
                    "content": f"""Extract special offers information from the following website content (which may span multiple pages):

{markdown_content}

Extract the following information for each special offer:
- Offer description: What the offer is (e.g., "First month free", "$500 off moving costs", "Get $200 off your first month")
- Valid until: Expiration date in YYYY-MM-DD format if specified, or null if no expiration date
- Descriptive text: Any additional details, terms, conditions, or descriptive text about the offer
- Floor plan name: If the offer applies to a specific floor plan type, include the floor plan name (e.g., "1BR/1BA", "Studio"). Leave null if the offer applies to all units.

The content may be from multiple pages separated by "---PAGE BREAK---". Look through all pages to find special offers, especially on pages like "Special Offers", "Promotions", "Move-In Specials", "Current Deals", or similar sections. Also check the homepage, floor plans pages, and any banners or promotional sections. If no special offers are found, return an empty array."""
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


def filter_expired_offers(offers):
    """
    Filter out expired offers based on valid_until date.
    
    Args:
        offers: List of offer dictionaries
        
    Returns:
        List of offers that are still valid (not expired)
    """
    if not offers:
        return []
    
    today = date.today()
    valid_offers = []
    
    for offer in offers:
        valid_until_str = offer.get("valid_until")
        if valid_until_str:
            try:
                # Parse the date string (YYYY-MM-DD format)
                valid_until_date = datetime.strptime(valid_until_str, "%Y-%m-%d").date()
                if valid_until_date >= today:
                    valid_offers.append(offer)
                else:
                    print(f"  ⚠ Skipping expired offer: {offer.get('offer_description')} (expired {valid_until_str})")
            except ValueError:
                # If date parsing fails, include the offer (better to include than exclude)
                print(f"  ⚠ Could not parse date '{valid_until_str}' for offer '{offer.get('offer_description')}' - including anyway")
                valid_offers.append(offer)
        else:
            # No expiration date - include it
            valid_offers.append(offer)
    
    return valid_offers


def get_tool_definition():
    """Returns the tool definition for OpenAI function calling."""
    return {
        "type": "function",
        "function": {
            "name": "extract_special_offers",
            "description": "Extract special offers and promotions from a property website. Can accept either a URL (will crawl/scrape the site first) or markdown content directly. Returns offer descriptions, validity dates, descriptive text, and optional floor plan associations. Checks cache first - if cached data exists, will use it unless force_refresh is True.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the property website to extract special offers from. If provided, will call crawl_property_website internally to get the content."
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
    Execute the extract_special_offers tool.
    
    Extracts special offers information from website content.
    Can accept either a URL (calls crawl_property_website internally) or markdown content directly.
    
    Args:
        arguments: Dictionary containing tool arguments
            - url (str, optional): The URL of the property website
            - markdown (str, optional): Raw markdown content from the website
            - use_cache (bool, optional): When url provided, whether to use cached data. Passed to crawl_property_website.
            - force_refresh (bool, optional): When url provided, force fresh crawl. Passed to crawl_property_website.
        
    Returns:
        Dictionary with extracted special offers information
    """
    url = arguments.get("url")
    markdown = arguments.get("markdown")
    use_cache = arguments.get("use_cache")
    force_refresh = arguments.get("force_refresh", False)
    
    # Validate that at least one input is provided
    if not url and not markdown:
        return {
            "error": "Either 'url' or 'markdown' must be provided",
            "offers": []
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
                "offers": []
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
                    "offers": []
                }
            
            if "cache_available" in crawl_result and crawl_result["cache_available"]:
                # Cache prompting needed - return the cache info
                return {
                    "cache_available": True,
                    "cache_age_hours": crawl_result.get("cache_age_hours"),
                    "domain": crawl_result.get("domain"),
                    "message": crawl_result.get("message"),
                    "offers": []
                }
            
            # Get markdown from crawl result
            markdown = crawl_result.get("markdown")
            if not markdown:
                return {
                    "error": "No markdown content returned from crawl",
                    "offers": []
                }
    
    # Extract structured data from markdown
    print("Extracting special offers information from content...")
    try:
        openai_client = get_openai_client()
        extracted_data = extract_with_openai(markdown, openai_client)
        
        if not extracted_data:
            return {
                "error": "OpenAI extraction returned no data",
                "offers": []
            }
        
        # Ensure we have the expected structure
        offers = extracted_data.get("offers", [])
        
        # Filter out expired offers
        valid_offers = filter_expired_offers(offers)
        
        final_result = {
            "offers": valid_offers if valid_offers else []
        }
        
        # Display extracted information
        print(f"\n[Extracted Special Offers Information]")
        print("=" * 60)
        
        if final_result.get("offers"):
            print(f"\nSpecial Offers ({len(valid_offers)}):")
            for i, offer in enumerate(valid_offers, 1):
                desc = offer.get("offer_description", "Unknown")
                valid_until = offer.get("valid_until", "")
                descriptive_text = offer.get("descriptive_text", "")
                floor_plan = offer.get("floor_plan_name", "")
                
                details = []
                if valid_until:
                    details.append(f"Valid until: {valid_until}")
                if floor_plan:
                    details.append(f"Applies to: {floor_plan}")
                if descriptive_text:
                    # Truncate long descriptive text
                    desc_text = descriptive_text[:100] + "..." if len(descriptive_text) > 100 else descriptive_text
                    details.append(f"Details: {desc_text}")
                
                detail_str = f" ({', '.join(details)})" if details else ""
                print(f"  {i}. {desc}{detail_str}")
        else:
            print(f"\nSpecial Offers: Not found")
        
        print("=" * 60)
        
        # Save to database
        try:
            property_repo = PropertyRepository()
            
            # Try to find property by website URL
            property_obj = None
            if url:
                property_obj = property_repo.get_property_by_website_url(url)
            
            if property_obj and property_obj.id:
                # Save special offers to database
                offers_added = property_repo.add_property_special_offers(
                    property_obj.id,
                    valid_offers,
                    url if url else None
                )
                if offers_added > 0:
                    print(f"✓ Saved {offers_added} special offers to database (Property ID: {property_obj.id})")
                else:
                    print("⚠ Warning: Failed to save special offers to database")
            else:
                print(f"ℹ No property found for URL - special offers not saved to database")
        except Exception as db_error:
            error_msg = str(db_error)
            # Check if it's a table not found error
            if "property_special_offers" in error_msg.lower() or "PGRST205" in error_msg:
                print(f"⚠ Warning: Database table 'property_special_offers' not found.")
                print(f"   Please run the migration: supabase/migrations/20251221190000_add_property_special_offers_table.sql")
                print(f"   Special offers data was extracted but not saved to database.")
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
            "offers": []
        }
    
    except Exception as e:
        # Other errors (network, API, etc.)
        print(f"Error extracting special offers information: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to extract special offers information: {str(e)}",
            "offers": []
        }


