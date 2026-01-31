"""
Agno Workflow for onboarding a property.

Orchestrates all extraction steps with proper dependencies and parallelization.
"""

from agno.workflow import Workflow, Step, Parallel
from typing import Optional, Dict, Any
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from agno_tools.extract_property_info_tool import extract_property_info_tool
from agno_tools.extract_images_tool import extract_images_tool
from agno_tools.extract_brand_identity_tool import extract_brand_identity_tool
from agno_tools.extract_amenities_tool import extract_amenities_tool
from agno_tools.extract_floor_plans_tool import extract_floor_plans_tool
from agno_tools.extract_special_offers_tool import extract_special_offers_tool
from agno_tools.extract_reviews_tool import extract_reviews_tool
from agno_tools.find_competitors_tool import find_competitors_tool
from agno_tools.classify_images_tool import classify_images_tool

from tools.cache_manager import get_domain_from_url
from database import CacheRepository, OnboardingRepository


def decide_cache_strategy(
    domain: str,
    use_cache: Optional[bool],
    force_refresh: bool
) -> Dict[str, Any]:
    """
    Decide cache strategy upfront at workflow start.
    
    Args:
        domain: Domain name extracted from URL
        use_cache: User's cache preference (None, True, or False)
        force_refresh: Whether to force refresh
        
    Returns:
        Dictionary with cache preferences to pass to steps
    """
    cache_repo = CacheRepository()
    
    # If force refresh, ignore cache
    if force_refresh:
        return {
            "use_cache": False,
            "force_refresh": True
        }
    
    # Check if markdown cache exists and is valid
    cache_valid = cache_repo.is_cache_valid(domain, "markdown")
    cache_age = cache_repo.get_cache_age(domain, "markdown") if cache_valid else None
    
    # Decision logic
    if use_cache is True:
        # User explicitly wants cache
        if cache_valid:
            return {
                "use_cache": True,
                "force_refresh": False
            }
        else:
            # Cache requested but not valid, refresh
            return {
                "use_cache": False,
                "force_refresh": False
            }
    elif use_cache is False:
        # User explicitly doesn't want cache
        return {
            "use_cache": False,
            "force_refresh": False
        }
    else:
        # use_cache is None - auto-decide based on age
        if cache_valid and cache_age is not None and cache_age < 12:
            # Cache is fresh (< 12 hours), use it
            return {
                "use_cache": True,
                "force_refresh": False
            }
        else:
            # Cache is old or doesn't exist, refresh
            return {
                "use_cache": False,
                "force_refresh": False
            }


def create_progress_tracker(session_id: str, repo: OnboardingRepository):
    """Create a progress tracking function for workflow steps."""
    completed_steps = []
    
    def track_progress(step_name: str, success: bool, error: Optional[str] = None, property_id: Optional[str] = None):
        """Track progress for a workflow step."""
        nonlocal completed_steps
        
        if success:
            if step_name not in completed_steps:
                completed_steps.append(step_name)
            repo.update_progress(
                session_id=session_id,
                status="in_progress",
                completed_steps=completed_steps,
                property_id=property_id,
                clear_current_step=True
            )
        else:
            # Add error
            session = repo.get_session(session_id)
            errors = session.errors.copy() if session.errors else [] if session else []
            errors.append({
                "extraction_type": step_name,
                "error": error or "Unknown error"
            })
            repo.update_progress(
                session_id=session_id,
                status="in_progress",
                current_step=step_name,
                completed_steps=completed_steps,
                errors=errors,
                property_id=property_id
            )
    
    return track_progress


def create_onboard_property_workflow(
    url: str,
    session_id: str,
    use_cache: Optional[bool] = None,
    force_refresh: bool = False
) -> Workflow:
    """
    Create the property onboarding workflow.
    
    Args:
        url: Property website URL
        session_id: Onboarding session ID for progress tracking
        use_cache: Cache preference
        force_refresh: Force refresh flag
        
    Returns:
        Configured Agno Workflow
    """
    # Get domain and decide cache strategy
    domain = get_domain_from_url(url)
    cache_prefs = decide_cache_strategy(domain, use_cache, force_refresh)
    
    # Initialize repositories
    onboarding_repo = OnboardingRepository()
    progress_tracker = create_progress_tracker(session_id, onboarding_repo)
    
    # Step 1: Extract Property Info (must run first)
    def step1_extract_property_info(context: Dict[str, Any]) -> Dict[str, Any]:
        """Step 1: Extract property information and create DB record."""
        try:
            onboarding_repo.update_progress(
                session_id=session_id,
                status="in_progress",
                current_step="property_info"
            )
            
            result = extract_property_info_tool.func(
                url=url,
                use_cache=cache_prefs.get("use_cache"),
                force_refresh=cache_prefs.get("force_refresh", False)
            )
            
            if "error" in result:
                progress_tracker("property_info", False, result.get("error"))
                raise Exception(result.get("error"))
            
            property_id = result.get("property_id")
            progress_tracker("property_info", True, property_id=property_id)
            
            return {
                "property_id": property_id,
                "property_info": result
            }
        except Exception as e:
            progress_tracker("property_info", False, str(e))
            raise
    
    # Step 2: Parallel extractions (5 steps)
    def step2_extract_images(context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract images."""
        try:
            onboarding_repo.update_progress(
                session_id=session_id,
                status="in_progress",
                current_step="images"
            )
            
            result = extract_images_tool.func(
                url=url,
                use_cache=cache_prefs.get("use_cache"),
                force_refresh=cache_prefs.get("force_refresh", False)
            )
            
            if "error" in result:
                progress_tracker("images", False, result.get("error"))
                return {"error": result.get("error")}
            
            progress_tracker("images", True)
            return {"images": result}
        except Exception as e:
            progress_tracker("images", False, str(e))
            return {"error": str(e)}
    
    def step2_extract_brand_identity(context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract brand identity."""
        try:
            onboarding_repo.update_progress(
                session_id=session_id,
                status="in_progress",
                current_step="brand_identity"
            )
            
            result = extract_brand_identity_tool.func(
                url=url,
                use_cache=cache_prefs.get("use_cache"),
                force_refresh=cache_prefs.get("force_refresh", False)
            )
            
            if "error" in result:
                progress_tracker("brand_identity", False, result.get("error"))
                return {"error": result.get("error")}
            
            progress_tracker("brand_identity", True)
            return {"brand_identity": result}
        except Exception as e:
            progress_tracker("brand_identity", False, str(e))
            return {"error": str(e)}
    
    def step2_extract_amenities(context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract amenities."""
        try:
            onboarding_repo.update_progress(
                session_id=session_id,
                status="in_progress",
                current_step="amenities"
            )
            
            result = extract_amenities_tool.func(
                url=url,
                use_cache=cache_prefs.get("use_cache"),
                force_refresh=cache_prefs.get("force_refresh", False)
            )
            
            if "error" in result:
                progress_tracker("amenities", False, result.get("error"))
                return {"error": result.get("error")}
            
            progress_tracker("amenities", True)
            return {"amenities": result}
        except Exception as e:
            progress_tracker("amenities", False, str(e))
            return {"error": str(e)}
    
    def step2_extract_floor_plans(context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract floor plans."""
        try:
            onboarding_repo.update_progress(
                session_id=session_id,
                status="in_progress",
                current_step="floor_plans"
            )
            
            result = extract_floor_plans_tool.func(
                url=url,
                use_cache=cache_prefs.get("use_cache"),
                force_refresh=cache_prefs.get("force_refresh", False)
            )
            
            if "error" in result:
                progress_tracker("floor_plans", False, result.get("error"))
                return {"error": result.get("error")}
            
            progress_tracker("floor_plans", True)
            return {"floor_plans": result}
        except Exception as e:
            progress_tracker("floor_plans", False, str(e))
            return {"error": str(e)}
    
    def step2_extract_special_offers(context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract special offers."""
        try:
            onboarding_repo.update_progress(
                session_id=session_id,
                status="in_progress",
                current_step="special_offers"
            )
            
            result = extract_special_offers_tool.func(
                url=url,
                use_cache=cache_prefs.get("use_cache"),
                force_refresh=cache_prefs.get("force_refresh", False)
            )
            
            if "error" in result:
                progress_tracker("special_offers", False, result.get("error"))
                return {"error": result.get("error")}
            
            progress_tracker("special_offers", True)
            return {"special_offers": result}
        except Exception as e:
            progress_tracker("special_offers", False, str(e))
            return {"error": str(e)}
    
    # Step 3: Sequential extractions (need property address)
    def step3_extract_reviews(context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract reviews (needs property_id from step 1)."""
        try:
            # Get property_id from step 1 result (context accumulates previous step outputs)
            step1_result = context.get("extract_property_info", {})
            property_id = step1_result.get("property_id") or context.get("property_id")
            if not property_id:
                raise Exception("Property ID not available from step 1")
            
            onboarding_repo.update_progress(
                session_id=session_id,
                status="in_progress",
                current_step="reviews"
            )
            
            result = extract_reviews_tool.func(
                property_id=property_id,
                url=url
            )
            
            if "error" in result:
                progress_tracker("reviews", False, result.get("error"))
                return {"error": result.get("error")}
            
            progress_tracker("reviews", True)
            return {"reviews": result}
        except Exception as e:
            progress_tracker("reviews", False, str(e))
            return {"error": str(e)}
    
    def step3_find_competitors(context: Dict[str, Any]) -> Dict[str, Any]:
        """Find competitors (needs property_id from step 1)."""
        try:
            # Get property_id from step 1 result (context accumulates previous step outputs)
            step1_result = context.get("extract_property_info", {})
            property_id = step1_result.get("property_id") or context.get("property_id")
            if not property_id:
                raise Exception("Property ID not available from step 1")
            
            onboarding_repo.update_progress(
                session_id=session_id,
                status="in_progress",
                current_step="competitors"
            )
            
            result = find_competitors_tool.func(
                property_id=property_id
            )
            
            if "error" in result:
                progress_tracker("competitors", False, result.get("error"))
                return {"error": result.get("error")}
            
            progress_tracker("competitors", True)
            return {"competitors": result}
        except Exception as e:
            progress_tracker("competitors", False, str(e))
            return {"error": str(e)}
    
    # Step 2.5: Classify images (depends on images and amenities from parallel step)
    def step2_5_classify_images(context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify images using AI (needs property_id and benefits from amenities)."""
        try:
            # Get property_id from step 1 result
            step1_result = context.get("extract_property_info", {})
            property_id = step1_result.get("property_id") or context.get("property_id")
            if not property_id:
                raise Exception("Property ID not available from step 1")
            
            # Check if images were extracted (should be available from parallel step)
            # But don't fail if images extraction had errors - classification can still run
            # on any images that exist in the database
            
            onboarding_repo.update_progress(
                session_id=session_id,
                status="in_progress",
                current_step="classify_images"
            )
            
            result = classify_images_tool.func(
                property_id=property_id,
                force_reclassify=False,
                batch_size=5
            )
            
            if "error" in result or not result.get("success"):
                error_msg = result.get("error") or "Image classification failed"
                progress_tracker("classify_images", False, error_msg)
                # Don't raise - continue onboarding even if classification fails
                return {"error": error_msg}
            
            progress_tracker("classify_images", True)
            return {"classify_images": result}
        except Exception as e:
            # Log error but don't fail onboarding
            error_msg = str(e)
            progress_tracker("classify_images", False, error_msg)
            return {"error": error_msg}
    
    # Create workflow
    workflow = Workflow(
        name="onboard_property",
        description="Onboard a property by extracting all information from its website",
        steps=[
            Step(
                name="extract_property_info",
                executor=step1_extract_property_info
            ),
            Parallel(
                Step(name="extract_images", executor=step2_extract_images),
                Step(name="extract_brand_identity", executor=step2_extract_brand_identity),
                Step(name="extract_amenities", executor=step2_extract_amenities),
                Step(name="extract_floor_plans", executor=step2_extract_floor_plans),
                Step(name="extract_special_offers", executor=step2_extract_special_offers),
                name="parallel_extractions"
            ),
            Step(
                name="classify_images",
                executor=step2_5_classify_images
            ),
            Step(
                name="extract_reviews",
                executor=step3_extract_reviews
            ),
            Step(
                name="find_competitors",
                executor=step3_find_competitors
            ),
        ]
    )
    
    return workflow
