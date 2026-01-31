#!/usr/bin/env python3
"""
Test script for amenity normalization.

Tests the normalization service with sample amenities to verify it's working correctly.
"""

import os
import sys
import json
import warnings
from pathlib import Path
from dotenv import load_dotenv

# Suppress warnings
warnings.filterwarnings('ignore')

# Load environment variables
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env.local"
if not env_file.exists():
    env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(env_file)

# Add backend to path
script_dir = Path(__file__).parent
backend_path = script_dir.parent
sys.path.insert(0, str(backend_path))
os.chdir(backend_path)

from services.amenity_normalizer import AmenityNormalizer


def main():
    """Test normalization with sample amenities."""
    print("Testing Amenity Normalization System\n")
    print("=" * 60)
    
    # Test amenities - variations that should normalize to the same canonical name
    test_amenities = [
        {"name": "gym", "category": "building"},
        {"name": "fitness center", "category": "building"},
        {"name": "24-Hour Fitness Center", "category": "building"},
        {"name": "swimming pool", "category": "building"},
        {"name": "pool", "category": "building"},
        {"name": "dishwasher", "category": "apartment"},
        {"name": "Dishwasher", "category": "apartment"},
        {"name": "washer/dryer", "category": "apartment"},
        {"name": "Washer & Dryer", "category": "apartment"},
    ]
    
    print(f"\nTesting {len(test_amenities)} amenities...\n")
    
    try:
        normalizer = AmenityNormalizer()
        
        print("Normalizing amenities...")
        normalized = normalizer.normalize_batch(test_amenities)
        
        print("\nResults:")
        print("-" * 60)
        
        # Group by normalized name to show variations
        grouped = {}
        for n in normalized:
            key = n.normalized_name
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(n)
        
        for normalized_name, mappings in sorted(grouped.items()):
            raw_names = [m.raw_name for m in mappings]
            confidences = [m.confidence for m in mappings if m.confidence]
            avg_confidence = sum(confidences) / len(confidences) if confidences else None
            
            print(f"\n✓ {normalized_name}")
            print(f"  Raw variations: {', '.join(raw_names)}")
            if avg_confidence:
                print(f"  Avg confidence: {avg_confidence:.2f}")
        
        print("\n" + "=" * 60)
        print("✅ Normalization test completed successfully!")
        print(f"   {len(normalized)} amenities normalized")
        print(f"   {len(grouped)} unique normalized names")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
