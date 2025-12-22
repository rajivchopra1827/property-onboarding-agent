#!/usr/bin/env python3
"""
API wrapper script for generate_social_posts tool.
Called from Next.js API routes via subprocess.

Usage:
    python3 generate_social_posts_api.py <property_id> [post_count]

Outputs JSON to stdout:
    {"success": true, "count": 8, "posts": [...]}
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
    from tools.generate_social_posts import execute
except ImportError as e:
    output = json.dumps({
        "success": False,
        "error": f"Failed to import generate_social_posts: {str(e)}"
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
        post_count = 8
        
        if len(sys.argv) > 2:
            try:
                post_count = int(sys.argv[2])
                post_count = max(5, min(10, post_count))  # Clamp between 5-10
            except ValueError:
                pass  # Use default
        
        # Execute tool
        # Note: The execute function may print progress messages, but we'll extract JSON from output
        result = execute({
            "property_id": property_id,
            "post_count": post_count
        })
        
        # Check for errors
        if result.get("error"):
            output = json.dumps({
                "success": False,
                "error": result.get("error")
            })
            print(output, flush=True)
            sys.exit(1)
        
        # Return success result (flush to ensure it's sent)
        output = json.dumps({
            "success": True,
            "count": result.get("count", 0),
            "property_id": result.get("property_id"),
            "posts": result.get("posts", [])
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

