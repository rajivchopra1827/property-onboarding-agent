"""
Supabase client initialization for FionaFast.

Handles connection to Supabase local instance or hosted instance.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client


def _load_env_from_project_root():
    """Load environment variables from project root .env.local or .env file."""
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env.local"
    if not env_file.exists():
        env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)


def get_supabase_url() -> str:
    """
    Get Supabase URL from environment variables.
    
    Reads from SUPABASE_URL in .env.local file in project root.
    For local development, set SUPABASE_URL=http://127.0.0.1:54321
    For production, set SUPABASE_URL to your Supabase project URL.
    
    Returns:
        Supabase URL string
        
    Raises:
        ValueError: If SUPABASE_URL is not set in .env.local
    """
    # Load from project root .env.local or .env file
    _load_env_from_project_root()
    
    # Check for SUPABASE_URL (required)
    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        return supabase_url
    
    # Fallback to SUPABASE_LOCAL_URL for backward compatibility
    supabase_url = os.getenv("SUPABASE_LOCAL_URL")
    if supabase_url:
        return supabase_url
    
    # No URL found - raise error
    raise ValueError(
        "SUPABASE_URL not found in .env.local file. "
        "Please set SUPABASE_URL in your .env.local file in the project root. "
        "For local development: SUPABASE_URL=http://127.0.0.1:54321"
    )


def get_supabase_key() -> str:
    """
    Get Supabase anon/service key from environment variables.
    
    Reads from SUPABASE_KEY in .env.local file in project root.
    For local development, set SUPABASE_KEY to the anon key from `supabase start` output.
    For production, set SUPABASE_KEY to your Supabase project anon key.
    
    Returns:
        Supabase key string
        
    Raises:
        ValueError: If SUPABASE_KEY is not set in .env.local
    """
    # Load from project root .env.local or .env file
    _load_env_from_project_root()
    
    # Check for SUPABASE_KEY (required)
    supabase_key = os.getenv("SUPABASE_KEY")
    if supabase_key:
        return supabase_key
    
    # Fallback to SUPABASE_LOCAL_KEY for backward compatibility
    supabase_key = os.getenv("SUPABASE_LOCAL_KEY")
    if supabase_key:
        return supabase_key
    
    # No key found - raise error
    raise ValueError(
        "SUPABASE_KEY not found in .env.local file. "
        "Please set SUPABASE_KEY in your .env.local file in the project root. "
        "For local development, get the key from 'supabase start' output."
    )


def get_supabase_client() -> Client:
    """
    Initialize and return Supabase client.
    
    Reads configuration from .env.local file in project root:
    - SUPABASE_URL (required) - Supabase project URL
    - SUPABASE_KEY (required) - Supabase anon or service role key
    
    Returns:
        Supabase client instance
        
    Raises:
        ValueError: If required configuration is missing from .env.local
    """
    url = get_supabase_url()
    key = get_supabase_key()
    
    return create_client(url, key)


