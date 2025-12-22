"""
Tool for classifying property images using OpenAI Vision API.

Analyzes images to:
- Assign tags from predefined categories
- Calculate confidence scores for each tag
- Assess image quality (composition, lighting, clarity, resolution)
"""

import os
import json
import base64
import requests
from typing import List, Dict, Any, Optional
from openai import OpenAI
from datetime import datetime


# Predefined image categories
IMAGE_CATEGORIES = [
    "floor_plans",
    "apartment_interior",
    "building_amenities",
    "apartment_amenities",
    "common_areas",
    "lifestyle",
    "exterior",
    "outdoor_spaces"
]


def get_openai_client():
    """Initialize and return OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Please set it in your environment variables."
        )
    return OpenAI(api_key=api_key)


def download_image_as_base64(image_url: str) -> Optional[str]:
    """
    Download an image from URL and convert to base64.
    
    Args:
        image_url: URL of the image to download
        
    Returns:
        Base64-encoded image string, or None if download fails
    """
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Check if it's an image
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            print(f"Warning: URL does not appear to be an image: {content_type}")
            return None
        
        # Encode to base64
        image_base64 = base64.b64encode(response.content).decode('utf-8')
        return image_base64
    except Exception as e:
        print(f"Error downloading image from {image_url}: {e}")
        return None


def classify_image_with_openai(
    image_url: str, 
    client: OpenAI, 
    amenities_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Classify a single image using OpenAI Vision API.
    
    Args:
        image_url: URL of the image to classify
        client: OpenAI client instance
        amenities_data: Optional dictionary with building_amenities and apartment_amenities lists
        
    Returns:
        Dictionary with tags, confidence scores, and quality score
    """
    # Download and encode image
    image_base64 = download_image_as_base64(image_url)
    if not image_base64:
        return {
            "tags": [],
            "confidence": 0.0,
            "quality_score": 0.0,
            "error": "Failed to download image"
        }
    
    # Build amenities context if provided
    amenities_context = ""
    if amenities_data:
        building_amenities_list = amenities_data.get("building_amenities", [])
        apartment_amenities_list = amenities_data.get("apartment_amenities", [])
        
        if building_amenities_list or apartment_amenities_list:
            amenities_context = "\n\nCONTEXT - Known amenities for this property:\n"
            
            if building_amenities_list:
                building_names = []
                for amenity in building_amenities_list[:10]:  # Limit to first 10
                    if isinstance(amenity, dict):
                        building_names.append(amenity.get("name", ""))
                    else:
                        building_names.append(str(amenity))
                if building_names:
                    amenities_context += f"- Building amenities: {', '.join(building_names)}\n"
            
            if apartment_amenities_list:
                apartment_names = []
                for amenity in apartment_amenities_list[:10]:  # Limit to first 10
                    if isinstance(amenity, dict):
                        apartment_names.append(amenity.get("name", ""))
                    else:
                        apartment_names.append(str(amenity))
                if apartment_names:
                    amenities_context += f"- Apartment amenities: {', '.join(apartment_names)}\n"
            
            amenities_context += "\nUse this context to help match images to the correct amenity category.\n"
    
    # Create the classification prompt
    prompt = f"""Analyze this property image and classify it according to the following categories:

- floor_plans: Architectural drawings, blueprints, layout diagrams, 2D visualizations showing room layouts and spatial relationships. These are technical drawings or digital renderings, not photographs.

- apartment_interior: Actual photographs of furnished or unfurnished apartment rooms including living rooms, bedrooms, kitchens, bathrooms, dining areas, and other interior spaces. These are real photos showing actual room interiors.

- building_amenities: Images of shared/public facilities available to all residents such as pools, gyms, fitness centers, clubhouses, business centers, parking garages, rooftop decks, dog parks, and other building-level amenities. These are spaces shared by the community, not inside individual apartments.

- apartment_amenities: Images of in-unit features and appliances within individual apartments such as stainless steel appliances, granite countertops, dishwashers, air conditioning units, in-unit washers/dryers, walk-in closets, hardwood floors, and other apartment-specific features. These are features inside the actual living units.

- common_areas: Images of shared spaces like lobbies, hallways, mailrooms, elevators, and other common building areas.

- lifestyle: Images showing people, activities, community events, or lifestyle scenes that convey the living experience at the property.

- exterior: Images of the building facade, street view, aerial shots, or any external views of the property.

- outdoor_spaces: Images of patios, balconies, courtyards, rooftop decks, gardens, and other outdoor areas.

For each applicable category, provide:
1. The category name
2. A confidence score from 0.0 to 1.0 (how certain you are this image belongs to this category)

IMPORTANT: 
- Distinguish carefully between "floor_plans" (drawings/diagrams) and "apartment_interior" (actual photographs of rooms). Floor plans are technical drawings or visualizations, while apartment interiors are real photos of rooms.
- Distinguish carefully between "building_amenities" (shared/public facilities like pools, gyms) and "apartment_amenities" (in-unit features like appliances, countertops). Building amenities are shared spaces, while apartment amenities are inside individual units.
{amenities_context}

Also assess the image quality based on:
- Composition (framing, balance)
- Lighting (brightness, contrast)
- Clarity (sharpness, focus)
- Resolution (image size and detail)

Return your analysis as a JSON object with this structure:
{{
    "tags": [
        {{"category": "exterior", "confidence": 0.95}},
        {{"category": "building_amenities", "confidence": 0.30}}
    ],
    "quality_score": 0.85,
    "quality_assessment": "Brief description of quality factors"
}}

Only include tags with confidence >= 0.3. Return only valid JSON, no additional text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        # Parse the response
        content = response.choices[0].message.content.strip()
        
        # Try to extract JSON from the response (in case there's extra text)
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            content = content[json_start:json_end]
        
        result = json.loads(content)
        
        # Extract tags and calculate overall confidence
        tags = []
        confidences = []
        for tag_data in result.get("tags", []):
            category = tag_data.get("category", "").lower()
            confidence = float(tag_data.get("confidence", 0.0))
            if category in IMAGE_CATEGORIES and confidence >= 0.3:
                tags.append(category)
                confidences.append(confidence)
        
        # Calculate overall confidence (average of tag confidences)
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Get quality score
        quality_score = float(result.get("quality_score", 0.0))
        
        return {
            "tags": tags,
            "confidence": round(overall_confidence, 3),
            "quality_score": round(quality_score, 3),
            "quality_assessment": result.get("quality_assessment", "")
        }
        
    except json.JSONDecodeError as e:
        print(f"Error parsing OpenAI response: {e}")
        print(f"Response content: {content}")
        return {
            "tags": [],
            "confidence": 0.0,
            "quality_score": 0.0,
            "error": f"Failed to parse response: {str(e)}"
        }
    except Exception as e:
        print(f"Error classifying image with OpenAI: {e}")
        return {
            "tags": [],
            "confidence": 0.0,
            "quality_score": 0.0,
            "error": str(e)
        }


def classify_images(
    image_urls: List[str], 
    batch_size: int = 5,
    amenities_data: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Classify multiple images, processing in batches to respect rate limits.
    
    Args:
        image_urls: List of image URLs to classify
        batch_size: Number of images to process in each batch
        amenities_data: Optional dictionary with building_amenities and apartment_amenities lists
        
    Returns:
        List of classification results, one per image URL
    """
    client = get_openai_client()
    results = []
    
    for i in range(0, len(image_urls), batch_size):
        batch = image_urls[i:i + batch_size]
        print(f"Classifying batch {i // batch_size + 1} ({len(batch)} images)...")
        
        for image_url in batch:
            print(f"  Classifying: {image_url[:80]}...")
            result = classify_image_with_openai(image_url, client, amenities_data=amenities_data)
            result["image_url"] = image_url
            results.append(result)
            
            # Small delay between requests to avoid rate limits
            import time
            time.sleep(0.5)
        
        # Longer delay between batches
        if i + batch_size < len(image_urls):
            import time
            time.sleep(2)
    
    return results


def get_tool_definition():
    """Returns the tool definition for OpenAI function calling."""
    return {
        "type": "function",
        "function": {
            "name": "classify_images",
            "description": "Classify property images using AI vision to assign tags, confidence scores, and quality scores. Analyzes image content to categorize into: floor_plans, apartment_interior, building_amenities, apartment_amenities, common_areas, lifestyle, exterior, outdoor_spaces.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of image URLs to classify"
                    },
                    "property_id": {
                        "type": "string",
                        "description": "Optional property ID to associate classifications with"
                    },
                    "batch_size": {
                        "type": "integer",
                        "description": "Number of images to process per batch (default: 5)",
                        "default": 5
                    }
                },
                "required": ["image_urls"]
            }
        }
    }


def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the classify_images tool.
    
    Args:
        arguments: Dictionary containing tool arguments
            - image_urls (list): List of image URLs to classify
            - property_id (str, optional): Property ID to update
            - batch_size (int, optional): Batch size for processing
            
    Returns:
        Dictionary with classification results
    """
    image_urls = arguments.get("image_urls", [])
    property_id = arguments.get("property_id")
    batch_size = arguments.get("batch_size", 5)
    
    if not image_urls:
        return {
            "error": "No image URLs provided",
            "results": []
        }
    
    print(f"Classifying {len(image_urls)} images...")
    
    try:
        # Fetch amenities data if property_id is provided
        amenities_data = None
        if property_id:
            from database import PropertyRepository
            repo = PropertyRepository()
            
            # Fetch amenities data for context
            amenities_obj = repo.get_amenities_by_property_id(property_id)
            if amenities_obj and amenities_obj.amenities_data:
                amenities_data = amenities_obj.amenities_data
                print(f"✓ Loaded amenities data for context: {len(amenities_data.get('building_amenities', []))} building, {len(amenities_data.get('apartment_amenities', []))} apartment")
        
        # Classify images
        results = classify_images(image_urls, batch_size=batch_size, amenities_data=amenities_data)
        
        # Update database if property_id is provided
        if property_id:
            if not 'repo' in locals():
                from database import PropertyRepository
                repo = PropertyRepository()
            
            updated_count = 0
            for result in results:
                if "error" not in result:
                    image_url = result.get("image_url")
                    tags = result.get("tags", [])
                    confidence = result.get("confidence", 0.0)
                    quality_score = result.get("quality_score", 0.0)
                    
                    # Find image by URL and update
                    success = repo.update_image_classification_by_url(
                        property_id=property_id,
                        image_url=image_url,
                        tags=tags,
                        confidence=confidence,
                        quality_score=quality_score,
                        method="ai_vision"
                    )
                    if success:
                        updated_count += 1
            
            print(f"✓ Updated {updated_count} images in database")
        
        return {
            "results": results,
            "total_classified": len(results),
            "successful": len([r for r in results if "error" not in r])
        }
        
    except ValueError as e:
        return {
            "error": str(e),
            "results": []
        }
    except Exception as e:
        print(f"Error classifying images: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to classify images: {str(e)}",
            "results": []
        }

