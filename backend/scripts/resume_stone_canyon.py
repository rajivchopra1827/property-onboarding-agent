#!/usr/bin/env python3
"""
Helper script to resume onboarding for Stone Canyon Apartments.
"""

import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.onboard_property import get_missing_extractions, execute as onboard_property, DEFAULT_EXTRACTIONS
from database import PropertyRepository
from dotenv import load_dotenv

# Load environment variables from project root .env.local or .env file
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env.local"
if not env_file.exists():
    env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(env_file)


def find_stone_canyon():
    """Find Stone Canyon property in database."""
    repo = PropertyRepository()
    
    # Try to find by name (partial match)
    property_obj = repo.get_property_by_name("Stone Canyon")
    
    if property_obj:
        return property_obj
    
    # If not found, try common variations
    variations = [
        "Stone Canyon Apartments",
        "Live at Stone Canyon",
        "Stone Canyon"
    ]
    
    for name in variations:
        prop = repo.get_property_by_name(name)
        if prop:
            return prop
    
    return None


def main():
    """Main function."""
    print(f"\n{'='*60}")
    print("RESUMING ONBOARDING FOR STONE CANYON APARTMENTS")
    print(f"{'='*60}\n")
    
    # Find the property
    print("Searching for Stone Canyon property in database...")
    property_obj = find_stone_canyon()
    
    if not property_obj:
        print("❌ Property not found in database.")
        print("\nPlease provide the website URL:")
        url = input("URL: ").strip()
        if not url:
            print("Error: URL required")
            sys.exit(1)
        
        print(f"\nChecking missing extractions for: {url}")
        missing = get_missing_extractions(url=url)
    else:
        print(f"✓ Found property: {property_obj.property_name}")
        print(f"  Property ID: {property_obj.id}")
        print(f"  URL: {property_obj.website_url}")
        
        print(f"\nChecking what extractions are missing...")
        missing = get_missing_extractions(property_id=property_obj.id, url=property_obj.website_url)
    
    print(f"\n{'='*60}")
    print("MISSING EXTRACTIONS")
    print(f"{'='*60}")
    
    if missing == DEFAULT_EXTRACTIONS:
        print("  → No existing data found. All extractions need to be run.")
        print(f"  → Missing: {', '.join(missing)}")
    elif len(missing) == 0:
        print("  ✓ All extractions already completed!")
        sys.exit(0)
    else:
        print(f"  Found {len(missing)} missing extraction(s):")
        for ext in missing:
            print(f"    - {ext}")
    
    # Ask user if they want to resume
    print(f"\n{'='*60}")
    response = input("\nResume onboarding with missing extractions? (y/n): ").strip().lower()
    
    if response not in ['y', 'yes']:
        print("Cancelled.")
        sys.exit(0)
    
    # Resume onboarding
    url = property_obj.website_url if property_obj else url
    print(f"\n{'='*60}")
    print("RESUMING ONBOARDING")
    print(f"{'='*60}\n")
    
    result = onboard_property({
        "url": url,
        "resume": True,
        "extractions": missing
    })
    
    print(f"\n{'='*60}")
    print("ONBOARDING COMPLETE")
    print(f"{'='*60}")
    print(f"Status: {result.get('status', 'unknown')}")
    if result.get('property_id'):
        print(f"Property ID: {result.get('property_id')}")
    print(f"\n{result.get('summary', '')}")


if __name__ == "__main__":
    main()

