"""
Tool for extracting brand identity from property websites using Firecrawl.

Primary function: Uses Firecrawl's branding format to extract comprehensive brand identity
information (colors, fonts, typography, spacing, components, etc.) from property websites.
Also extracts tone information from website content using LLM analysis.
"""

import os
import json
from firecrawl import Firecrawl
from openai import OpenAI
from .cache_manager import (
    get_domain_from_url,
    is_branding_cache_valid,
    get_branding_cache_age,
    get_cached_branding_from_cache,
    save_branding_cache,
    get_cached_markdown,
    is_cache_valid
)
from .crawl_property_website import execute as crawl_property_website
from database import PropertyRepository


def get_firecrawl_client():
    """Initialize and return Firecrawl client with API key from environment."""
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError(
            "FIRECRAWL_API_KEY not found. Please set it in your environment variables."
        )
    return Firecrawl(api_key=api_key)


def get_openai_client():
    """Initialize and return OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Please set it in your environment variables."
        )
    return OpenAI(api_key=api_key)


def get_tone_schema():
    """Returns the JSON schema for tone extraction."""
    return {
        "type": "object",
        "properties": {
            "writing_style": {
                "type": "object",
                "properties": {
                    "formality_level": {
                        "type": "string",
                        "description": "Level of formality in writing (e.g., 'formal', 'professional', 'casual', 'conversational')",
                        "enum": ["very_formal", "formal", "professional", "moderate", "casual", "conversational", "very_casual"]
                    },
                    "professional_level": {
                        "type": "string",
                        "description": "Level of professionalism (e.g., 'high', 'moderate', 'low')",
                        "enum": ["very_high", "high", "moderate", "low", "very_low"]
                    },
                    "technical_level": {
                        "type": "string",
                        "description": "Level of technical language used (e.g., 'high', 'moderate', 'low')",
                        "enum": ["very_high", "high", "moderate", "low", "very_low"]
                    }
                },
                "required": ["formality_level", "professional_level", "technical_level"]
            },
            "emotional_tone": {
                "type": "object",
                "properties": {
                    "warmth": {
                        "type": "string",
                        "description": "Level of warmth in the tone (e.g., 'warm', 'neutral', 'cool')",
                        "enum": ["very_warm", "warm", "neutral", "cool", "very_cool"]
                    },
                    "energy_level": {
                        "type": "string",
                        "description": "Energy level of the tone (e.g., 'energetic', 'moderate', 'calm')",
                        "enum": ["very_energetic", "energetic", "moderate", "calm", "very_calm"]
                    },
                    "inviting_level": {
                        "type": "string",
                        "description": "How inviting/welcoming the tone is (e.g., 'very_inviting', 'inviting', 'neutral')",
                        "enum": ["very_inviting", "inviting", "moderate", "neutral", "distant"]
                    }
                },
                "required": ["warmth", "energy_level", "inviting_level"]
            },
            "voice_characteristics": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "Array of descriptive tags for voice characteristics (e.g., ['conversational', 'authoritative', 'friendly', 'playful', 'serious'])"
            },
            "tone_tags": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "Array of overall tone descriptors that summarize the brand voice (e.g., ['professional', 'friendly', 'modern', 'inviting'])"
            },
            "description": {
                "type": "string",
                "description": "Free-form text description of the overall tone and voice of the website content"
            }
        },
        "required": ["writing_style", "emotional_tone", "voice_characteristics", "tone_tags", "description"]
    }


def get_openai_tone_json_schema():
    """Convert tone schema to OpenAI's JSON schema format for structured output."""
    base_schema = get_tone_schema()
    return {
        "name": "tone_analysis",
        "description": "Tone and voice analysis of website content",
        "schema": base_schema,
        "strict": False
    }


def extract_tone_from_content(markdown_content, client):
    """
    Use OpenAI to extract tone information from markdown content.
    
    Args:
        markdown_content: The markdown content scraped from the website
        client: OpenAI client instance
        
    Returns:
        Dictionary with extracted tone information, or None if extraction fails
    """
    if not markdown_content or not markdown_content.strip():
        return None
    
    try:
        # Truncate content if too long (OpenAI has token limits)
        # Keep a reasonable amount for tone analysis (roughly 50k characters should be enough)
        max_chars = 50000
        if len(markdown_content) > max_chars:
            print(f"⚠ Warning: Markdown content is {len(markdown_content)} chars, truncating to {max_chars} for tone analysis")
            markdown_content = markdown_content[:max_chars] + "\n\n[... content truncated for analysis ...]"
        
        response = client.beta.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at analyzing the tone and voice of website content. Analyze the writing style, emotional tone, and voice characteristics of the provided content. Be specific and accurate in your analysis."
                },
                {
                    "role": "user",
                    "content": f"""Analyze the tone and voice of the following website content (which may span multiple pages):

{markdown_content}

Extract comprehensive tone information including:
- Writing style: formality level, professionalism, technical language usage
- Emotional tone: warmth, energy level, how inviting/welcoming the content feels
- Voice characteristics: descriptive tags like conversational, authoritative, friendly, playful, serious, etc.
- Overall tone tags: summary descriptors that capture the brand voice
- Description: a free-form text description of the overall tone

The content may be from multiple pages separated by "---PAGE BREAK---". Analyze the overall tone across all pages."""
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": get_openai_tone_json_schema()
            },
            temperature=0.3  # Slightly higher than property extraction for more nuanced tone analysis
        )
        
        # Parse the response
        content = response.choices[0].message.content
        if content:
            extracted_tone = json.loads(content)
            return extracted_tone
        else:
            return None
            
    except json.JSONDecodeError as e:
        print(f"⚠ Warning: Error parsing OpenAI tone extraction response: {e}")
        return None
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "rate_limit" in error_str.lower() or "Rate limit" in error_str:
            print(f"⚠ Warning: OpenAI rate limit reached during tone extraction")
            print(f"   Error details: {error_str[:200]}...")
        else:
            print(f"⚠ Warning: Error in OpenAI tone extraction: {e}")
        return None


def get_tool_definition():
    """Returns the tool definition for OpenAI function calling."""
    return {
        "type": "function",
        "function": {
            "name": "extract_brand_identity",
            "description": "Extract brand identity information (colors, fonts, typography, spacing, components, tone, etc.) from a property website using Firecrawl and LLM analysis. Checks cache first - if cached data exists, will use it unless force_refresh is True. Returns comprehensive branding data including color scheme, logo, colors, fonts, typography, spacing, UI components, and tone analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the property website to extract brand identity from"
                    },
                    "use_cache": {
                        "type": "boolean",
                        "description": "Whether to use cached data if available. If None/not provided, the agent will prompt the user. If True, uses cache. If False, forces fresh extraction."
                    },
                    "force_refresh": {
                        "type": "boolean",
                        "description": "Force a fresh extraction even if cache exists. Defaults to False.",
                        "default": False
                    }
                },
                "required": ["url"]
            }
        }
    }


def execute(arguments):
    """
    Execute the extract_brand_identity tool.
    
    Uses Firecrawl's branding format to extract comprehensive brand identity information.
    Returns branding data including colors, fonts, typography, spacing, components, etc.
    
    Process:
    1. Checks cache first (if use_cache is True or None)
    2. If no cache or force_refresh, calls Firecrawl API to extract visual branding
    3. Gets website content (from cache or by crawling) and extracts tone using LLM
    4. Merges visual branding and tone data
    5. Saves extracted branding to cache
    6. Saves branding to database if property exists
    7. Returns branding data with cache info
    
    Args:
        arguments: Dictionary containing tool arguments
            - url (str): The URL of the property website
            - use_cache (bool, optional): Whether to use cached data. None = prompt user, True = use cache, False = fresh extraction
            - force_refresh (bool, optional): Force fresh extraction even if cache exists. Defaults to False.
        
    Returns:
        Dictionary with branding_data and cache_info
    """
    url = arguments.get("url", "")
    use_cache = arguments.get("use_cache")  # None, True, or False
    force_refresh = arguments.get("force_refresh", False)
    
    if not url:
        return {
            "error": "URL is required",
            "branding_data": None
        }
    
    print(f"Extracting brand identity from property website: {url}")
    
    # Get domain for cache lookup
    domain = get_domain_from_url(url)
    cache_valid = is_branding_cache_valid(domain)
    cache_age = get_branding_cache_age(domain) if cache_valid else None
    
    # Debug: Print cache status for troubleshooting
    if cache_valid:
        print(f"🔍 Cache check: Found branding cache for {domain} (age: {cache_age:.1f} hours)" if cache_age else f"🔍 Cache check: Found branding cache for {domain} (age: unknown)")
    else:
        print(f"🔍 Cache check: No branding cache found for {domain}")
    
    # Determine if we should use cache
    should_use_cache = False
    if force_refresh:
        should_use_cache = False
        print("Force refresh requested - ignoring cache")
    elif use_cache is True:
        if cache_valid:
            should_use_cache = True
            print(f"Using cached branding (age: {cache_age:.1f} hours)")
        else:
            print("Cache requested but not valid - will extract fresh")
    elif use_cache is False:
        should_use_cache = False
        print("Fresh extraction requested - ignoring cache")
    elif cache_valid:
        # use_cache is None - return cache info for agent to prompt user
        # But only if cache_age is not None (safety check)
        if cache_age is not None:
            return {
                "cache_available": True,
                "cache_age_hours": cache_age,
                "domain": domain,
                "message": f"Cached branding available from {cache_age:.1f} hours ago. Set use_cache=True to use cache, or force_refresh=True to extract fresh.",
                "branding_data": None
            }
        else:
            # Cache was reported as valid but age is None - this shouldn't happen, but handle it
            print("⚠ Warning: Cache reported as valid but age is None - will extract fresh")
    
    try:
        branding_data = None
        
        # Try to use cache if requested
        if should_use_cache and cache_valid:
            branding_data = get_cached_branding_from_cache(domain)
            if branding_data:
                print(f"✓ USING CACHE: Loaded branding data from cache (age: {cache_age:.1f} hours)")
                
                # Check if tone is missing (backward compatibility with old cached data)
                if "tone" not in branding_data or not branding_data.get("tone"):
                    print("⚠ Cached branding missing tone data - extracting tone now...")
                    # Get markdown content for tone extraction
                    markdown_content = None
                    markdown_cache_valid = is_cache_valid(domain)
                    if markdown_cache_valid:
                        markdown_content = get_cached_markdown(domain)
                    
                    if not markdown_content:
                        # Try to crawl if no cached markdown
                        try:
                            crawl_args = {"url": url, "use_cache": True}
                            crawl_result = crawl_property_website(crawl_args)
                            if "error" not in crawl_result and "cache_available" not in crawl_result:
                                markdown_content = crawl_result.get("markdown")
                        except Exception as e:
                            print(f"⚠ Warning: Could not get markdown for tone extraction: {e}")
                    
                    if markdown_content:
                        try:
                            openai_client = get_openai_client()
                            tone_data = extract_tone_from_content(markdown_content, openai_client)
                            if tone_data:
                                branding_data["tone"] = tone_data
                                print(f"✓ Extracted and added tone to cached branding")
                                # Update cache with tone added
                                save_branding_cache(domain, branding_data)
                            else:
                                print(f"⚠ Warning: Tone extraction returned no data")
                        except Exception as e:
                            print(f"⚠ Warning: Error extracting tone for cached branding: {e}")
                    else:
                        print(f"⚠ Warning: No markdown content available - cannot extract tone")
            else:
                print("⚠ Cache exists but branding data is empty - will extract fresh")
                should_use_cache = False
        
        # Extract branding if not using cache
        if not should_use_cache or not branding_data:
            print("🔄 EXTRACTING FRESH: Using Firecrawl to extract brand identity...")
            firecrawl_client = get_firecrawl_client()
            
            # Call Firecrawl scrape API with branding format
            print(f"Calling Firecrawl API with branding format...")
            result = firecrawl_client.scrape(url, formats=["branding"])
            
            # Extract branding data from Firecrawl response
            # Firecrawl SDK returns a Document object with attributes
            branding_data = None
            if result:
                # Check if result is a Document object (has branding attribute)
                if hasattr(result, 'branding') and result.branding:
                    branding_data = result.branding
                # Check if result is a dict with 'branding' key
                elif isinstance(result, dict) and "branding" in result:
                    branding_data = result.get("branding")
                # Check if response has 'data' wrapper (API format)
                elif isinstance(result, dict) and "data" in result:
                    branding_data = result.get("data", {}).get("branding")
                # Check if result itself is the branding data
                elif isinstance(result, dict) and ("colorScheme" in result or "colors" in result):
                    branding_data = result
                # Try to convert Document object to dict if it has a model_dump or dict method
                elif hasattr(result, 'model_dump'):
                    result_dict = result.model_dump()
                    branding_data = result_dict.get("branding") or result_dict.get("data", {}).get("branding")
                elif hasattr(result, '__dict__'):
                    result_dict = result.__dict__
                    if "branding" in result_dict:
                        branding_data = result_dict["branding"]
                    elif "data" in result_dict:
                        data = result_dict["data"]
                        if isinstance(data, dict):
                            branding_data = data.get("branding")
                        elif hasattr(data, 'branding'):
                            branding_data = data.branding
            
            # Convert BrandingProfile object to dict if needed (for JSON serialization)
            # This must happen before any cache or database operations
            if branding_data:
                if not isinstance(branding_data, dict):
                    print(f"🔧 Converting BrandingProfile object to dict (type: {type(branding_data)})")
                    if hasattr(branding_data, 'model_dump'):
                        # Pydantic v2 model - use model_dump() with mode='json' for deep serialization
                        try:
                            branding_data = branding_data.model_dump(mode='json')
                            print(f"✓ Converted using model_dump(mode='json')")
                        except TypeError:
                            # Fallback if mode='json' not supported
                            try:
                                branding_data = branding_data.model_dump()
                                print(f"✓ Converted using model_dump()")
                            except Exception as e:
                                print(f"⚠ Warning: model_dump() failed: {e}")
                                branding_data = {}
                        except Exception as e:
                            print(f"⚠ Warning: model_dump() failed: {e}")
                            branding_data = {}
                    elif hasattr(branding_data, 'dict'):
                        # Pydantic v1 style
                        try:
                            branding_data = branding_data.dict()
                            print(f"✓ Converted using dict()")
                        except Exception as e:
                            print(f"⚠ Warning: dict() failed: {e}")
                            branding_data = {}
                    elif hasattr(branding_data, '__dict__'):
                        # Regular object - convert to dict, but this might not handle nested objects
                        import json
                        try:
                            # Use json serialization to ensure all nested objects are converted
                            branding_data = json.loads(json.dumps(branding_data, default=str))
                            print(f"✓ Converted using json serialization")
                        except Exception as e:
                            print(f"⚠ Warning: json conversion failed: {e}, trying __dict__")
                            try:
                                branding_data = branding_data.__dict__
                                print(f"✓ Converted using __dict__")
                            except Exception as e2:
                                print(f"⚠ Warning: __dict__ conversion also failed: {e2}")
                                branding_data = {}
                    else:
                        # Try to convert using json.dumps/json.loads as last resort
                        import json
                        try:
                            branding_data = json.loads(json.dumps(branding_data, default=str))
                            print(f"✓ Converted using json serialization")
                        except Exception as e:
                            print(f"⚠ Warning: Could not convert branding_data to dict, type: {type(branding_data)}, error: {e}")
                            branding_data = {}
                
                # Ensure the dict is fully JSON serializable (handle any remaining nested objects)
                if isinstance(branding_data, dict):
                    import json
                    try:
                        # Test serialization to catch any nested non-serializable objects
                        json.dumps(branding_data)
                        print(f"✓ Verified branding_data is JSON serializable")
                    except TypeError as e:
                        print(f"⚠ Warning: branding_data contains non-serializable objects: {e}")
                        # Try to fix by converting all nested objects
                        try:
                            branding_data = json.loads(json.dumps(branding_data, default=str))
                            print(f"✓ Fixed non-serializable objects using default=str")
                        except Exception as e2:
                            print(f"⚠ Warning: Could not fix serialization: {e2}")
                            branding_data = {}
            
            if branding_data and branding_data != {}:
                print(f"✓ Successfully extracted visual branding data")
                
                # Extract tone from website content
                print("🎨 Extracting tone from website content...")
                markdown_content = None
                
                # Try to get markdown from cache first
                markdown_cache_valid = is_cache_valid(domain)
                if markdown_cache_valid:
                    markdown_content = get_cached_markdown(domain)
                    if markdown_content:
                        print(f"✓ Using cached markdown content for tone analysis")
                
                # If no cached markdown, crawl the website
                if not markdown_content:
                    print("🔄 Crawling website to get content for tone analysis...")
                    try:
                        crawl_args = {"url": url}
                        if use_cache is not None:
                            crawl_args["use_cache"] = use_cache
                        if force_refresh:
                            crawl_args["force_refresh"] = force_refresh
                        
                        crawl_result = crawl_property_website(crawl_args)
                        
                        # Check if crawl returned an error or cache prompt
                        if "error" in crawl_result:
                            print(f"⚠ Warning: Failed to crawl website for tone analysis: {crawl_result.get('error')}")
                        elif "cache_available" in crawl_result and crawl_result["cache_available"]:
                            # Cache prompting needed - skip tone extraction for now
                            print(f"⚠ Warning: Cache prompt needed for markdown - skipping tone extraction")
                        else:
                            markdown_content = crawl_result.get("markdown")
                            if markdown_content:
                                print(f"✓ Retrieved markdown content for tone analysis")
                    except Exception as crawl_error:
                        print(f"⚠ Warning: Error crawling website for tone analysis: {crawl_error}")
                
                # Extract tone if we have markdown content
                if markdown_content:
                    try:
                        openai_client = get_openai_client()
                        tone_data = extract_tone_from_content(markdown_content, openai_client)
                        
                        if tone_data:
                            # Merge tone into branding_data
                            branding_data["tone"] = tone_data
                            print(f"✓ Successfully extracted and merged tone data")
                        else:
                            print(f"⚠ Warning: Tone extraction returned no data - continuing with visual branding only")
                    except ValueError as api_error:
                        # API key missing
                        print(f"⚠ Warning: OpenAI API key not found - skipping tone extraction: {api_error}")
                    except Exception as tone_error:
                        print(f"⚠ Warning: Error extracting tone: {tone_error}")
                        # Continue with visual branding only
                else:
                    print(f"⚠ Warning: No markdown content available - skipping tone extraction")
                
                # Save to cache - only save if we have actual branding data
                cache_saved = save_branding_cache(domain, branding_data)
                if cache_saved:
                    print(f"✓ Cached branding data for {domain}")
                else:
                    print(f"⚠ Warning: Failed to save branding cache for {domain}")
            else:
                print(f"⚠ Warning: Firecrawl returned no branding data")
                print(f"   Debug: Result type: {type(result)}")
                if isinstance(result, dict):
                    print(f"   Debug: Result keys: {list(result.keys())}")
                elif hasattr(result, '__dict__'):
                    print(f"   Debug: Result attributes: {list(result.__dict__.keys())}")
                elif hasattr(result, 'model_fields'):
                    print(f"   Debug: Result model fields: {list(result.model_fields.keys()) if hasattr(result.model_fields, 'keys') else 'N/A'}")
                branding_data = {}
                print(f"⚠ Warning: No branding data found to cache (skipping cache save)")
        
        # Save branding to database if we have a property for this URL
        try:
            property_repo = PropertyRepository()
            # Try to find property by website URL
            property_obj = property_repo.get_property_by_website_url(url)
            
            if property_obj and property_obj.id:
                # Only save if we have actual branding data
                if branding_data and branding_data != {}:
                    branding_id = property_repo.create_or_update_branding(
                        property_obj.id,
                        branding_data,
                        url
                    )
                    if branding_id:
                        print(f"✓ Saved branding data to database for property")
                    else:
                        print(f"⚠ Warning: Failed to save branding data to database")
                else:
                    print(f"⚠ Warning: No branding data to save (Firecrawl returned empty data)")
            else:
                print(f"ℹ No property found for URL - branding not saved to database (will be cached)")
        except Exception as db_error:
            error_msg = str(db_error)
            # Check if it's a table not found error
            if "property_branding" in error_msg.lower() or "PGRST205" in error_msg:
                print(f"⚠ Warning: Database table 'property_branding' not found.")
                print(f"   Please run the migration: supabase/migrations/20251221160906_add_property_branding_table.sql")
                print(f"   Branding data was cached but not saved to database.")
            else:
                print(f"⚠ Warning: Error saving branding to database: {db_error}")
            # Don't fail the extraction if database save fails
        
        # Return branding data
        result = {
            "branding_data": branding_data
        }
        
        # Add cache info and show status
        if should_use_cache and cache_valid:
            result["cache_info"] = {
                "used_cache": True,
                "cache_age_hours": cache_age
            }
            print(f"\n[Cache Status] ✓ Used cached branding (age: {cache_age:.1f} hours)")
        else:
            # Check if we actually cached anything
            actually_cached = branding_data and branding_data != {} and not should_use_cache
            result["cache_info"] = {
                "used_cache": False,
                "cached": actually_cached  # Only True if we actually cached data
            }
            if actually_cached:
                print(f"\n[Cache Status] ✓ Extracted fresh branding and saved to cache")
            else:
                print(f"\n[Cache Status] ⚠ Extracted branding but no data to cache")
        
        print(f"[Tool Execution Complete]")
        return result
    
    except ValueError as e:
        # API key missing or other value errors
        print(f"Error: {e}")
        return {
            "error": str(e),
            "branding_data": None
        }
    
    except Exception as e:
        # Other errors (network, API, etc.)
        print(f"Error extracting brand identity from property website: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to extract brand identity from property website: {str(e)}",
            "branding_data": None
        }

