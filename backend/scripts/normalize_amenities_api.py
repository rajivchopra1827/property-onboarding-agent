#!/usr/bin/env python3
"""
API script for normalizing amenity names.

Called from Next.js API route to normalize amenities using the AmenityNormalizer service.

Usage:
    echo '{"amenities": [{"name": "gym", "category": "building"}]}' | python3 normalize_amenities_api.py

Outputs JSON to stdout:
    {"normalized": [...], "success": true}
    or
    {"error": "error message", "success": false}
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

# Add backend to path - ensure we can import services
script_dir = Path(__file__).parent
backend_path = script_dir.parent
sys.path.insert(0, str(backend_path))

# Change to backend directory to ensure relative imports work
os.chdir(backend_path)

try:
    from services.amenity_normalizer import AmenityNormalizer
except ImportError as e:
    output = json.dumps({
        "success": False,
        "error": f"Failed to import modules: {str(e)}"
    })
    print(output, flush=True)
    sys.exit(1)


def main():
    """Normalize amenities from stdin JSON."""
    try:
        # Read amenities from stdin
        input_data = json.load(sys.stdin)
        
        if not isinstance(input_data, dict) or 'amenities' not in input_data:
            output = json.dumps({
                "success": False,
                "error": "Invalid input: 'amenities' array required"
            })
            print(output, flush=True)
            sys.exit(1)
        
        amenities = input_data['amenities']
        
        if not isinstance(amenities, list):
            output = json.dumps({
                "success": False,
                "error": "Invalid input: 'amenities' must be an array"
            })
            print(output, flush=True)
            sys.exit(1)
        
        # Initialize normalizer
        normalizer = AmenityNormalizer()
        
        # Normalize all amenities
        normalized = normalizer.normalize_batch(amenities)
        
        # Convert to dict format
        result = {
            "normalized": [n.to_dict() for n in normalized],
            "success": True
        }
        
        print(json.dumps(result), flush=True)
        
    except Exception as e:
        error_result = {
            "error": str(e),
            "success": False
        }
        print(json.dumps(error_result), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
