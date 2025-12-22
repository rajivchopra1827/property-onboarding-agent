#!/usr/bin/env python3
"""
Helper script to check what extraction types are missing for a property.

Usage:
    python scripts/check_missing_extractions.py <url>
    python scripts/check_missing_extractions.py --property-id <property_id>
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.onboard_property import get_missing_extractions, DEFAULT_EXTRACTIONS
from dotenv import load_dotenv

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
        print("Usage:")
        print("  python scripts/check_missing_extractions.py <url>")
        print("  python scripts/check_missing_extractions.py --property-id <property_id>")
        sys.exit(1)
    
    url = None
    property_id = None
    
    if sys.argv[1] == "--property-id" and len(sys.argv) > 2:
        property_id = sys.argv[2]
    elif sys.argv[1].startswith("http"):
        url = sys.argv[1]
    else:
        print("Error: Please provide a valid URL or use --property-id <id>")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print("CHECKING MISSING EXTRACTIONS")
    print(f"{'='*60}")
    
    if property_id:
        print(f"Property ID: {property_id}")
        missing = get_missing_extractions(property_id=property_id)
    else:
        print(f"URL: {url}")
        missing = get_missing_extractions(url=url)
    
    print(f"\nMissing Extractions ({len(missing)}):")
    if missing == DEFAULT_EXTRACTIONS:
        print("  → No existing data found. All extractions need to be run.")
        print(f"  → Missing: {', '.join(missing)}")
    elif len(missing) == 0:
        print("  ✓ All extractions already completed!")
    else:
        for ext in missing:
            print(f"  - {ext}")
        print(f"\nTo resume onboarding, run:")
        print(f"  onboard_property(url=\"{url}\", extractions={missing}, resume=True)")
        print(f"\nOr use the resume parameter:")
        print(f"  onboard_property(url=\"{url}\", resume=True)")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()


