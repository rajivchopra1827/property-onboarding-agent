#!/usr/bin/env python3
"""
API wrapper script for generating videos from selected property images.
Called from Next.js API routes via subprocess.

Usage:
    python3 generate_videos_api.py <property_id> <image_ids_json> <theme>

Where image_ids_json is a JSON array of image IDs: '["id1", "id2", ...]'

Outputs JSON to stdout:
    {"success": true, "videos": [...], "errors": [...]}
    or
    {"success": false, "error": "error message"}
"""

import os
import sys
import json
import warnings
import time as time_module
from contextlib import redirect_stdout
from pathlib import Path
from dotenv import load_dotenv

# Suppress warnings to ensure clean JSON output
warnings.filterwarnings('ignore')

# Helper function to print progress messages to stderr (keeps stdout clean for JSON)
def log_progress(*args, **kwargs):
    """Print progress messages to stderr."""
    print(*args, file=sys.stderr, flush=True, **kwargs)

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
    from agno_tools.generate_video_reel_tool import generate_video_reel
    from database import PropertyRepository, PropertySocialPost
except ImportError as e:
    output = json.dumps({
        "success": False,
        "error": f"Failed to import required modules: {str(e)}"
    })
    sys.stdout.write(output)
    sys.stdout.flush()
    sys.exit(1)


def generate_videos_for_images(property_id: str, image_ids: list, theme: str):
    """
    Generate videos for selected images and create minimal social posts.
    
    Args:
        property_id: Property ID
        image_ids: List of image IDs to generate videos for
        theme: Theme to use for video generation
        
    Returns:
        Dictionary with success status, videos, and errors
    """
    property_repo = PropertyRepository()
    videos = []
    errors = []
    
    # Get all property images
    all_images = property_repo.get_visible_property_images(property_id)
    image_map = {img.id: img for img in all_images}
    
    # Process each image
    for image_id in image_ids:
        if image_id not in image_map:
            errors.append({
                "image_id": image_id,
                "error": f"Image {image_id} not found or is hidden"
            })
            continue
        
        image = image_map[image_id]
        
        try:
            # Generate video (redirect stdout to stderr to keep stdout clean for JSON)
            log_progress(f"Generating video for image {image_id}...")
            
            # #region agent log
            try:
                with open('/Users/rajivchopra/Development/Projects/Property Onboarding Agent/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"location":"generate_videos_api.py:97","message":"Starting video generation","data":{"image_id":image_id,"theme":theme},"timestamp":int(time_module.time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"G"}) + "\n")
            except: pass
            # #endregion
            
            try:
                with redirect_stdout(sys.stderr):
                    video_result = generate_video_reel(
                        property_id=property_id,
                        post_theme=theme,
                        image_id=image_id,
                        save_to_db=False  # We'll create the post ourselves
                    )
            except Exception as gen_error:
                # #region agent log
                try:
                    with open('/Users/rajivchopra/Development/Projects/Property Onboarding Agent/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({"location":"generate_videos_api.py:107","message":"Exception during video generation","data":{"image_id":image_id,"errorType":type(gen_error).__name__,"errorMessage":str(gen_error)[:500]},"timestamp":int(time_module.time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"I"}) + "\n")
                except: pass
                # #endregion
                errors.append({
                    "image_id": image_id,
                    "image_url": image.image_url,
                    "error": f"Exception during generation: {type(gen_error).__name__}: {str(gen_error)[:500]}"
                })
                continue
            
            # #region agent log
            try:
                with open('/Users/rajivchopra/Development/Projects/Property Onboarding Agent/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"location":"generate_videos_api.py:120","message":"Video generation result","data":{"image_id":image_id,"success":video_result.get("success") if video_result else None,"video_url":video_result.get("video_url") if video_result else None,"error":video_result.get("error") if video_result else "No result returned","resultKeys":list(video_result.keys()) if video_result else []},"timestamp":int(time_module.time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"G"}) + "\n")
            except Exception as log_err:
                try:
                    with open('/Users/rajivchopra/Development/Projects/Property Onboarding Agent/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({"location":"generate_videos_api.py:120","message":"Failed to log result","data":{"logError":str(log_err)},"timestamp":int(time_module.time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"G"}) + "\n")
                except: pass
            # #endregion
            
            if not video_result or not video_result.get("success"):
                error_msg = video_result.get("error", "Unknown error") if video_result else "No result returned from generate_video_reel"
                errors.append({
                    "image_id": image_id,
                    "image_url": image.image_url,
                    "error": error_msg
                })
                continue
            
            # Create minimal social post with video
            video_url = video_result.get("video_url")
            video_metadata = {
                "generation_time_seconds": video_result.get("generation_time_seconds"),
                "estimated_cost": video_result.get("estimated_cost"),
                "model": video_result.get("model"),
                "duration_seconds": video_result.get("duration_seconds"),
                "resolution": video_result.get("resolution"),
                "aspect_ratio": video_result.get("aspect_ratio")
            }
            
            # Create minimal caption
            caption = f"Video reel - {theme.replace('_', ' ').title()}"
            
            social_post = PropertySocialPost(
                property_id=property_id,
                platform="instagram",
                post_type="video_reel",
                theme=theme,
                image_url=image.image_url,
                caption=caption,
                hashtags=[],
                cta=None,
                ready_to_post_text=caption,
                mockup_image_url=None,
                video_url=video_url,
                is_video=True,
                video_metadata=video_metadata,
                structured_data={
                    "theme": theme,
                    "image": {
                        "url": image.image_url,
                        "alt_text": image.alt_text,
                        "page_url": image.page_url
                    },
                    "caption": caption,
                    "platform": "instagram",
                    "post_type": "video_reel",
                    "video_metadata": video_metadata
                }
            )
            
            post_id = property_repo.create_social_post(social_post)
            
            # #region agent log
            try:
                with open('/Users/rajivchopra/Development/Projects/Property Onboarding Agent/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"location":"generate_videos_api.py:155","message":"Attempting to save video post","data":{"post_id":post_id,"image_id":image_id,"video_url":video_url,"is_video":True},"timestamp":int(time_module.time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"E"}) + "\n")
            except: pass
            # #endregion
            
            if post_id:
                videos.append({
                    "post_id": post_id,
                    "image_id": image_id,
                    "image_url": image.image_url,
                    "video_url": video_url,
                    "theme": theme,
                    "video_metadata": video_metadata
                })
                log_progress(f"Created video post {post_id} for image {image_id}")
                
                # #region agent log
                try:
                    with open('/Users/rajivchopra/Development/Projects/Property Onboarding Agent/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({"location":"generate_videos_api.py:162","message":"Video post saved successfully","data":{"post_id":post_id,"video_url":video_url},"timestamp":int(time_module.time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"E"}) + "\n")
                except: pass
                # #endregion
            else:
                errors.append({
                    "image_id": image_id,
                    "image_url": image.image_url,
                    "error": "Failed to save social post to database"
                })
                
                # #region agent log
                try:
                    with open('/Users/rajivchopra/Development/Projects/Property Onboarding Agent/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({"location":"generate_videos_api.py:175","message":"Failed to save video post","data":{"image_id":image_id,"video_url":video_url},"timestamp":int(time_module.time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"E"}) + "\n")
                except: pass
                # #endregion
                
        except Exception as e:
            errors.append({
                "image_id": image_id,
                "image_url": image.image_url if image else None,
                "error": str(e)
            })
            log_progress(f"Error generating video for image {image_id}: {e}")
    
    return {
        "videos": videos,
        "errors": errors,
        "total_requested": len(image_ids),
        "total_succeeded": len(videos),
        "total_failed": len(errors)
    }


def main():
    """Main function to execute video generation and return JSON result."""
    try:
        # Parse arguments
        if len(sys.argv) < 4:
            output = json.dumps({
                "success": False,
                "error": "Usage: python3 generate_videos_api.py <property_id> <image_ids_json> <theme>"
            })
            print(output, flush=True)
            sys.exit(1)
        
        property_id = sys.argv[1]
        image_ids_json = sys.argv[2]
        theme = sys.argv[3]
        
        # Validate theme
        valid_themes = ["lifestyle", "amenities", "floor_plans", "special_offers", "reviews", "location"]
        if theme not in valid_themes:
            output = json.dumps({
                "success": False,
                "error": f"Invalid theme: {theme}. Must be one of: {', '.join(valid_themes)}"
            })
            print(output, flush=True)
            sys.exit(1)
        
        # Parse image IDs
        try:
            image_ids = json.loads(image_ids_json)
            if not isinstance(image_ids, list):
                raise ValueError("image_ids must be a JSON array")
            if len(image_ids) == 0:
                raise ValueError("At least one image ID is required")
        except json.JSONDecodeError as e:
            output = json.dumps({
                "success": False,
                "error": f"Invalid JSON for image_ids: {str(e)}"
            })
            print(output, flush=True)
            sys.exit(1)
        except ValueError as e:
            output = json.dumps({
                "success": False,
                "error": str(e)
            })
            print(output, flush=True)
            sys.exit(1)
        
        # Generate videos
        result = generate_videos_for_images(property_id, image_ids, theme)
        
        # #region agent log
        try:
            with open('/Users/rajivchopra/Development/Projects/Property Onboarding Agent/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"location":"generate_videos_api.py:240","message":"Video generation complete, preparing response","data":{"totalSucceeded":result.get("total_succeeded"),"totalFailed":result.get("total_failed"),"videosCount":len(result.get("videos",[])),"errorsCount":len(result.get("errors",[]))},"timestamp":int(time_module.time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"F"}) + "\n")
        except: pass
        # #endregion
        
        # Return result to stdout (only JSON output goes here)
        output = json.dumps({
            "success": True,
            **result
        })
        sys.stdout.write(output)
        sys.stdout.flush()
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        log_progress(f"Error in main: {error_details}")
        output = json.dumps({
            "success": False,
            "error": str(e)
        })
        sys.stdout.write(output)
        sys.stdout.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()
