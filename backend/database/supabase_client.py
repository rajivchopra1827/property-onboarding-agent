"""
Supabase client initialization for FionaFast.

Handles connection to Supabase local instance or hosted instance.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client


def get_supabase_url() -> str:
    """
    Get Supabase URL from environment variables.
    
    For local development, this is typically: http://127.0.0.1:54321
    For production, this would be your Supabase project URL.
    
    Returns:
        Supabase URL string
    """
    # Try to load from .env.local first, then .env
    env_file = Path(".env.local")
    if not env_file.exists():
        env_file = Path(".env")
    
    if env_file.exists():
        load_dotenv(env_file)
    
    # Check for SUPABASE_URL first (for local or production)
    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        return supabase_url
    
    # Default to local Supabase instance
    # This will be set when you run `supabase start`
    return os.getenv("SUPABASE_LOCAL_URL", "http://127.0.0.1:54321")


def get_supabase_key() -> str:
    """
    Get Supabase anon/service key from environment variables.
    
    For local development, this is typically the anon key from `supabase start` output.
    For production, this would be your Supabase project anon key.
    
    Returns:
        Supabase key string
    """
    # Try to load from .env.local first, then .env
    env_file = Path(".env.local")
    if not env_file.exists():
        env_file = Path(".env")
    
    if env_file.exists():
        load_dotenv(env_file)
    
    # Check for SUPABASE_KEY first (for local or production)
    supabase_key = os.getenv("SUPABASE_KEY")
    if supabase_key:
        return supabase_key
    
    # Default to local Supabase anon key
    # This will be set when you run `supabase start`
    # Default local anon key (can be overridden via env var)
    return os.getenv(
        "SUPABASE_LOCAL_KEY",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
    )


def get_supabase_client() -> Client:
    """
    Initialize and return Supabase client.
    
    Reads configuration from environment variables:
    - SUPABASE_URL or SUPABASE_LOCAL_URL (defaults to http://127.0.0.1:54321)
    - SUPABASE_KEY or SUPABASE_LOCAL_KEY (defaults to local demo key)
    
    Returns:
        Supabase client instance
        
    Raises:
        ValueError: If required configuration is missing
    """
    url = get_supabase_url()
    key = get_supabase_key()
    
    if not url:
        raise ValueError(
            "SUPABASE_URL or SUPABASE_LOCAL_URL not found. "
            "Please set it in your environment variables or run 'supabase start' to get local values."
        )
    
    if not key:
        raise ValueError(
            "SUPABASE_KEY or SUPABASE_LOCAL_KEY not found. "
            "Please set it in your environment variables or run 'supabase start' to get local values."
        )
    
    return create_client(url, key)

