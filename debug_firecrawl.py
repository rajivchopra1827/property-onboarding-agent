#!/usr/bin/env python3
"""
Debug script to inspect Firecrawl response structure.
Run this to understand how Firecrawl returns data.
"""

import os
from dotenv import load_dotenv
from pathlib import Path
from firecrawl import Firecrawl

# Load environment variables
env_file = Path(".env.local")
if not env_file.exists():
    env_file = Path(".env")

if env_file.exists():
    load_dotenv(env_file)

# Get API key
api_key = os.getenv("FIRECRAWL_API_KEY")
if not api_key:
    print("Error: FIRECRAWL_API_KEY not found")
    exit(1)

# Initialize Firecrawl
firecrawl = Firecrawl(api_key=api_key)

# Test URL
test_url = "https://www.villasattowngate.com"

print(f"Testing Firecrawl scrape on: {test_url}")
print("=" * 60)

try:
    result = firecrawl.scrape(
        url=test_url,
        formats=["markdown"],
        only_main_content=True,
        timeout=120000
    )
    
    print(f"\nResult type: {type(result)}")
    print(f"Result class: {result.__class__}")
    print(f"Result module: {result.__class__.__module__}")
    
    print(f"\nAvailable attributes:")
    attrs = [attr for attr in dir(result) if not attr.startswith('_')]
    for attr in attrs:
        try:
            value = getattr(result, attr)
            if not callable(value):
                print(f"  - {attr}: {type(value)} = {str(value)[:100]}")
        except Exception as e:
            print(f"  - {attr}: Error accessing - {e}")
    
    print(f"\nTrying to access markdown:")
    if hasattr(result, 'markdown'):
        print(f"  ✓ result.markdown exists: {len(str(result.markdown))} chars")
    else:
        print(f"  ✗ result.markdown does not exist")
    
    if isinstance(result, dict):
        print(f"  ✓ result is a dict")
        if 'markdown' in result:
            print(f"  ✓ result['markdown'] exists: {len(str(result['markdown']))} chars")
    else:
        print(f"  ✗ result is not a dict")
    
    if hasattr(result, 'data'):
        print(f"  ✓ result.data exists: {type(result.data)}")
        if hasattr(result.data, 'markdown'):
            print(f"  ✓ result.data.markdown exists: {len(str(result.data.markdown))} chars")
        elif isinstance(result.data, dict) and 'markdown' in result.data:
            print(f"  ✓ result.data['markdown'] exists: {len(str(result.data['markdown']))} chars")
    
    print(f"\nFull object representation (first 500 chars):")
    print(str(result)[:500])
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()

