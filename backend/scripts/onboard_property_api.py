#!/usr/bin/env python3
"""
API wrapper script for onboard_property tool.
Called from Next.js API routes via subprocess.

Usage:
    python3 onboard_property_api.py <session_id> <url> [use_cache] [force_refresh]

Outputs JSON to stdout:
    {"success": true, "property_id": "...", "status": "completed"}
    or
    {"success": false, "error": "error message"}
"""

import os
import sys
import json
import warnings
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Suppress warnings to ensure clean JSON output
warnings.filterwarnings('ignore')

# Load environment variables
env_file = Path(".env.local")
if not env_file.exists():
    env_file = Path(".env")
if not env_file.exists():
    env_file = Path("../.env.local")
if not env_file.exists():
    env_file = Path("../.env")

if env_file.exists():
    load_dotenv(env_file)

# Add backend to path - ensure we can import tools
script_dir = Path(__file__).parent
backend_path = script_dir.parent
sys.path.insert(0, str(backend_path))

# Change to backend directory to ensure relative imports work
os.chdir(backend_path)

try:
    from tools.onboard_property import execute
    from database.onboarding_repository import OnboardingRepository
except ImportError as e:
    output = json.dumps({
        "success": False,
        "error": f"Failed to import modules: {str(e)}"
    })
    print(output, flush=True)
    sys.exit(1)


def create_progress_callback(session_id: str, repo: OnboardingRepository, total_steps: int):
    """Create a progress callback function for the onboarding process."""
    completed_steps = []
    
    def progress_callback(extraction_type: str, success: Optional[bool], error: Optional[str], 
                          property_id: Optional[str], status: str):
        """Callback function called after each extraction step."""
        nonlocal completed_steps
        
        # Handle different statuses
        if status == "in_progress" and success is None:
            # Step is starting
            repo.update_progress(
                session_id=session_id,
                status="in_progress",
                current_step=extraction_type,
                completed_steps=completed_steps,
                property_id=property_id
            )
            return
        
        # Update completed steps if successful
        if success:
            if extraction_type not in completed_steps:
                completed_steps.append(extraction_type)
        elif status == "failed":
            # Add error to errors list
            errors = []
            session = repo.get_session(session_id)
            if session:
                errors = session.errors.copy() if session.errors else []
            errors.append({
                "extraction_type": extraction_type,
                "error": error or "Unknown error"
            })
            repo.update_progress(
                session_id=session_id,
                status="in_progress",
                current_step=extraction_type,
                completed_steps=completed_steps,
                errors=errors,
                property_id=property_id
            )
            return
        
        # Update progress in database for completed step
        if status == "completed":
            repo.update_progress(
                session_id=session_id,
                status="in_progress",  # Still in progress overall
                completed_steps=completed_steps,
                property_id=property_id,
                clear_current_step=True  # Clear current step
            )
    
    return progress_callback


def main():
    """Main function to execute tool and return JSON result."""
    try:
        # Parse arguments
        if len(sys.argv) < 3:
            output = json.dumps({
                "success": False,
                "error": "session_id and url are required"
            })
            print(output, flush=True)
            sys.exit(1)
        
        session_id = sys.argv[1]
        url = sys.argv[2]
        use_cache = None
        force_refresh = False
        
        if len(sys.argv) > 3:
            use_cache_str = sys.argv[3].lower()
            if use_cache_str == "true":
                use_cache = True
            elif use_cache_str == "false":
                use_cache = False
        
        if len(sys.argv) > 4:
            force_refresh_str = sys.argv[4].lower()
            if force_refresh_str == "true":
                force_refresh = True
        
        # Initialize repository
        repo = OnboardingRepository()
        
        # Get session to verify it exists
        session = repo.get_session(session_id)
        if not session:
            output = json.dumps({
                "success": False,
                "error": f"Session {session_id} not found"
            })
            print(output, flush=True)
            sys.exit(1)
        
        # Create progress callback
        from tools.onboard_property import DEFAULT_EXTRACTIONS
        progress_callback = create_progress_callback(session_id, repo, len(DEFAULT_EXTRACTIONS))
        
        # Update session status to in_progress
        repo.update_progress(session_id, status="in_progress", current_step="property_info")
        
        # Execute tool with progress callback
        result = execute(
            {
                "url": url,
                "use_cache": use_cache,
                "force_refresh": force_refresh
            },
            progress_callback=progress_callback
        )
        
        # Check for cache prompts
        if result.get("cache_available"):
            repo.update_progress(
                session_id,
                status="cache_prompt",
                current_step=result.get("extraction_type")
            )
            output = json.dumps({
                "success": False,
                "error": "Cache prompt required",
                "cache_available": True,
                "cache_age_hours": result.get("cache_age_hours"),
                "domain": result.get("domain"),
                "message": result.get("message")
            })
            print(output, flush=True)
            sys.exit(1)
        
        # Check for errors
        if result.get("error"):
            repo.mark_failed(session_id, result.get("error"))
            output = json.dumps({
                "success": False,
                "error": result.get("error")
            })
            print(output, flush=True)
            sys.exit(1)
        
        # Mark session as completed
        property_id = result.get("property_id")
        repo.mark_complete(session_id, property_id)
        
        # Return success result
        output = json.dumps({
            "success": True,
            "property_id": property_id,
            "status": result.get("status", "completed"),
            "summary": result.get("summary", ""),
            "statistics": result.get("statistics", {}),
            "errors": result.get("errors", [])
        })
        print(output, flush=True)
        
    except Exception as e:
        # Try to mark session as failed
        try:
            if len(sys.argv) >= 2:
                session_id = sys.argv[1]
                repo = OnboardingRepository()
                repo.mark_failed(session_id, str(e))
        except:
            pass
        
        output = json.dumps({
            "success": False,
            "error": str(e)
        })
        print(output, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

