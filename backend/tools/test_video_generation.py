"""
Test video generation with Google GenAI Veo model.
"""

import os
import time
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Configuration
IMAGE_URL = "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=1080"
OUTPUT_DIR = Path(__file__).parent.parent / "reels"
OUTPUT_DIR.mkdir(exist_ok=True)

# Initialize client
api_key = os.getenv("GOOGLE_AI_API_KEY")
if not api_key:
    print("✗ GOOGLE_AI_API_KEY not found")
    exit(1)

client = genai.Client(api_key=api_key)
print(f"✓ Client initialized")

# Download image
print(f"\nDownloading image from: {IMAGE_URL}")
response = requests.get(IMAGE_URL, timeout=30)
response.raise_for_status()
image_bytes = response.content
print(f"✓ Downloaded {len(image_bytes)} bytes")

# Upload image to Gemini Files API
print("\nUploading image to Gemini...")
try:
    # Save bytes to temporary file first
    temp_image_path = OUTPUT_DIR / "temp_source.jpg"
    with open(temp_image_path, "wb") as f:
        f.write(image_bytes)

    print(f"  Saved to temp file: {temp_image_path}")

    # Upload using file parameter (trying different approaches)
    try:
        # Approach 1: with file path string
        uploaded_file = client.files.upload(file=str(temp_image_path))
    except TypeError:
        # Approach 2: with open file handle
        with open(temp_image_path, "rb") as f:
            uploaded_file = client.files.upload(file=f)

    print(f"✓ File uploaded: {uploaded_file.name}")
    print(f"  URI: {uploaded_file.uri}")

except Exception as e:
    print(f"✗ Upload failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Generate video
print("\nGenerating video with Veo 2.0...")
try:
    prompt = "Smooth cinematic camera motion revealing the space. Gentle dolly forward with soft ambient lighting. Professional real estate video quality."

    print(f"  Model: veo-2.0-generate-001")
    print(f"  Prompt: {prompt[:60]}...")
    print(f"  Aspect ratio: 9:16 (portrait)")

    # Try text-to-video first (without image) to test if billing works
    print(f"  Testing text-to-video (no image reference)")

    operation = client.models.generate_videos(
        model="veo-2.0-generate-001",
        prompt=prompt + " Modern luxury apartment with floor-to-ceiling windows and city views.",
        # image=None,  # Omit image parameter for text-to-video
        config=types.GenerateVideosConfig(
            aspect_ratio="9:16",
            number_of_videos=1,
        )
    )

    print(f"✓ Video generation started")
    print(f"  Operation: {operation.name}")

    # Poll for completion
    print("\nWaiting for generation to complete...")
    max_wait = 300  # 5 minutes
    poll_interval = 10
    elapsed = 0

    while not operation.done and elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval
        operation = client.operations.get(operation)
        status = "running" if not operation.done else "complete"
        print(f"  {elapsed}s elapsed... (status: {status})")

    if not operation.done:
        print("✗ Timeout waiting for video generation")
        exit(1)

    print(f"✓ Generation complete!")

    # Check for errors
    if operation.error:
        print(f"✗ Generation error: {operation.error}")
        exit(1)

    # Get generated video
    if not operation.response or not operation.response.generated_videos:
        print("✗ No video generated")
        exit(1)

    generated_video = operation.response.generated_videos[0]
    print(f"  Generated video object received")

    # Download video
    print("\nDownloading generated video...")
    video_data = client.files.download(file=generated_video.video.uri)

    # Save video
    output_path = OUTPUT_DIR / "test_reel_001.mp4"
    with open(output_path, "wb") as f:
        f.write(video_data)

    file_size = len(video_data) / (1024 * 1024)  # MB
    print(f"✓ Video saved: {output_path}")
    print(f"  Size: {file_size:.2f} MB")
    print(f"\n🎬 SUCCESS! Video generated at: {output_path}")

except Exception as e:
    print(f"✗ Video generation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Cleanup temp file
if temp_image_path.exists():
    temp_image_path.unlink()
    print("\n✓ Cleaned up temporary files")
