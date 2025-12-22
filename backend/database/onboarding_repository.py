"""
Repository for onboarding session-related database operations.

Handles CRUD operations for onboarding sessions.
"""

from typing import Optional, List, Dict, Any
from .supabase_client import get_supabase_client
from .models import OnboardingSession


class OnboardingRepository:
    """Repository for managing onboarding sessions in the database."""
    
    def __init__(self):
        """Initialize repository with Supabase client."""
        self.client = get_supabase_client()
    
    def create_session(self, session: OnboardingSession) -> Optional[str]:
        """
        Create a new onboarding session in the database.
        
        Args:
            session: OnboardingSession instance to create
            
        Returns:
            ID of the created session, or None if creation failed
        """
        try:
            data = session.to_dict()
            response = self.client.table("onboarding_sessions").insert(data).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0].get("id")
            return None
        except Exception as e:
            print(f"Error creating onboarding session: {e}")
            return None
    
    def get_session(self, session_id: str) -> Optional[OnboardingSession]:
        """
        Get onboarding session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            OnboardingSession instance if found, None otherwise
        """
        try:
            response = self.client.table("onboarding_sessions").select("*").eq("id", session_id).execute()
            
            if response.data and len(response.data) > 0:
                return OnboardingSession.from_dict(response.data[0])
            return None
        except Exception as e:
            print(f"Error getting onboarding session: {e}")
            return None
    
    def update_progress(
        self,
        session_id: str,
        status: Optional[str] = None,
        current_step: Optional[str] = None,
        completed_steps: Optional[List[str]] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
        property_id: Optional[str] = None,
        clear_current_step: bool = False
    ) -> bool:
        """
        Update onboarding session progress.
        
        Args:
            session_id: Session ID
            status: New status (e.g., 'started', 'in_progress', 'completed', 'failed')
            current_step: Current step being processed (or None to clear if clear_current_step=True)
            completed_steps: List of completed step names
            errors: List of error dictionaries
            property_id: Property ID if available
            clear_current_step: If True, clear current_step even if it's None
            
        Returns:
            True if update succeeded, False otherwise
        """
        try:
            update_data = {}
            if status is not None:
                update_data["status"] = status
            if clear_current_step:
                update_data["current_step"] = None
            elif current_step is not None:
                update_data["current_step"] = current_step
            if completed_steps is not None:
                update_data["completed_steps"] = completed_steps
            if errors is not None:
                update_data["errors"] = errors
            if property_id is not None:
                update_data["property_id"] = property_id
            
            if not update_data:
                return True  # Nothing to update
            
            response = self.client.table("onboarding_sessions").update(update_data).eq("id", session_id).execute()
            return response.data is not None
        except Exception as e:
            print(f"Error updating onboarding session progress: {e}")
            return False
    
    def mark_complete(self, session_id: str, property_id: Optional[str] = None) -> bool:
        """
        Mark onboarding session as completed.
        
        Args:
            session_id: Session ID
            property_id: Property ID if available
            
        Returns:
            True if update succeeded, False otherwise
        """
        update_data = {"status": "completed"}
        if property_id is not None:
            update_data["property_id"] = property_id
        return self.update_progress(session_id, **update_data)
    
    def mark_failed(self, session_id: str, error: Optional[str] = None) -> bool:
        """
        Mark onboarding session as failed.
        
        Args:
            session_id: Session ID
            error: Error message
            
        Returns:
            True if update succeeded, False otherwise
        """
        update_data = {"status": "failed"}
        if error:
            # Get existing errors and add new one
            session = self.get_session(session_id)
            if session:
                errors = session.errors.copy() if session.errors else []
                errors.append({"message": error, "step": session.current_step})
                update_data["errors"] = errors
        return self.update_progress(session_id, **update_data)

