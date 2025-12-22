#!/usr/bin/env python3
"""
API wrapper script for bulk_classify_images tool.
Called from Next.js API routes via subprocess.

Usage:
    python3 classify_images_api.py <property_id> [force_reclassify]

Outputs JSON to stdout:
    {"success": true, "classified": 10, "failed": 0}
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

# Load environment variables from project root .env.local or .env file
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env.local"
if not env_file.exists():
    env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(env_file)

# Add backend to path - ensure we can import tools
script_dir = Path(__file__).parent
backend_path = script_dir.parent
sys.path.insert(0, str(backend_path))

# Change to backend directory to ensure relative imports work
os.chdir(backend_path)

try:
    from tools.bulk_classify_images import execute
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
        force_reclassify = len(sys.argv) > 2 and sys.argv[2].lower() == 'true'
        
        # Execute tool
        result = execute({
            "property_id": property_id,
            "force_reclassify": force_reclassify
        })
        
        # Check for errors
        if not result.get("success") or result.get("error"):
            output = json.dumps({
                "success": False,
                "error": result.get("error") or "Classification failed"
            })
            print(output, flush=True)
            sys.exit(1)
        
        # Extract statistics from result
        stats = result.get("statistics", {})
        
        # Return success result
        output = json.dumps({
            "success": True,
            "property_id": property_id,
            "classified": stats.get("classified", 0),
            "failed": stats.get("failed", 0),
            "total_images": stats.get("total_images", 0),
            "images_to_classify": stats.get("images_to_classify", 0)
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

