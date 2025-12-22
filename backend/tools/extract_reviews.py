"""
Tool for extracting Google Maps reviews for properties.

Uses Apify Google Maps Reviews Scraper Actor to find and scrape reviews from Google Maps.
Stores overall rating, review count, and individual reviews in the database.
"""

import os
import urllib.parse
from datetime import datetime
from apify_client import ApifyClient
from database import PropertyRepository


def get_apify_client():
    """Initialize and return Apify client with API token from environment."""
    token = os.getenv("APIFY_API_TOKEN")
    if not token:
        raise ValueError(
            "APIFY_API_TOKEN not found. Please set it in your environment variables."
        )
    return ApifyClient(token=token)


def construct_google_maps_search_url(property_name: str, street_address: str = None, city: str = None, state: str = None) -> str:
    """
    Construct a Google Maps search URL from property information.
    
    Args:
        property_name: Name of the property
        street_address: Street address (optional)
        city: City name (optional)
        state: State abbreviation (optional)
        
    Returns:
        Google Maps search URL
    """
    # Build search query from available information
    query_parts = [property_name]
    if street_address:
        query_parts.append(street_address)
    if city:
        query_parts.append(city)
    if state:
        query_parts.append(state)
    
    query = " ".join(query_parts)
    encoded_query = urllib.parse.quote(query)
    
    return f"https://www.google.com/maps/search/?api=1&query={encoded_query}"


def transform_review_data(apify_review: dict) -> dict:
    """
    Transform Apify Actor output format to our review format.
    
    Args:
        apify_review: Dictionary from Apify Actor with review data
        
    Returns:
        Dictionary with our review format
    """
    # Parse published date if available
    published_at = None
    if apify_review.get("publishedAtDate"):
        try:
            # Handle ISO format datetime string
            published_at_str = apify_review.get("publishedAtDate")
            if isinstance(published_at_str, str):
                from dateutil import parser
                published_at = parser.parse(published_at_str)
            elif isinstance(published_at_str, datetime):
                published_at = published_at_str
        except Exception as e:
            print(f"Warning: Could not parse publishedAtDate: {e}")
    
    # Parse response date if available
    response_date = None
    if apify_review.get("responseFromOwnerDate"):
        try:
            response_date_str = apify_review.get("responseFromOwnerDate")
            if isinstance(response_date_str, str):
                from dateutil import parser
                response_date = parser.parse(response_date_str)
            elif isinstance(response_date_str, datetime):
                response_date = response_date_str
        except Exception as e:
            print(f"Warning: Could not parse responseFromOwnerDate: {e}")
    
    return {
        "review_id": apify_review.get("reviewId", ""),
        "reviewer_name": apify_review.get("name"),
        "reviewer_id": apify_review.get("reviewerId"),
        "reviewer_url": apify_review.get("reviewerUrl"),
        "reviewer_photo_url": apify_review.get("reviewerPhotoUrl"),
        "review_text": apify_review.get("text"),
        "stars": apify_review.get("stars"),
        "published_at": published_at.isoformat() if published_at else None,
        "review_url": apify_review.get("reviewUrl"),
        "response_from_owner_text": apify_review.get("responseFromOwnerText"),
        "response_from_owner_date": response_date.isoformat() if response_date else None,
        "review_image_urls": apify_review.get("reviewImageUrls", []),
        "is_local_guide": apify_review.get("isLocalGuide", False)
    }


def get_tool_definition():
    """Returns the tool definition for OpenAI function calling."""
    return {
        "type": "function",
        "function": {
            "name": "extract_reviews",
            "description": "Extract Google Maps reviews for a property. Automatically searches Google Maps using property name and address, then scrapes reviews using Apify Actor. Stores overall rating, review count, and individual reviews in the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "string",
                        "description": "Property ID to scrape reviews for. If not provided, will use url to find property."
                    },
                    "url": {
                        "type": "string",
                        "description": "Property website URL. Used to find property in database if property_id not provided."
                    },
                    "google_maps_url": {
                        "type": "string",
                        "description": "Direct Google Maps URL or Place ID. If provided, skips search step and uses this URL directly."
                    },
                    "max_reviews": {
                        "type": "integer",
                        "description": "Maximum number of reviews to scrape. Defaults to 100.",
                        "default": 100
                    },
                    "use_cache": {
                        "type": "boolean",
                        "description": "Whether to use cached data if available. Not currently implemented for reviews."
                    },
                    "force_refresh": {
                        "type": "boolean",
                        "description": "Force fresh scrape even if cache exists. Defaults to False.",
                        "default": False
                    }
                },
                "required": []
            }
        }
    }


def execute(arguments):
    """
    Execute the extract_reviews tool.
    
    Finds property on Google Maps and scrapes reviews using Apify Actor.
    Stores summary and individual reviews in the database.
    
    Args:
        arguments: Dictionary containing tool arguments
            - property_id (str, optional): Property ID to scrape reviews for
            - url (str, optional): Property website URL
            - google_maps_url (str, optional): Direct Google Maps URL/Place ID
            - max_reviews (int, optional): Maximum number of reviews (default: 100)
            - use_cache (bool, optional): Whether to use cached data
            - force_refresh (bool, optional): Force fresh scrape
            
    Returns:
        Dictionary with reviews summary and count of reviews added
    """
    property_id = arguments.get("property_id")
    url = arguments.get("url")
    google_maps_url = arguments.get("google_maps_url")
    max_reviews = arguments.get("max_reviews", 100)
    force_refresh = arguments.get("force_refresh", False)
    
    # Get property from database
    property_repo = PropertyRepository()
    property_obj = None
    
    if property_id:
        property_obj = property_repo.get_property_by_id(property_id)
    elif url:
        property_obj = property_repo.get_property_by_website_url(url)
    
    if not property_obj:
        return {
            "error": "Property not found. Please provide either property_id or url to find the property.",
            "overall_rating": None,
            "review_count": None,
            "reviews_added": 0
        }
    
    # Determine Google Maps URL
    maps_url = google_maps_url
    if not maps_url:
        # Construct search URL from property information
        if not property_obj.property_name:
            return {
                "error": "Property name is required to search Google Maps. Please ensure property information has been extracted first.",
                "overall_rating": None,
                "review_count": None,
                "reviews_added": 0
            }
        
        maps_url = construct_google_maps_search_url(
            property_name=property_obj.property_name,
            street_address=property_obj.street_address,
            city=property_obj.city,
            state=property_obj.state
        )
        print(f"Constructed Google Maps search URL: {maps_url}")
    else:
        print(f"Using provided Google Maps URL: {maps_url}")
    
    # Call Apify Google Maps Reviews Scraper Actor
    try:
        print(f"Scraping Google Maps reviews using Apify Actor...")
        apify_client = get_apify_client()
        
        # Prepare Actor input
        actor_input = {
            "startUrls": [{"url": maps_url}],
            "maxReviews": max_reviews,
            "reviewsSort": "newest",
            "language": "en",
            "reviewsOrigin": "google",  # Google-only reviews
            "personalData": True  # Store reviewer personal data
        }
        
        # Run the Actor and wait for it to finish
        print(f"Running Apify Actor: compass/google-maps-reviews-scraper...")
        run = apify_client.actor("compass/google-maps-reviews-scraper").call(run_input=actor_input)
        
        # Fetch results from the dataset
        print(f"Fetching results from dataset {run['defaultDatasetId']}...")
        dataset = apify_client.dataset(run["defaultDatasetId"])
        
        # Get all review items
        reviews = []
        summary_data = None
        
        for item in dataset.iterate_items():
            # First item typically contains place summary data
            if not summary_data and (item.get("totalScore") is not None or item.get("reviewsCount") is not None):
                summary_data = {
                    "overall_rating": item.get("totalScore"),
                    "review_count": item.get("reviewsCount"),
                    "google_maps_place_id": item.get("placeId"),
                    "google_maps_url": item.get("url")
                }
            
            # Extract review data (skip if it's just place metadata without review content)
            if item.get("reviewId") or item.get("text") or item.get("stars"):
                reviews.append(item)
        
        if not reviews:
            return {
                "error": "No reviews found for this property on Google Maps.",
                "overall_rating": summary_data.get("overall_rating") if summary_data else None,
                "review_count": summary_data.get("review_count") if summary_data else None,
                "reviews_added": 0
            }
        
        print(f"✓ Found {len(reviews)} reviews from Apify Actor")
        
        # Transform reviews to our format
        transformed_reviews = []
        for review in reviews:
            transformed = transform_review_data(review)
            if transformed.get("review_id"):  # Only include reviews with valid review_id
                transformed_reviews.append(transformed)
        
        # Save summary to database
        if summary_data:
            summary_id = property_repo.create_or_update_reviews_summary(
                property_id=property_obj.id,
                overall_rating=summary_data.get("overall_rating"),
                review_count=summary_data.get("review_count"),
                google_maps_place_id=summary_data.get("google_maps_place_id"),
                google_maps_url=summary_data.get("google_maps_url")
            )
            if summary_id:
                print(f"✓ Saved reviews summary to database (ID: {summary_id})")
        
        # Save individual reviews (incremental - only new ones)
        reviews_added = property_repo.add_property_reviews(property_obj.id, transformed_reviews)
        
        print(f"✓ Added {reviews_added} new reviews to database (skipped {len(transformed_reviews) - reviews_added} duplicates)")
        
        # Generate sentiment summary if reviews were added or if summary doesn't exist
        sentiment_summary = None
        existing_summary = property_repo.get_reviews_summary_by_property_id(property_obj.id)
        # Safely check for sentiment_summary attribute (may not exist on older model instances)
        has_sentiment_summary = existing_summary and hasattr(existing_summary, 'sentiment_summary') and existing_summary.sentiment_summary
        if reviews_added > 0 or not existing_summary or not has_sentiment_summary:
            try:
                from .generate_reviews_sentiment import get_or_generate_sentiment_summary
                print(f"Generating sentiment summary...")
                sentiment_summary = get_or_generate_sentiment_summary(property_obj.id, force_regenerate=(reviews_added > 0))
                print(f"✓ Generated sentiment summary")
            except Exception as e:
                print(f"⚠ Warning: Failed to generate sentiment summary: {e}")
                # Don't fail the whole operation if sentiment generation fails
        
        # Display summary
        print(f"\n[Extracted Reviews Information]")
        print("=" * 60)
        if summary_data and summary_data.get("overall_rating"):
            print(f"Overall Rating: {summary_data['overall_rating']:.2f} / 5.0")
        else:
            print(f"Overall Rating: Not available")
        
        if summary_data and summary_data.get("review_count"):
            print(f"Total Reviews: {summary_data['review_count']}")
        else:
            print(f"Total Reviews: {len(transformed_reviews)}")
        
        print(f"New Reviews Added: {reviews_added}")
        print(f"Total Reviews Scraped: {len(transformed_reviews)}")
        print("=" * 60)
        
        return {
            "overall_rating": summary_data.get("overall_rating") if summary_data else None,
            "review_count": summary_data.get("review_count") if summary_data else len(transformed_reviews),
            "reviews_added": reviews_added,
            "reviews_scraped": len(transformed_reviews),
            "google_maps_place_id": summary_data.get("google_maps_place_id") if summary_data else None,
            "google_maps_url": summary_data.get("google_maps_url") if summary_data else maps_url,
            "sentiment_summary": sentiment_summary
        }
    
    except ValueError as e:
        # API key missing or other value errors
        print(f"Error: {e}")
        return {
            "error": str(e),
            "overall_rating": None,
            "review_count": None,
            "reviews_added": 0
        }
    
    except Exception as e:
        # Other errors (network, API, etc.)
        print(f"Error extracting reviews: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to extract reviews: {str(e)}",
            "overall_rating": None,
            "review_count": None,
            "reviews_added": 0
        }

