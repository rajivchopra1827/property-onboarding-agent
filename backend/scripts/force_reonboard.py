#!/usr/bin/env python3
"""
Script to force a complete re-onboard of a property.
This bypasses the frontend check and forces all extractions to run again.

Usage:
    python3 force_reonboard.py <url> [force_refresh]
    
Example:
    python3 force_reonboard.py https://www.thehillsatquailrun.com true
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.onboard_property import execute as onboard_property

# Load environment variables from project root .env.local or .env file
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env.local"
if not env_file.exists():
    env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(env_file)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python3 force_reonboard.py <url> [force_refresh]")
        print("Example: python3 force_reonboard.py https://www.thehillsatquailrun.com true")
        sys.exit(1)
    
    url = sys.argv[1].strip()
    force_refresh = False
    
    if len(sys.argv) > 2:
        force_refresh_str = sys.argv[2].lower()
        if force_refresh_str == "true":
            force_refresh = True
    
    print(f"\n{'='*60}")
    print("FORCE RE-ONBOARDING PROPERTY")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Force Refresh: {force_refresh}")
    print(f"{'='*60}\n")
    
    # Force complete re-onboard by running all extractions
    # Note: This will overwrite existing data
    result = onboard_property({
        "url": url,
        "force_refresh": force_refresh,
        "use_cache": False if force_refresh else None,
        # Don't use resume=True - we want to run ALL extractions
    })
    
    print(f"\n{'='*60}")
    print("ONBOARDING COMPLETE")
    print(f"{'='*60}")
    print(f"Status: {result.get('status', 'unknown')}")
    if result.get('property_id'):
        print(f"Property ID: {result.get('property_id')}")
    print(f"\n{result.get('summary', '')}")
    
    if result.get('errors'):
        print(f"\nErrors encountered: {len(result.get('errors', []))}")
        for error in result.get('errors', []):
            print(f"  - {error.get('extraction_type')}: {error.get('error')}")


if __name__ == "__main__":
    main()


