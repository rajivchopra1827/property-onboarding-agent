"""
Amenity normalization service.

Maps raw amenity names (e.g., "gym", "24-Hour Fitness Center") to canonical
standardized names (e.g., "Fitness Center") using AI-powered mapping against
a predefined taxonomy.
"""

import os
import json
from typing import Optional, Dict, Any, List
from openai import OpenAI
from database.property_repository import PropertyRepository
from database.amenity_taxonomy import CANONICAL_AMENITIES, get_canonical_amenities, is_canonical


def get_openai_client() -> OpenAI:
    """Initialize and return OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Please set it in your environment variables."
        )
    return OpenAI(api_key=api_key)


class NormalizedAmenity:
    """Represents a normalized amenity with metadata."""
    
    def __init__(self, raw_name: str, normalized_name: str, confidence: Optional[float] = None):
        self.raw_name = raw_name
        self.normalized_name = normalized_name
        self.confidence = confidence
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_name": self.raw_name,
            "normalized_name": self.normalized_name,
            "confidence": self.confidence
        }


class AmenityNormalizer:
    """Service for normalizing amenity names using AI and taxonomy."""
    
    def __init__(self):
        self.taxonomy = CANONICAL_AMENITIES
        self.db = PropertyRepository()
        self.openai_client = None  # Lazy initialization
    
    def _get_openai_client(self) -> OpenAI:
        """Lazy initialization of OpenAI client."""
        if self.openai_client is None:
            self.openai_client = get_openai_client()
        return self.openai_client
    
    def normalize(self, raw_name: str, category: str) -> NormalizedAmenity:
        """
        Normalize a single amenity name.
        
        Args:
            raw_name: Raw amenity name to normalize
            category: Category ('building' or 'apartment')
            
        Returns:
            NormalizedAmenity instance
        """
        # 1. Check if already canonical
        if is_canonical(raw_name, category):
            return NormalizedAmenity(raw_name, raw_name, confidence=1.0)
        
        # 2. Check mappings table
        mapping = self.db.get_normalization_mapping(raw_name, category)
        if mapping:
            return NormalizedAmenity(
                raw_name=raw_name,
                normalized_name=mapping["normalized_name"],
                confidence=mapping.get("confidence_score")
            )
        
        # 3. Use AI to normalize
        normalized = self._normalize_with_ai(raw_name, category)
        
        # 4. Store mapping
        self.db.create_normalization_mapping(
            raw_name=raw_name,
            normalized_name=normalized.normalized_name,
            category=category,
            confidence_score=normalized.confidence,
            source='ai'
        )
        
        return normalized
    
    def normalize_batch(self, amenities: List[Dict[str, str]]) -> List[NormalizedAmenity]:
        """
        Normalize multiple amenities in batch.
        
        Args:
            amenities: List of dicts with 'name' and 'category' keys
            
        Returns:
            List of NormalizedAmenity instances
        """
        results = []
        for amenity in amenities:
            normalized = self.normalize(
                raw_name=amenity["name"],
                category=amenity["category"]
            )
            results.append(normalized)
        return results
    
    def _normalize_with_ai(self, raw_name: str, category: str) -> NormalizedAmenity:
        """
        Use AI to normalize an amenity name against the canonical taxonomy.
        
        Args:
            raw_name: Raw amenity name
            category: Category ('building' or 'apartment')
            
        Returns:
            NormalizedAmenity instance
        """
        canonical_list = get_canonical_amenities(category)
        
        # Create prompt for AI
        prompt = f"""You are an amenity normalization expert. Map the following amenity name to the closest standard name from the taxonomy.

Raw Name: "{raw_name}"
Category: {category}

Canonical Taxonomy ({len(canonical_list)} options):
{json.dumps(canonical_list, indent=2)}

Instructions:
1. Find the closest matching canonical amenity name
2. If no good match exists, return the raw name as-is (but still provide a confidence score)
3. Consider variations, synonyms, and common naming patterns
4. Return a JSON object with normalized_name, confidence (0.0-1.0), and reasoning

Return JSON:
{{
  "normalized_name": "Fitness Center",
  "confidence": 0.95,
  "reasoning": "24-Hour Fitness Center is a variation of Fitness Center"
}}"""

        try:
            client = self._get_openai_client()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at normalizing amenity names. Always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistency
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            normalized_name = result.get("normalized_name", raw_name)
            confidence = result.get("confidence", 0.8)
            
            # Validate that normalized name is in taxonomy (or use raw if not)
            if normalized_name not in canonical_list and normalized_name != raw_name:
                # Try fuzzy match or use raw name
                normalized_name = raw_name
                confidence = 0.5
            
            return NormalizedAmenity(
                raw_name=raw_name,
                normalized_name=normalized_name,
                confidence=float(confidence)
            )
            
        except Exception as e:
            print(f"Error normalizing with AI: {e}")
            # Fallback: return raw name
            return NormalizedAmenity(
                raw_name=raw_name,
                normalized_name=raw_name,
                confidence=0.5
            )
    
    def find_similar_amenities(self, normalized_name: str, category: str) -> List[str]:
        """
        Find all raw names that map to a normalized name.
        
        Args:
            normalized_name: Normalized canonical name
            category: Category ('building' or 'apartment')
            
        Returns:
            List of raw names that map to this normalized name
        """
        mappings = self.db.get_normalizations_by_normalized_name(normalized_name, category)
        return [m["raw_name"] for m in mappings]
