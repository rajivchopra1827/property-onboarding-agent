#!/usr/bin/env python3
"""
API wrapper script for extract_brand_identity tool.
Called from Next.js API routes via subprocess.

Usage:
    python3 extract_brand_identity_api.py <property_id>

Outputs JSON to stdout:
    {"success": true}
    or
    {"success": false, "error": "error message"}
"""

import os
import sys
import json
import warnings
from pathlib import Path
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
    from tools.extract_brand_identity import execute
    from database import PropertyRepository
except ImportError as e:
    output = json.dumps({
        "success": False,
        "error": f"Failed to import modules: {str(e)}"
    })
    print(output, flush=True)
    sys.exit(1)

def main():
    """Main function to execute tool and return JSON result."""
    try:
        # Parse arguments
        if len(sys.argv) < 2:
            output = json.dumps({
                "success": False,
                "error": "property_id is required"
            })
            print(output, flush=True)
            sys.exit(1)
        
        property_id = sys.argv[1]
        
        # Get property to retrieve website URL
        property_repo = PropertyRepository()
        property_obj = property_repo.get_property_by_id(property_id)
        
        if not property_obj:
            output = json.dumps({
                "success": False,
                "error": f"Property with ID {property_id} not found"
            })
            print(output, flush=True)
            sys.exit(1)
        
        if not property_obj.website_url:
            output = json.dumps({
                "success": False,
                "error": "Property does not have a website URL"
            })
            print(output, flush=True)
            sys.exit(1)
        
        # Execute tool
        result = execute({
            "url": property_obj.website_url,
            "use_cache": True,
            "force_refresh": False
        })
        
        # Check for errors
        if result.get("error"):
            output = json.dumps({
                "success": False,
                "error": result.get("error")
            })
            print(output, flush=True)
            sys.exit(1)
        
        # Return success result
        output = json.dumps({
            "success": True,
            "property_id": property_id
        })
        print(output, flush=True)
        
    except Exception as e:
        output = json.dumps({
            "success": False,
            "error": str(e)
        })
        print(output, flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()


