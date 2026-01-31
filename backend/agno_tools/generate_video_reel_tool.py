"""
Agno-native tool for generating video reels from property images.

Uses Google Gemini Veo 2.0 to transform static images into 5-second cinematic videos.
Falls back to static mockup if video generation fails.
"""

import os
import sys
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from database import PropertyRepository
from agno_tools.tool import Tool


def generate_video_reel(
    property_id: str,
    post_theme: str = "lifestyle",
    image_id: Optional[str] = None,
    image_url: Optional[str] = None,
    caption: Optional[str] = None,
    save_to_db: bool = True
) -> Dict[str, Any]:
    """
    Generate a video reel from a property image.

    This tool:
    1. Fetches the property image (by ID or URL)
    2. Generates a 5-second cinematic video using Google Gemini Veo
    3. Saves the video to backend/reels/
    4. Optionally updates the database with video URL

    Args:
        property_id: ID of the property
        post_theme: Theme for the post (affects motion style)
        image_id: Optional ID of the property image to use
        image_url: Optional direct URL of the image to use
        caption: Optional caption text for context
        save_to_db: Whether to save video URL to database

    Returns:
        Dictionary with video_url, success status, and metadata
    """
    print(f"Generating video reel for property {property_id}")
    print(f"Theme: {post_theme}")

    # Validate inputs
    if not property_id:
        return {
            "success": False,
            "error": "property_id is required",
            "video_url": None,
            "fallback_used": True
        }

    # Get image URL if not provided
    if not image_url:
        if image_id:
            # Fetch image by ID
            try:
                property_repo = PropertyRepository()
                images = property_repo.get_property_images(property_id)
                image = next((img for img in images if img.id == image_id), None)
                if image:
                    image_url = image.image_url
                else:
                    return {
                        "success": False,
                        "error": f"Image with ID {image_id} not found",
                        "video_url": None,
                        "fallback_used": True
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to fetch image: {e}",
                    "video_url": None,
                    "fallback_used": True
                }
        else:
            # Get any visible image for the property
            try:
                property_repo = PropertyRepository()
                images = property_repo.get_visible_property_images(property_id)
                if images:
                    image_url = images[0].image_url
                else:
                    return {
                        "success": False,
                        "error": "No visible images found for property",
                        "video_url": None,
                        "fallback_used": True
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to fetch images: {e}",
                    "video_url": None,
                    "fallback_used": True
                }

    print(f"Using image: {image_url}")

    # Import the video generation function
    try:
        from tools.generate_simple_video import generate_video_from_image, GENAI_AVAILABLE
    except ImportError as e:
        return {
            "success": False,
            "error": f"Video generation module not available: {e}",
            "video_url": None,
            "fallback_used": True
        }

    # Check if Google AI is available
    if not GENAI_AVAILABLE:
        print("  Warning: google-generativeai not installed, falling back to static mockup")
        return {
            "success": False,
            "error": "google-generativeai SDK not installed",
            "video_url": None,
            "fallback_used": True,
            "fallback_reason": "sdk_not_installed"
        }

    # Check for API key
    if not os.getenv("GOOGLE_AI_API_KEY"):
        print("  Warning: GOOGLE_AI_API_KEY not set, falling back to static mockup")
        return {
            "success": False,
            "error": "GOOGLE_AI_API_KEY environment variable not set",
            "video_url": None,
            "fallback_used": True,
            "fallback_reason": "api_key_not_set"
        }

    # Generate output path
    reels_dir = Path(__file__).parent.parent / "reels"
    reels_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"reel_{property_id}_{post_theme}_{timestamp}.mp4"
    output_path = str(reels_dir / output_filename)

    # Generate the video
    print(f"  Generating video to: {output_path}")
    result = generate_video_from_image(
        image_url=image_url,
        output_path=output_path,
        theme=post_theme,
        caption=caption
    )

    if result.get("success"):
        # Video generated successfully
        video_url = f"reels/{output_filename}"

        print(f"  Video generated successfully: {video_url}")
        print(f"  Generation time: {result.get('generation_time_seconds', 0):.1f}s")
        print(f"  Estimated cost: ${result.get('estimated_cost', 0):.2f}")

        return {
            "success": True,
            "video_url": video_url,
            "video_path": output_path,
            "generation_time_seconds": result.get("generation_time_seconds"),
            "estimated_cost": result.get("estimated_cost"),
            "model": result.get("model"),
            "duration_seconds": result.get("duration_seconds"),
            "resolution": result.get("resolution"),
            "aspect_ratio": result.get("aspect_ratio"),
            "theme": post_theme,
            "source_image_url": image_url,
            "property_id": property_id,
            "fallback_used": False
        }
    else:
        # Video generation failed, return error info
        print(f"  Video generation failed: {result.get('error')}")
        return {
            "success": False,
            "error": result.get("error"),
            "video_url": None,
            "fallback_used": True,
            "fallback_reason": "generation_failed",
            "source_image_url": image_url,
            "property_id": property_id
        }


def get_tool_definition() -> Dict[str, Any]:
    """Returns the tool definition for OpenAI function calling."""
    return {
        "type": "function",
        "function": {
            "name": "generate_video_reel",
            "description": "Generate a 5-second cinematic video reel from a property image using Google Gemini Veo. Falls back to static mockup if video generation is unavailable.",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "string",
                        "description": "The ID of the property"
                    },
                    "post_theme": {
                        "type": "string",
                        "enum": ["lifestyle", "amenities", "floor_plans", "special_offers", "reviews", "location"],
                        "description": "Theme for the video (affects motion style)",
                        "default": "lifestyle"
                    },
                    "image_id": {
                        "type": "string",
                        "description": "Optional ID of a specific property image to use"
                    },
                    "image_url": {
                        "type": "string",
                        "description": "Optional direct URL of the image to use"
                    },
                    "caption": {
                        "type": "string",
                        "description": "Optional caption text for context"
                    }
                },
                "required": ["property_id"]
            }
        }
    }


# Create Agno Tool
generate_video_reel_tool = Tool(
    name="generate_video_reel",
    description="Generate a 5-second cinematic video reel from a property image using Google Gemini Veo 2.0. Falls back to static mockup if unavailable.",
    func=generate_video_reel,
)


# CLI interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python generate_video_reel_tool.py <property_id> [theme] [image_url]")
        print("Themes: lifestyle, amenities, floor_plans, special_offers, reviews, location")
        sys.exit(1)

    property_id = sys.argv[1]
    theme = sys.argv[2] if len(sys.argv) > 2 else "lifestyle"
    image_url = sys.argv[3] if len(sys.argv) > 3 else None

    print(f"\nGenerating video reel for property: {property_id}")
    print(f"Theme: {theme}")
    if image_url:
        print(f"Image URL: {image_url}")
    print("-" * 50)

    result = generate_video_reel(
        property_id=property_id,
        post_theme=theme,
        image_url=image_url
    )

    print("\n" + "=" * 50)
    print("Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")
