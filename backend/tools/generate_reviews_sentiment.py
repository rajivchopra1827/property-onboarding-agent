"""
Tool for generating sentiment summaries from property reviews using OpenAI.

Analyzes review texts and creates a concise summary highlighting key themes,
common positive feedback, and common concerns.
"""

import os
from openai import OpenAI
from database import PropertyRepository


def get_openai_client():
    """Initialize and return OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Please set it in your environment variables."
        )
    return OpenAI(api_key=api_key)


def generate_sentiment_summary(reviews_text_list: list[str]) -> str:
    """
    Generate a sentiment summary from a list of review texts using OpenAI.
    
    Args:
        reviews_text_list: List of review text strings to analyze
        
    Returns:
        Generated sentiment summary string (2-3 sentences)
    """
    if not reviews_text_list:
        return "No reviews available for sentiment analysis."
    
    # Limit the number of reviews to avoid token limits
    # Take up to 50 reviews, prioritizing recent ones
    reviews_to_analyze = reviews_text_list[:50]
    
    # Combine reviews into a single text block
    reviews_text = "\n\n---\n\n".join([
        f"Review {i+1}: {review_text}" 
        for i, review_text in enumerate(reviews_to_analyze)
    ])
    
    # Truncate if too long (OpenAI has token limits)
    max_chars = 8000  # Conservative limit to stay within token budget
    if len(reviews_text) > max_chars:
        reviews_text = reviews_text[:max_chars] + "\n\n[... truncated ...]"
    
    try:
        client = get_openai_client()
        
        prompt = f"""Analyze the following property reviews and create a concise summary (2-3 sentences) highlighting:
1. Key themes and patterns across the reviews
2. Common positive feedback points
3. Common concerns or negative feedback

Reviews:
{reviews_text}

Please provide a balanced summary that captures both positive and negative aspects mentioned in the reviews."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at analyzing customer reviews and extracting key insights. Provide concise, balanced summaries."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        summary = response.choices[0].message.content.strip()
        return summary if summary else "Unable to generate sentiment summary."
    
    except Exception as e:
        print(f"Error generating sentiment summary with OpenAI: {e}")
        # Return a fallback message
        return f"Error generating sentiment summary: {str(e)}"


def get_or_generate_sentiment_summary(property_id: str, force_regenerate: bool = False) -> str:
    """
    Get cached sentiment summary or generate a new one if not available.
    
    Args:
        property_id: ID of the property
        force_regenerate: If True, regenerate even if cached summary exists
        
    Returns:
        Sentiment summary string
    """
    property_repo = PropertyRepository()
    
    # Check if cached summary exists
    if not force_regenerate:
        summary_data = property_repo.get_reviews_summary_by_property_id(property_id)
        if summary_data and summary_data.sentiment_summary:
            print(f"✓ Using cached sentiment summary for property {property_id}")
            return summary_data.sentiment_summary
    
    # Get all reviews for the property
    all_reviews = property_repo.get_reviews_by_property_id(property_id, limit=100)
    
    if not all_reviews:
        return "No reviews available for sentiment analysis."
    
    # Extract review texts (filter out empty ones)
    review_texts = [
        review.review_text 
        for review in all_reviews 
        if review.review_text and review.review_text.strip()
    ]
    
    if not review_texts:
        return "No review text available for sentiment analysis."
    
    print(f"Generating sentiment summary from {len(review_texts)} reviews...")
    
    # Generate summary
    sentiment_summary = generate_sentiment_summary(review_texts)
    
    # Store in database
    success = property_repo.update_reviews_sentiment_summary(property_id, sentiment_summary)
    
    if success:
        print(f"✓ Saved sentiment summary to database")
    else:
        print(f"⚠ Warning: Failed to save sentiment summary to database")
    
    return sentiment_summary


def get_tool_definition():
    """Returns the tool definition for OpenAI function calling."""
    return {
        "type": "function",
        "function": {
            "name": "generate_reviews_sentiment",
            "description": "Generate or retrieve a sentiment summary for a property's reviews. Analyzes review texts using OpenAI to create a concise summary highlighting key themes, positive feedback, and concerns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "string",
                        "description": "Property ID to generate sentiment summary for"
                    },
                    "force_regenerate": {
                        "type": "boolean",
                        "description": "If True, regenerate summary even if cached version exists. Defaults to False.",
                        "default": False
                    }
                },
                "required": ["property_id"]
            }
        }
    }


def execute(arguments):
    """
    Execute the generate_reviews_sentiment tool.
    
    Args:
        arguments: Dictionary containing tool arguments
            - property_id (str): Property ID to generate sentiment summary for
            - force_regenerate (bool, optional): Force regeneration even if cached
            
    Returns:
        Dictionary with sentiment summary and status
    """
    property_id = arguments.get("property_id")
    force_regenerate = arguments.get("force_regenerate", False)
    
    if not property_id:
        return {
            "error": "property_id is required",
            "sentiment_summary": None
        }
    
    try:
        sentiment_summary = get_or_generate_sentiment_summary(property_id, force_regenerate)
        
        return {
            "sentiment_summary": sentiment_summary,
            "success": True
        }
    
    except ValueError as e:
        # API key missing or other value errors
        print(f"Error: {e}")
        return {
            "error": str(e),
            "sentiment_summary": None,
            "success": False
        }
    
    except Exception as e:
        # Other errors (network, API, etc.)
        print(f"Error generating sentiment summary: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to generate sentiment summary: {str(e)}",
            "sentiment_summary": None,
            "success": False
        }


