#!/usr/bin/env python3
"""
Check if a property has any video posts in Supabase.

Usage:
    python3 check_property_videos.py "Property Name"
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env.local"
if not env_file.exists():
    env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(env_file)

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from database import PropertyRepository

def check_property_videos(property_name: str):
    """Check if a property has video posts."""
    repo = PropertyRepository()
    
    # Find property by name
    properties = repo.client.table("properties").select("*").ilike("property_name", f"%{property_name}%").execute()
    
    if not properties.data:
        print(f"❌ Property '{property_name}' not found")
        return
    
    print(f"Found {len(properties.data)} matching property/properties:\n")
    
    for prop in properties.data:
        prop_id = prop["id"]
        prop_name = prop.get("property_name", "Unknown")
        
        print(f"Property: {prop_name}")
        print(f"ID: {prop_id}")
        
        # Get all social posts for this property
        posts = repo.client.table("property_social_posts").select("*").eq("property_id", prop_id).execute()
        
        if not posts.data:
            print("  No social posts found\n")
            continue
        
        # Filter for video posts
        video_posts = [p for p in posts.data if p.get("is_video") == True]
        
        print(f"  Total posts: {len(posts.data)}")
        print(f"  Video posts: {len(video_posts)}")
        
        if video_posts:
            print("\n  Video Posts:")
            for i, post in enumerate(video_posts, 1):
                video_url = post.get("video_url", "N/A")
                theme = post.get("theme", "N/A")
                created = post.get("created_at", "N/A")
                print(f"    {i}. Theme: {theme}")
                print(f"       Video URL: {video_url}")
                print(f"       Created: {created}")
                print()
        else:
            print("  No video posts found\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 check_property_videos.py \"Property Name\"")
        sys.exit(1)
    
    property_name = sys.argv[1]
    check_property_videos(property_name)
