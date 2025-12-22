"""
Tool for fully onboarding a property by orchestrating all extraction tools.

This tool runs all property extraction tools in sequence to fully onboard
a property from a website URL. It handles errors gracefully, provides
progress updates, and returns comprehensive results.
"""

from typing import Dict, Any, List, Optional, Callable
import json
import time
from .extract_property_information import execute as extract_property_info
from .extract_website_images import execute as extract_images
from .extract_brand_identity import execute as extract_branding
from .extract_amenities import execute as extract_amenities
from .extract_floor_plans import execute as extract_floor_plans
from .extract_special_offers import execute as extract_offers
from .extract_reviews import execute as extract_reviews
from .find_competitors import execute as find_competitors

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
            onboard_property(url="https://example.com", extractions=missing)
    """
    from database import PropertyRepository
    
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
    
    # Ensure property_info is included if property exists (it should already be there, but double-check)
    # Actually, if property exists, property_info was already extracted, so we don't need to add it
    
    # Return missing extractions in the correct order (matching DEFAULT_EXTRACTIONS order)
    ordered_missing = [ext for ext in DEFAULT_EXTRACTIONS if ext in missing]
    
    return ordered_missing


def get_tool_definition():
    """Returns the tool definition for OpenAI function calling."""
    return {
        "type": "function",
        "function": {
            "name": "onboard_property",
            "description": "Fully onboard a property by running all extraction tools in sequence. Extracts property information, images, brand identity, amenities, floor plans, special offers, reviews, and finds nearby competitors. Handles errors gracefully and continues processing even if individual extractions fail. Returns comprehensive summary and detailed results. Use resume=True to automatically detect and run only missing extractions (useful for resuming partial onboarding).",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the property website to onboard"
                    },
                    "use_cache": {
                        "type": "boolean",
                        "description": "Whether to use cached data if available. If None/not provided, individual tools will handle cache prompting. If True, uses cache. If False, forces fresh extraction."
                    },
                    "force_refresh": {
                        "type": "boolean",
                        "description": "Force a fresh extraction even if cache exists. Defaults to False.",
                        "default": False
                    },
                    "extractions": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["property_info", "images", "brand_identity", "amenities", "floor_plans", "special_offers", "reviews", "competitors"]
                        },
                        "description": "List of extraction types to run. If not provided, runs all extractions. Options: property_info, images, brand_identity, amenities, floor_plans, special_offers, reviews, competitors"
                    },
                    "resume": {
                        "type": "boolean",
                        "description": "If True, automatically checks what data already exists for this property and only runs missing extractions. Useful for resuming a partial onboarding. Defaults to False.",
                        "default": False
                    }
                },
                "required": ["url"]
            }
        }
    }


def validate_url(url: str) -> bool:
    """
    Validate that URL is provided and looks valid.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL appears valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    if not url:
        return False
    
    # Basic validation - should start with http:// or https://
    return url.startswith("http://") or url.startswith("https://")


def run_extraction(
    extraction_type: str,
    url: str,
    use_cache: Optional[bool],
    force_refresh: bool,
    property_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run a single extraction tool.
    
    Args:
        extraction_type: Type of extraction to run
        url: Property website URL
        use_cache: Cache preference
        force_refresh: Whether to force refresh
        property_id: Optional property ID (for logging)
        
    Returns:
        Dictionary with result and status
    """
    extraction_name = extraction_type.replace("_", " ").title()
    print(f"\n{'='*60}")
    print(f"Running: {extraction_name}")
    print(f"{'='*60}")
    
    # Prepare arguments for the extraction tool
    args = {"url": url}
    if use_cache is not None:
        args["use_cache"] = use_cache
    if force_refresh:
        args["force_refresh"] = force_refresh
    
    # For reviews and competitors extraction, also pass property_id if available
    if extraction_type in ["reviews", "competitors"] and property_id:
        args["property_id"] = property_id
    
    try:
        # Map extraction types to their execute functions
        extraction_map = {
            "property_info": extract_property_info,
            "images": extract_images,
            "brand_identity": extract_branding,
            "amenities": extract_amenities,
            "floor_plans": extract_floor_plans,
            "special_offers": extract_offers,
            "reviews": extract_reviews,
            "competitors": find_competitors
        }
        
        if extraction_type not in extraction_map:
            return {
                "success": False,
                "error": f"Unknown extraction type: {extraction_type}",
                "result": None
            }
        
        # Execute the extraction
        # #region agent log
        _log("onboard_property.py:run_extraction:before_execute", "Before extraction execute", {
            "extraction_type": extraction_type,
            "has_url": bool(args.get("url"))
        }, "H6")
        # #endregion
        
        result = extraction_map[extraction_type](args)
        
        # #region agent log
        _log("onboard_property.py:run_extraction:after_execute", "After extraction execute", {
            "extraction_type": extraction_type,
            "has_error": "error" in result,
            "error": result.get("error") if "error" in result else None,
            "has_cache_available": "cache_available" in result
        }, "H6")
        # #endregion
        
        # Check for errors
        if "error" in result:
            return {
                "success": False,
                "error": result.get("error"),
                "result": result
            }
        
        # Check for cache prompts (these are not errors, but need user interaction)
        if "cache_available" in result and result.get("cache_available"):
            return {
                "success": False,
                "error": "Cache prompt required",
                "cache_prompt": True,
                "cache_info": {
                    "cache_age_hours": result.get("cache_age_hours"),
                    "domain": result.get("domain"),
                    "message": result.get("message")
                },
                "result": result
            }
        
        # Success
        return {
            "success": True,
            "error": None,
            "result": result
        }
        
    except Exception as e:
        error_msg = str(e)
        # #region agent log
        _log("onboard_property.py:run_extraction:exception", "Exception in run_extraction", {
            "extraction_type": extraction_type,
            "error": error_msg,
            "error_type": type(e).__name__
        }, "H6")
        # #endregion
        print(f"⚠ Error during {extraction_name}: {error_msg}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": error_msg,
            "result": None
        }


def extract_statistics(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract statistics from results.
    
    Args:
        results: Dictionary of extraction results
        
    Returns:
        Dictionary with statistics
    """
    stats = {
        "images_count": 0,
        "building_amenities_count": 0,
        "apartment_amenities_count": 0,
        "floor_plans_count": 0,
        "special_offers_count": 0,
        "reviews_count": 0,
        "overall_rating": None,
        "competitors_count": 0,
        "has_branding": False,
        "has_property_info": False
    }
    
    # Count images
    if "images" in results:
        images_result = results["images"].get("result", {})
        if images_result and "images" in images_result:
            stats["images_count"] = len(images_result.get("images", []))
    
    # Count amenities
    if "amenities" in results:
        amenities_result = results["amenities"].get("result", {})
        if amenities_result:
            stats["building_amenities_count"] = len(amenities_result.get("building_amenities", []))
            stats["apartment_amenities_count"] = len(amenities_result.get("apartment_amenities", []))
    
    # Count floor plans
    if "floor_plans" in results:
        floor_plans_result = results["floor_plans"].get("result", {})
        if floor_plans_result:
            stats["floor_plans_count"] = len(floor_plans_result.get("floor_plans", []))
    
    # Count special offers
    if "special_offers" in results:
        offers_result = results["special_offers"].get("result", {})
        if offers_result:
            stats["special_offers_count"] = len(offers_result.get("offers", []))
    
    # Count reviews
    if "reviews" in results:
        reviews_result = results["reviews"].get("result", {})
        if reviews_result:
            stats["reviews_count"] = reviews_result.get("review_count", 0)
            stats["overall_rating"] = reviews_result.get("overall_rating")
    
    # Count competitors
    if "competitors" in results:
        competitors_result = results["competitors"].get("result", {})
        if competitors_result:
            stats["competitors_count"] = competitors_result.get("competitors_added", 0)
    
    # Check for branding
    if "brand_identity" in results:
        branding_result = results["brand_identity"].get("result", {})
        if branding_result and branding_result.get("branding_data"):
            stats["has_branding"] = True
    
    # Check for property info
    if "property_info" in results:
        prop_info_result = results["property_info"].get("result", {})
        if prop_info_result and prop_info_result.get("property_name"):
            stats["has_property_info"] = True
    
    return stats


def generate_summary(results: Dict[str, Any], errors: List[Dict[str, Any]], statistics: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of the onboarding process.
    
    Args:
        results: Dictionary of extraction results
        errors: List of errors encountered
        statistics: Statistics dictionary
        
    Returns:
        Summary string
    """
    lines = []
    lines.append("\n" + "="*60)
    lines.append("PROPERTY ONBOARDING SUMMARY")
    lines.append("="*60)
    
    # Overall status
    total_extractions = len(results)
    successful_extractions = sum(1 for r in results.values() if r.get("success"))
    failed_extractions = total_extractions - successful_extractions
    
    if failed_extractions == 0:
        status = "✓ SUCCESS - All extractions completed successfully"
    elif successful_extractions > 0:
        status = f"⚠ PARTIAL SUCCESS - {successful_extractions}/{total_extractions} extractions succeeded"
    else:
        status = "✗ FAILED - No extractions succeeded"
    
    lines.append(f"\nStatus: {status}")
    
    # Extraction results
    lines.append(f"\nExtraction Results:")
    extraction_names = {
        "property_info": "Property Information",
        "images": "Images",
        "brand_identity": "Brand Identity",
        "amenities": "Amenities",
        "floor_plans": "Floor Plans",
        "special_offers": "Special Offers",
        "reviews": "Reviews",
        "competitors": "Competitors"
    }
    
    for extraction_type, result in results.items():
        name = extraction_names.get(extraction_type, extraction_type.replace("_", " ").title())
        if result.get("success"):
            lines.append(f"  ✓ {name}: Success")
        else:
            error = result.get("error", "Unknown error")
            lines.append(f"  ✗ {name}: Failed - {error}")
    
    # Statistics
    lines.append(f"\nStatistics:")
    if statistics.get("has_property_info"):
        lines.append(f"  • Property information extracted")
    if statistics.get("images_count", 0) > 0:
        lines.append(f"  • {statistics['images_count']} images extracted")
    if statistics.get("building_amenities_count", 0) > 0:
        lines.append(f"  • {statistics['building_amenities_count']} building amenities")
    if statistics.get("apartment_amenities_count", 0) > 0:
        lines.append(f"  • {statistics['apartment_amenities_count']} apartment amenities")
    if statistics.get("floor_plans_count", 0) > 0:
        lines.append(f"  • {statistics['floor_plans_count']} floor plans")
    if statistics.get("special_offers_count", 0) > 0:
        lines.append(f"  • {statistics['special_offers_count']} special offers")
    if statistics.get("reviews_count", 0) > 0:
        rating = statistics.get("overall_rating")
        if rating:
            lines.append(f"  • {statistics['reviews_count']} reviews (rating: {rating:.2f}/5.0)")
        else:
            lines.append(f"  • {statistics['reviews_count']} reviews")
    if statistics.get("competitors_count", 0) > 0:
        lines.append(f"  • {statistics['competitors_count']} competitors found")
    if statistics.get("has_branding"):
        lines.append(f"  • Brand identity extracted")
    
    # Errors
    if errors:
        lines.append(f"\nErrors Encountered ({len(errors)}):")
        for i, error in enumerate(errors, 1):
            extraction_type = error.get("extraction_type", "Unknown")
            error_msg = error.get("error", "Unknown error")
            lines.append(f"  {i}. {extraction_type}: {error_msg}")
    
    lines.append("\n" + "="*60)
    
    return "\n".join(lines)


def execute(arguments: Dict[str, Any], progress_callback: Optional[Callable[[str, Optional[bool], Optional[str], Optional[str], str], None]] = None) -> Dict[str, Any]:
    """
    Execute the onboard_property tool.
    
    Orchestrates all extraction tools to fully onboard a property.
    
    Args:
        arguments: Dictionary containing tool arguments
            - url (str): The URL of the property website
            - use_cache (bool, optional): Cache preference
            - force_refresh (bool, optional): Force fresh extraction
            - extractions (list, optional): List of extraction types to run
            - resume (bool, optional): If True, automatically detect and run only missing extractions
        progress_callback: Optional callback function to call after each extraction step.
            Called with (extraction_type, success, error, property_id)
        
    Returns:
        Dictionary with onboarding results
    """
    url = arguments.get("url", "").strip()
    use_cache = arguments.get("use_cache")
    force_refresh = arguments.get("force_refresh", False)
    extractions = arguments.get("extractions")
    resume = arguments.get("resume", False)
    
    # Validate URL
    if not validate_url(url):
        return {
            "error": "Invalid URL provided. URL must be a non-empty string starting with http:// or https://",
            "status": "failed",
            "property_id": None,
            "summary": "",
            "results": {},
            "errors": [],
            "statistics": {}
        }
    
    # Handle resume mode - automatically detect missing extractions
    if resume:
        print(f"\n[Resume Mode] Checking what data already exists for this property...")
        missing_extractions = get_missing_extractions(url=url)
        
        # Always ensure property_info is included if property doesn't exist
        # (get_missing_extractions returns all DEFAULT_EXTRACTIONS if property not found)
        if missing_extractions == DEFAULT_EXTRACTIONS:
            # Property doesn't exist, ensure property_info runs first
            if "property_info" not in missing_extractions:
                missing_extractions.insert(0, "property_info")
        
        if not extractions:
            # No extractions specified, use detected missing ones
            extractions = missing_extractions
            if missing_extractions == DEFAULT_EXTRACTIONS:
                print(f"  → No existing data found. Will run all extractions.")
            else:
                print(f"  → Found existing data. Will run only missing extractions: {', '.join(missing_extractions)}")
        else:
            # Extractions specified, but still check and warn
            specified_set = set(extractions)
            missing_set = set(missing_extractions)
            already_complete = specified_set - missing_set
            
            # Ensure property_info is included if property doesn't exist
            from database import PropertyRepository
            repo = PropertyRepository()
            property_obj = repo.get_property_by_website_url(url)
            if not property_obj and "property_info" not in extractions:
                extractions.insert(0, "property_info")
                print(f"  → Property not found. Adding property_info to run first.")
            
            if already_complete:
                print(f"  ⚠ Warning: Some specified extractions already exist: {', '.join(already_complete)}")
                print(f"  → Will run: {', '.join(extractions)}")
            else:
                print(f"  → Will run specified extractions: {', '.join(extractions)}")
    
    # Determine which extractions to run
    if extractions:
        # Validate extraction types
        valid_extractions = set(DEFAULT_EXTRACTIONS)
        requested_extractions = set(extractions)
        invalid_extractions = requested_extractions - valid_extractions
        
        if invalid_extractions:
            return {
                "error": f"Invalid extraction types: {', '.join(invalid_extractions)}. Valid types: {', '.join(DEFAULT_EXTRACTIONS)}",
                "status": "failed",
                "property_id": None,
                "summary": "",
                "results": {},
                "errors": [],
                "statistics": {}
            }
        
        extractions_to_run = [e for e in DEFAULT_EXTRACTIONS if e in requested_extractions]
    else:
        extractions_to_run = DEFAULT_EXTRACTIONS.copy()
    
    if not extractions_to_run:
        return {
            "error": "No valid extractions specified",
            "status": "failed",
            "property_id": None,
            "summary": "",
            "results": {},
            "errors": [],
            "statistics": {}
        }
    
    print(f"\n{'='*60}")
    print(f"PROPERTY ONBOARDING")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Extractions to run: {', '.join(extractions_to_run)}")
    print(f"Cache preference: {use_cache if use_cache is not None else 'Prompt if available'}")
    print(f"Force refresh: {force_refresh}")
    print(f"{'='*60}\n")
    
    # Track results and errors
    results = {}
    errors = []
    property_id = None
    completed_steps = []
    cache_created = False  # Track if cache was created in first step
    
    # Run extractions in sequence
    for i, extraction_type in enumerate(extractions_to_run, 1):
        print(f"\n[{i}/{len(extractions_to_run)}] Starting {extraction_type}...")
        
        # Call progress callback to indicate step is starting
        if progress_callback:
            try:
                progress_callback(extraction_type, None, None, property_id, "in_progress")
            except Exception as e:
                print(f"⚠ Warning: Progress callback error: {e}")
        
        # Determine cache preference for this step
        # If force_refresh is True, only apply it to the first step (to create fresh cache)
        # Subsequent steps should use the cache that was just created
        step_force_refresh = force_refresh if i == 1 else False
        step_use_cache = None
        
        # Check if cache exists (after first step, cache should be available)
        from .cache_manager import get_domain_from_url, is_cache_valid
        domain = get_domain_from_url(url)
        cache_exists = is_cache_valid(domain)
        
        # After first step completes, if cache exists, subsequent steps should use it
        # (unless force_refresh was explicitly set globally, which only applies to first step)
        if i > 1:
            if cache_exists and not force_refresh:
                # Cache was created in first step, use it for subsequent steps
                step_use_cache = True
                step_force_refresh = False
            elif use_cache is not None:
                step_use_cache = use_cache
        else:
            # First step - use provided preferences
            if use_cache is not None:
                step_use_cache = use_cache
        
        # Mark cache as created after first step completes if it exists
        if i == 1 and cache_exists:
            cache_created = True
        
        # #region agent log
        _log("onboard_property.py:execute:before_step", "Before extraction step", {
            "extraction_type": extraction_type,
            "step_number": i,
            "step_use_cache": step_use_cache,
            "step_force_refresh": step_force_refresh,
            "cache_created": cache_created
        }, "H7")
        # #endregion
        
        # Run the extraction
        extraction_result = run_extraction(
            extraction_type=extraction_type,
            url=url,
            use_cache=step_use_cache,
            force_refresh=step_force_refresh,
            property_id=property_id
        )
        
        # Store result
        results[extraction_type] = extraction_result
        
        # After first step, check if cache was created
        if i == 1:
            from .cache_manager import get_domain_from_url, is_cache_valid
            domain = get_domain_from_url(url)
            if is_cache_valid(domain):
                cache_created = True
                # #region agent log
                _log("onboard_property.py:execute:cache_created", "Cache created after first step", {
                    "extraction_type": extraction_type,
                    "domain": domain
                }, "H7")
                # #endregion
        
        # Handle cache prompts (special case - not an error, but needs user interaction)
        if extraction_result.get("cache_prompt"):
            cache_info = extraction_result.get("cache_info", {})
            if progress_callback:
                try:
                    progress_callback(extraction_type, False, "Cache prompt required", property_id, "cache_prompt")
                except Exception as e:
                    print(f"⚠ Warning: Progress callback error: {e}")
            return {
                "cache_available": True,
                "cache_age_hours": cache_info.get("cache_age_hours"),
                "domain": cache_info.get("domain"),
                "message": cache_info.get("message"),
                "extraction_type": extraction_type,
                "status": "cache_prompt",
                "property_id": property_id,
                "summary": f"Cache available for {extraction_type}. User interaction required.",
                "results": results,
                "errors": errors,
                "statistics": {}
            }
        
        # Track errors
        if not extraction_result.get("success"):
            error_info = {
                "extraction_type": extraction_type,
                "error": extraction_result.get("error", "Unknown error")
            }
            errors.append(error_info)
            print(f"⚠ {extraction_type} failed: {extraction_result.get('error')}")
            
            # Call progress callback for failed step
            if progress_callback:
                try:
                    progress_callback(extraction_type, False, extraction_result.get("error"), property_id, "failed")
                except Exception as e:
                    print(f"⚠ Warning: Progress callback error: {e}")
        else:
            print(f"✓ {extraction_type} completed successfully")
            completed_steps.append(extraction_type)
            
            # Extract property_id from property_info result if available
            if extraction_type == "property_info" and extraction_result.get("result"):
                # Property info tool saves to database and returns the data
                # We need to get the property_id from the database
                try:
                    from database import PropertyRepository
                    property_repo = PropertyRepository()
                    property_obj = property_repo.get_property_by_website_url(url)
                    if property_obj and property_obj.id:
                        property_id = property_obj.id
                        print(f"✓ Property ID: {property_id}")
                except Exception as e:
                    print(f"⚠ Warning: Could not retrieve property ID: {e}")
            
            # Call progress callback for successful step
            if progress_callback:
                try:
                    progress_callback(extraction_type, True, None, property_id, "completed")
                except Exception as e:
                    print(f"⚠ Warning: Progress callback error: {e}")
    
    # Extract statistics
    statistics = extract_statistics(results)
    
    # Generate summary
    summary = generate_summary(results, errors, statistics)
    print(summary)
    
    # Determine overall status
    if len(errors) == 0:
        status = "success"
    elif len(errors) < len(extractions_to_run):
        status = "partial"
    else:
        status = "failed"
    
    # Prepare detailed results (clean up for return)
    detailed_results = {}
    for extraction_type, result in results.items():
        detailed_results[extraction_type] = {
            "success": result.get("success", False),
            "error": result.get("error"),
            "data": result.get("result")
        }
    
    return {
        "status": status,
        "property_id": property_id,
        "summary": summary,
        "results": detailed_results,
        "errors": errors,
        "statistics": statistics
    }

