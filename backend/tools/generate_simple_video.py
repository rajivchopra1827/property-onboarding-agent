"""
Phase 1 proof of concept: Single image-to-video conversion using Google Gemini API.

Generates 5-second cinematic videos from static property images.
"""

import os
import time
import requests
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import Google Generative AI
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("Warning: google-genai not installed. Run: pip install google-genai")


# Video generation configuration
VIDEO_CONFIG = {
    "model": "veo-2.0-generate-001",
    "duration_seconds": 5,
    "resolution": "1080p",
    "aspect_ratio": "9:16",  # Portrait for Instagram Reels
    "generation_timeout": 300,  # 5 minutes max wait
    "poll_interval": 10,  # Check every 10 seconds
}

# Cost tracking (approximate costs based on Gemini pricing)
COST_PER_VIDEO = 0.10  # Approximate cost per 5-second video


def get_genai_client():
    """Initialize and return Google Generative AI client."""
    if not GENAI_AVAILABLE:
        raise ValueError(
            "google-generativeai not installed. Run: pip install google-generativeai>=1.52.0"
        )

    api_key = os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_AI_API_KEY not found. Please set it in your environment variables."
        )

    return genai.Client(api_key=api_key)


def download_image_to_bytes(image_url: str) -> bytes:
    """Download image from URL and return bytes."""
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        raise ValueError(f"Failed to download image from {image_url}: {e}")


def get_motion_prompt(theme: str = "lifestyle") -> str:
    """
    Get a cinematic motion prompt based on the post theme.

    Args:
        theme: Post theme (lifestyle, amenities, location, etc.)

    Returns:
        Motion prompt string for video generation
    """
    theme_prompts = {
        "lifestyle": "Smooth cinematic camera motion revealing the space. Gentle dolly forward with soft ambient lighting. Professional real estate video quality.",
        "amenities": "Elegant slow pan across amenities with cinematic depth of field. Soft natural lighting highlighting key features. Luxury property showcase.",
        "floor_plans": "Architectural flythrough style camera movement. Steady glide through the living space. Clean modern aesthetic with natural light.",
        "special_offers": "Dynamic reveal with subtle zoom. Energetic yet professional motion. Eye-catching presentation for marketing.",
        "reviews": "Warm inviting camera movement showing lived-in comfort. Cozy atmosphere with gentle lighting. Home lifestyle video.",
        "location": "Establishing shot style with smooth pan. Showcase exterior and surroundings. Premium real estate video quality."
    }

    return theme_prompts.get(theme, theme_prompts["lifestyle"])


def generate_video_from_image(
    image_url: str,
    output_path: Optional[str] = None,
    theme: str = "lifestyle",
    caption: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a 5-second video from a static image using Google Gemini Veo.

    Args:
        image_url: URL of the source image
        output_path: Optional path to save the video (defaults to backend/reels/)
        theme: Post theme for motion style selection
        caption: Optional caption for context in generation

    Returns:
        Dictionary with video_url, generation_time, cost, and metadata
    """
    start_time = time.time()

    print(f"Starting video generation from image: {image_url}")
    print(f"Theme: {theme}")

    # Initialize client
    try:
        client = get_genai_client()
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "video_url": None,
            "fallback_used": True
        }

    # Set up output path
    if output_path is None:
        reels_dir = Path(__file__).parent.parent / "reels"
        reels_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(reels_dir / f"reel_{timestamp}.mp4")

    # Download and prepare the image
    try:
        print("  Downloading source image...")
        image_bytes = download_image_to_bytes(image_url)
        print(f"  Downloaded {len(image_bytes)} bytes")
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to download image: {e}",
            "video_url": None,
            "fallback_used": True
        }

    # Get motion prompt
    motion_prompt = get_motion_prompt(theme)
    print(f"  Motion prompt: {motion_prompt[:50]}...")

    # Upload image to Gemini
    try:
        print("  Uploading image to Gemini...")

        # Determine MIME type from image
        if image_url.lower().endswith('.png'):
            mime_type = "image/png"
        elif image_url.lower().endswith(('.jpg', '.jpeg')):
            mime_type = "image/jpeg"
        elif image_url.lower().endswith('.webp'):
            mime_type = "image/webp"
        else:
            mime_type = "image/jpeg"  # Default

        uploaded_image = client.files.upload(
            file=image_bytes,
            config=types.UploadFileConfig(
                mime_type=mime_type,
                display_name="property_image"
            )
        )
        print(f"  Uploaded file: {uploaded_image.name}")

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to upload image to Gemini: {e}",
            "video_url": None,
            "fallback_used": True
        }

    # Generate video using Veo
    try:
        print("  Generating video with Veo 2.0...")

        operation = client.models.generate_videos(
            model=VIDEO_CONFIG["model"],
            prompt=motion_prompt,
            image=uploaded_image,
            config=types.GenerateVideosConfig(
                aspect_ratio=VIDEO_CONFIG["aspect_ratio"],
                number_of_videos=1,
            )
        )

        # Poll for completion
        print("  Waiting for video generation...")
        elapsed = 0
        while not operation.done:
            if elapsed >= VIDEO_CONFIG["generation_timeout"]:
                return {
                    "success": False,
                    "error": "Video generation timed out",
                    "video_url": None,
                    "fallback_used": True
                }

            time.sleep(VIDEO_CONFIG["poll_interval"])
            elapsed += VIDEO_CONFIG["poll_interval"]
            print(f"    Progress: {elapsed}s elapsed...")
            operation = client.operations.get(operation)

        # Get the generated video
        if not operation.response or not operation.response.generated_videos:
            return {
                "success": False,
                "error": "No video generated",
                "video_url": None,
                "fallback_used": True
            }

        generated_video = operation.response.generated_videos[0]

        # Download and save the video
        print("  Downloading generated video...")
        video_data = client.files.download(file=generated_video.video)

        # Write video to file
        with open(output_path, "wb") as f:
            f.write(video_data)

        generation_time = time.time() - start_time

        print(f"  Video saved to: {output_path}")
        print(f"  Generation time: {generation_time:.1f}s")
        print(f"  Estimated cost: ${COST_PER_VIDEO:.2f}")

        return {
            "success": True,
            "video_url": output_path,
            "video_path": output_path,
            "generation_time_seconds": generation_time,
            "estimated_cost": COST_PER_VIDEO,
            "model": VIDEO_CONFIG["model"],
            "duration_seconds": VIDEO_CONFIG["duration_seconds"],
            "resolution": VIDEO_CONFIG["resolution"],
            "aspect_ratio": VIDEO_CONFIG["aspect_ratio"],
            "theme": theme,
            "motion_prompt": motion_prompt,
            "fallback_used": False
        }

    except Exception as e:
        error_msg = str(e)
        print(f"  Error generating video: {error_msg}")

        return {
            "success": False,
            "error": f"Video generation failed: {error_msg}",
            "video_url": None,
            "fallback_used": True
        }


def estimate_cost(video_count: int) -> Dict[str, Any]:
    """
    Estimate the cost of generating multiple videos.

    Args:
        video_count: Number of videos to generate

    Returns:
        Dictionary with cost estimate details
    """
    total_cost = video_count * COST_PER_VIDEO
    return {
        "video_count": video_count,
        "cost_per_video": COST_PER_VIDEO,
        "total_estimated_cost": total_cost,
        "currency": "USD"
    }


# CLI interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python generate_simple_video.py <image_url> [theme]")
        print("Themes: lifestyle, amenities, floor_plans, special_offers, reviews, location")
        sys.exit(1)

    image_url = sys.argv[1]
    theme = sys.argv[2] if len(sys.argv) > 2 else "lifestyle"

    print(f"\nGenerating video from: {image_url}")
    print(f"Theme: {theme}")
    print("-" * 50)

    result = generate_video_from_image(image_url, theme=theme)

    print("\n" + "=" * 50)
    print("Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")
