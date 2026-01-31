"""
Simple test to verify Google GenAI API is working and check available models.
"""

import os
from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    print("✓ google.genai imported successfully")
except ImportError as e:
    print(f"✗ Failed to import google.genai: {e}")
    exit(1)

# Get API key
api_key = os.getenv("GOOGLE_AI_API_KEY")
if not api_key:
    print("✗ GOOGLE_AI_API_KEY not found in environment")
    exit(1)

print(f"✓ API key found: {api_key[:20]}...")

# Create client
try:
    client = genai.Client(api_key=api_key)
    print("✓ Client created successfully")
except Exception as e:
    print(f"✗ Failed to create client: {e}")
    exit(1)

# List available models
try:
    print("\nChecking available models...")
    models = client.models.list()

    print("\nAvailable models:")
    for model in models:
        print(f"  - {model.name}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"    Methods: {model.supported_generation_methods}")

    # Look for video models specifically
    video_models = [m for m in models if 'veo' in m.name.lower() or 'video' in m.name.lower()]
    if video_models:
        print("\nVideo generation models found:")
        for m in video_models:
            print(f"  - {m.name}")
    else:
        print("\n⚠ No video generation models found")
        print("Video generation may require waitlist access or different API tier")

except Exception as e:
    print(f"✗ Failed to list models: {e}")
    import traceback
    traceback.print_exc()

print("\n✓ API connectivity test complete")
