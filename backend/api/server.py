"""
FastAPI server for property onboarding workflows.

Provides API endpoints to trigger and monitor Agno workflows.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from workflows.onboard_property_workflow import create_onboard_property_workflow
from workflows.utils import get_missing_extractions
from database import OnboardingRepository, PropertyRepository
from database.models import OnboardingSession

app = FastAPI(title="Property Onboarding API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OnboardRequest(BaseModel):
    """Request model for onboarding a property."""
    url: HttpUrl
    force_reonboard: Optional[bool] = False


class OnboardResponse(BaseModel):
    """Response model for onboarding request."""
    success: bool
    session_id: Optional[str] = None
    property_id: Optional[str] = None
    status: str
    message: str


class StatusResponse(BaseModel):
    """Response model for status check."""
    session_id: str
    status: str
    current_step: Optional[str] = None
    completed_steps: list
    errors: list
    property_id: Optional[str] = None


class MissingExtractionsResponse(BaseModel):
    """Response model for missing extractions check."""
    property_id: str
    missing_extractions: list
    all_complete: bool


async def run_workflow_async(
    workflow,
    session_id: str,
    onboarding_repo: OnboardingRepository
):
    """Run workflow asynchronously and update session status."""
    try:
        # Run workflow
        result = await asyncio.to_thread(workflow.run)
        
        # Get final status
        session = onboarding_repo.get_session(session_id)
        if session:
            # Check if workflow completed successfully
            errors = session.errors or []
            if len(errors) == 0:
                onboarding_repo.mark_complete(
                    session_id=session_id,
                    property_id=session.property_id
                )
            else:
                # Partial success or failure
                onboarding_repo.update_progress(
                    session_id=session_id,
                    status="completed" if len(session.completed_steps) > 0 else "failed"
                )
    except Exception as e:
        # Mark session as failed
        onboarding_repo.mark_failed(session_id, str(e))


@app.post("/api/onboard", response_model=OnboardResponse)
async def onboard_property(
    request: OnboardRequest,
    background_tasks: BackgroundTasks
):
    """
    Start onboarding workflow for a property.
    
    Creates a session and runs the workflow asynchronously.
    """
    url = str(request.url)
    onboarding_repo = OnboardingRepository()
    
    # Check if property already exists (skip if force_reonboard is true)
    # Use timeout to prevent hanging on slow database queries
    if not request.force_reonboard:
        try:
            from database import PropertyRepository
            property_repo = PropertyRepository()
            # Add timeout to prevent hanging (5 seconds max)
            existing_property = await asyncio.wait_for(
                asyncio.to_thread(property_repo.get_property_by_website_url, url),
                timeout=5.0
            )
            
            if existing_property:
                return OnboardResponse(
                    success=True,
                    session_id=None,
                    property_id=existing_property.id,
                    status="already_exists",
                    message="Property already exists"
                )
        except asyncio.TimeoutError:
            # If check times out, proceed with onboarding anyway
            print(f"Warning: Property existence check timed out for {url}, proceeding with onboarding")
        except Exception as e:
            # If check fails, proceed with onboarding anyway
            print(f"Warning: Error checking if property exists: {e}, proceeding with onboarding")
    
    # Create onboarding session
    session = OnboardingSession(
        url=url,
        status="started",
        current_step=None,
        completed_steps=[],
        errors=[]
    )
    session_id = onboarding_repo.create_session(session)
    
    if not session_id:
        raise HTTPException(
            status_code=500,
            detail="Failed to create onboarding session"
        )
    
    # Create workflow
    workflow = create_onboard_property_workflow(
        url=url,
        session_id=session_id,
        use_cache=None,  # Auto-decide based on cache age
        force_refresh=request.force_reonboard
    )
    
    # Run workflow in background
    background_tasks.add_task(
        run_workflow_async,
        workflow,
        session_id,
        onboarding_repo
    )
    
    return OnboardResponse(
        success=True,
        session_id=session_id,
        property_id=None,
        status="started",
        message="Onboarding started"
    )


@app.get("/api/onboard/{session_id}/status", response_model=StatusResponse)
async def get_onboarding_status(session_id: str):
    """Get the status of an onboarding session."""
    onboarding_repo = OnboardingRepository()
    session = onboarding_repo.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    return StatusResponse(
        session_id=session_id,
        status=session.status,
        current_step=session.current_step,
        completed_steps=session.completed_steps or [],
        errors=session.errors or [],
        property_id=session.property_id
    )


@app.get("/api/properties/{property_id}/missing-extractions", response_model=MissingExtractionsResponse)
async def get_missing_extractions_for_property(property_id: str):
    """
    Get list of missing extraction types for a property.
    
    Useful for checking what data still needs to be extracted.
    """
    property_repo = PropertyRepository()
    property_obj = property_repo.get_property_by_id(property_id)
    
    if not property_obj:
        raise HTTPException(
            status_code=404,
            detail=f"Property {property_id} not found"
        )
    
    missing = get_missing_extractions(property_id=property_id)
    
    return MissingExtractionsResponse(
        property_id=property_id,
        missing_extractions=missing,
        all_complete=len(missing) == 0
    )


@app.post("/api/properties/{property_id}/force-reonboard", response_model=OnboardResponse)
async def force_reonboard_property(
    property_id: str,
    background_tasks: BackgroundTasks
):
    """
    Force re-onboarding for an existing property.
    
    This will re-run all extractions even if data already exists.
    Useful for refreshing stale data or fixing errors.
    """
    property_repo = PropertyRepository()
    property_obj = property_repo.get_property_by_id(property_id)
    
    if not property_obj:
        raise HTTPException(
            status_code=404,
            detail=f"Property {property_id} not found"
        )
    
    if not property_obj.website_url:
        raise HTTPException(
            status_code=400,
            detail="Property does not have a website URL"
        )
    
    url = property_obj.website_url
    onboarding_repo = OnboardingRepository()
    
    # Create onboarding session
    session = OnboardingSession(
        url=url,
        status="started",
        current_step=None,
        completed_steps=[],
        errors=[]
    )
    session_id = onboarding_repo.create_session(session)
    
    if not session_id:
        raise HTTPException(
            status_code=500,
            detail="Failed to create onboarding session"
        )
    
    # Create workflow with force_refresh=True
    workflow = create_onboard_property_workflow(
        url=url,
        session_id=session_id,
        use_cache=False,  # Don't use cache for force reonboard
        force_refresh=True
    )
    
    # Run workflow in background
    background_tasks.add_task(
        run_workflow_async,
        workflow,
        session_id,
        onboarding_repo
    )
    
    return OnboardResponse(
        success=True,
        session_id=session_id,
        property_id=property_id,
        status="started",
        message="Force re-onboarding started"
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
