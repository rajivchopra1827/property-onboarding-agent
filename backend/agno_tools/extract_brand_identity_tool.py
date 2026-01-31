"""
Agno-native tool for extracting brand identity from property websites.

Uses Firecrawl's branding format and LLM analysis to extract comprehensive
brand identity information (colors, fonts, typography, spacing, components, tone, etc.).
"""

import os
import json
from typing import Optional
from firecrawl import Firecrawl
from openai import OpenAI
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from tools.cache_manager import (
    get_domain_from_url,
    is_branding_cache_valid,
    get_branding_cache_age,
    get_cached_branding_from_cache,
    save_branding_cache,
    get_cached_markdown,
    is_cache_valid
)
from tools.crawl_property_website import execute as crawl_property_website
from database import PropertyRepository
from agno_tools.tool import Tool


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
                        "description": "Level of formality in writing",
                        "enum": ["very_formal", "formal", "professional", "moderate", "casual", "conversational", "very_casual"]
                    },
                    "professional_level": {
                        "type": "string",
                        "description": "Level of professionalism",
                        "enum": ["very_high", "high", "moderate", "low", "very_low"]
                    },
                    "technical_level": {
                        "type": "string",
                        "description": "Level of technical language used",
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
                        "enum": ["very_warm", "warm", "neutral", "cool", "very_cool"]
                    },
                    "energy_level": {
                        "type": "string",
                        "enum": ["very_energetic", "energetic", "moderate", "calm", "very_calm"]
                    },
                    "inviting_level": {
                        "type": "string",
                        "enum": ["very_inviting", "inviting", "moderate", "neutral", "distant"]
                    }
                },
                "required": ["warmth", "energy_level", "inviting_level"]
            },
            "voice_characteristics": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Array of descriptive tags for voice characteristics"
            },
            "tone_tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Array of overall tone descriptors"
            },
            "description": {
                "type": "string",
                "description": "Free-form text description of the overall tone"
            }
        },
        "required": ["writing_style", "emotional_tone", "voice_characteristics", "tone_tags", "description"]
    }


def get_openai_tone_json_schema():
    """Convert tone schema to OpenAI's JSON schema format."""
    base_schema = get_tone_schema()
    return {
        "name": "tone_analysis",
        "description": "Tone and voice analysis of website content",
        "schema": base_schema,
        "strict": False
    }


def extract_tone_from_content(markdown_content, client):
    """Use OpenAI to extract tone information from markdown content."""
    if not markdown_content or not markdown_content.strip():
        return None
    
    try:
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
            temperature=0.3
        )
        
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


def extract_brand_identity(
    url: str,
    use_cache: Optional[bool] = None,
    force_refresh: bool = False,
) -> dict:
    """
    Extract brand identity information from a property website.
    
    Uses Firecrawl's branding format and LLM analysis.
    """
    if not url:
        return {
            "error": "URL is required",
            "branding_data": None
        }
    
    print(f"Extracting brand identity from property website: {url}")
    
    domain = get_domain_from_url(url)
    cache_valid = is_branding_cache_valid(domain)
    cache_age = get_branding_cache_age(domain) if cache_valid else None
    
    if cache_valid:
        print(f"🔍 Cache check: Found branding cache for {domain} (age: {cache_age:.1f} hours)" if cache_age else f"🔍 Cache check: Found branding cache for {domain} (age: unknown)")
    else:
        print(f"🔍 Cache check: No branding cache found for {domain}")
    
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
        if cache_age is not None:
            return {
                "cache_available": True,
                "cache_age_hours": cache_age,
                "domain": domain,
                "message": f"Cached branding available from {cache_age:.1f} hours ago. Set use_cache=True to use cache, or force_refresh=True to extract fresh.",
                "branding_data": None
            }
        else:
            print("⚠ Warning: Cache reported as valid but age is None - will extract fresh")
    
    try:
        branding_data = None
        
        if should_use_cache and cache_valid:
            branding_data = get_cached_branding_from_cache(domain)
            if branding_data:
                print(f"✓ USING CACHE: Loaded branding data from cache (age: {cache_age:.1f} hours)")
                
                if "tone" not in branding_data or not branding_data.get("tone"):
                    print("⚠ Cached branding missing tone data - extracting tone now...")
                    markdown_content = None
                    markdown_cache_valid = is_cache_valid(domain)
                    if markdown_cache_valid:
                        markdown_content = get_cached_markdown(domain)
                    
                    if not markdown_content:
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
        
        if not should_use_cache or not branding_data:
            print("🔄 EXTRACTING FRESH: Using Firecrawl to extract brand identity...")
            firecrawl_client = get_firecrawl_client()
            
            print(f"Calling Firecrawl API with branding format...")
            try:
                result = firecrawl_client.scrape(url, formats=["branding"])
            except Exception as firecrawl_error:
                error_str = str(firecrawl_error)
                error_lower = error_str.lower()
                
                # Check for payment/credit related errors
                if ("402" in error_str or 
                    "payment required" in error_lower or 
                    "insufficient credits" in error_lower or
                    "insufficient credit" in error_lower):
                    print(f"\n❌ FIRECRAWL PAYMENT/CREDIT ERROR:")
                    print(f"   Your Firecrawl account has insufficient credits or payment is required.")
                    print(f"   Error details: {error_str}")
                    print(f"   Please check your Firecrawl account balance at https://firecrawl.dev/pricing")
                    print(f"   Or contact support at help@firecrawl.com")
                    return {
                        "error": "Firecrawl account has insufficient credits or payment required. Please check your account balance.",
                        "error_type": "firecrawl_payment_required",
                        "error_details": error_str,
                        "branding_data": None
                    }
                else:
                    # Re-raise other errors to be handled by outer exception handler
                    raise
            
            branding_data = None
            if result:
                if hasattr(result, 'branding') and result.branding:
                    branding_data = result.branding
                elif isinstance(result, dict) and "branding" in result:
                    branding_data = result.get("branding")
                elif isinstance(result, dict) and "data" in result:
                    branding_data = result.get("data", {}).get("branding")
                elif isinstance(result, dict) and ("colorScheme" in result or "colors" in result):
                    branding_data = result
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
            
            if branding_data:
                if not isinstance(branding_data, dict):
                    print(f"🔧 Converting BrandingProfile object to dict (type: {type(branding_data)})")
                    if hasattr(branding_data, 'model_dump'):
                        try:
                            branding_data = branding_data.model_dump(mode='json')
                            print(f"✓ Converted using model_dump(mode='json')")
                        except TypeError:
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
                        try:
                            branding_data = branding_data.dict()
                            print(f"✓ Converted using dict()")
                        except Exception as e:
                            print(f"⚠ Warning: dict() failed: {e}")
                            branding_data = {}
                    elif hasattr(branding_data, '__dict__'):
                        try:
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
                        try:
                            branding_data = json.loads(json.dumps(branding_data, default=str))
                            print(f"✓ Converted using json serialization")
                        except Exception as e:
                            print(f"⚠ Warning: Could not convert branding_data to dict, type: {type(branding_data)}, error: {e}")
                            branding_data = {}
                
                if isinstance(branding_data, dict):
                    try:
                        json.dumps(branding_data)
                        print(f"✓ Verified branding_data is JSON serializable")
                    except TypeError as e:
                        print(f"⚠ Warning: branding_data contains non-serializable objects: {e}")
                        try:
                            branding_data = json.loads(json.dumps(branding_data, default=str))
                            print(f"✓ Fixed non-serializable objects using default=str")
                        except Exception as e2:
                            print(f"⚠ Warning: Could not fix serialization: {e2}")
                            branding_data = {}
            
            if branding_data and branding_data != {}:
                print(f"✓ Successfully extracted visual branding data")
                
                print("🎨 Extracting tone from website content...")
                markdown_content = None
                
                markdown_cache_valid = is_cache_valid(domain)
                if markdown_cache_valid:
                    markdown_content = get_cached_markdown(domain)
                    if markdown_content:
                        print(f"✓ Using cached markdown content for tone analysis")
                
                if not markdown_content:
                    print("🔄 Crawling website to get content for tone analysis...")
                    try:
                        crawl_args = {"url": url}
                        if use_cache is not None:
                            crawl_args["use_cache"] = use_cache
                        if force_refresh:
                            crawl_args["force_refresh"] = force_refresh
                        
                        crawl_result = crawl_property_website(crawl_args)
                        
                        if "error" in crawl_result:
                            print(f"⚠ Warning: Failed to crawl website for tone analysis: {crawl_result.get('error')}")
                        elif "cache_available" in crawl_result and crawl_result["cache_available"]:
                            print(f"⚠ Warning: Cache prompt needed for markdown - skipping tone extraction")
                        else:
                            markdown_content = crawl_result.get("markdown")
                            if markdown_content:
                                print(f"✓ Retrieved markdown content for tone analysis")
                    except Exception as crawl_error:
                        print(f"⚠ Warning: Error crawling website for tone analysis: {crawl_error}")
                
                if markdown_content:
                    try:
                        openai_client = get_openai_client()
                        tone_data = extract_tone_from_content(markdown_content, openai_client)
                        
                        if tone_data:
                            branding_data["tone"] = tone_data
                            print(f"✓ Successfully extracted and merged tone data")
                        else:
                            print(f"⚠ Warning: Tone extraction returned no data - continuing with visual branding only")
                    except ValueError as api_error:
                        print(f"⚠ Warning: OpenAI API key not found - skipping tone extraction: {api_error}")
                    except Exception as tone_error:
                        print(f"⚠ Warning: Error extracting tone: {tone_error}")
                else:
                    print(f"⚠ Warning: No markdown content available - skipping tone extraction")
                
                cache_saved = save_branding_cache(domain, branding_data)
                if cache_saved:
                    print(f"✓ Cached branding data for {domain}")
                else:
                    print(f"⚠ Warning: Failed to save branding cache for {domain}")
            else:
                print(f"⚠ Warning: Firecrawl returned no branding data")
                branding_data = {}
        
        try:
            property_repo = PropertyRepository()
            property_obj = property_repo.get_property_by_website_url(url)
            
            if property_obj and property_obj.id:
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
            if "property_branding" in error_msg.lower() or "PGRST205" in error_msg:
                print(f"⚠ Warning: Database table 'property_branding' not found.")
                print(f"   Please run the migration: supabase/migrations/20251221160906_add_property_branding_table.sql")
                print(f"   Branding data was cached but not saved to database.")
            else:
                print(f"⚠ Warning: Error saving branding to database: {db_error}")
        
        result = {
            "branding_data": branding_data
        }
        
        if should_use_cache and cache_valid:
            result["cache_info"] = {
                "used_cache": True,
                "cache_age_hours": cache_age
            }
            print(f"\n[Cache Status] ✓ Used cached branding (age: {cache_age:.1f} hours)")
        else:
            actually_cached = branding_data and branding_data != {} and not should_use_cache
            result["cache_info"] = {
                "used_cache": False,
                "cached": actually_cached
            }
            if actually_cached:
                print(f"\n[Cache Status] ✓ Extracted fresh branding and saved to cache")
            else:
                print(f"\n[Cache Status] ⚠ Extracted branding but no data to cache")
        
        print(f"[Tool Execution Complete]")
        return result
    
    except ValueError as e:
        print(f"Error: {e}")
        return {
            "error": str(e),
            "branding_data": None
        }
    
    except Exception as e:
        print(f"Error extracting brand identity from property website: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to extract brand identity from property website: {str(e)}",
            "branding_data": None
        }


# Create Agno Tool
extract_brand_identity_tool = Tool(
    name="extract_brand_identity",
    description="Extract comprehensive brand identity information from a property website including colors, fonts, typography, spacing, UI components, logo, and design system.",
    func=extract_brand_identity,
)
