"""
Tool for generating social media posts for properties.

Uses brand identity, property images, and property data to generate Instagram posts
with AI-generated captions, hashtags, CTAs, and visual mockups.
"""

import os
import json
import random
import requests
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
import io
from database import PropertyRepository, PropertySocialPost


def get_openai_client():
    """Initialize and return OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Please set it in your environment variables."
        )
    return OpenAI(api_key=api_key)


AVAILABLE_THEMES = [
    "lifestyle",
    "amenities",
    "floor_plans",
    "special_offers",
    "reviews",
    "location"
]

CTA_OPTIONS = [
    "Schedule a tour today!",
    "Learn more on our website",
    "Apply now and secure your new home",
    "Contact us to learn more",
    "Visit us today",
    "Book your tour now",
    "Discover your perfect home",
    "Get in touch with our team"
]


def get_theme_tag_mapping(theme: str) -> Optional[List[str]]:
    """
    Map a post theme to preferred image tags.
    
    Args:
        theme: Theme name (e.g., "amenities", "lifestyle")
        
    Returns:
        List of preferred tag names in priority order, or None if no specific preference
    """
    theme_tag_map = {
        "amenities": ["building_amenities", "apartment_amenities"],
        "floor_plans": ["floor_plans"],
        "lifestyle": ["lifestyle"],
        "location": ["exterior", "outdoor_spaces"],
        "special_offers": None,  # No specific preference, use any tag
        "reviews": ["lifestyle"]  # Prefer lifestyle images for reviews
    }
    
    return theme_tag_map.get(theme)


def distribute_themes(post_count: int, themes: Optional[List[str]] = None) -> List[str]:
    """
    Distribute posts across available themes.
    
    Args:
        post_count: Number of posts to generate
        themes: Optional list of specific themes to use (default: all available)
        
    Returns:
        List of theme names for each post
    """
    if themes is None:
        themes = AVAILABLE_THEMES
    
    # Ensure we only use available themes
    themes = [t for t in themes if t in AVAILABLE_THEMES]
    
    if not themes:
        themes = AVAILABLE_THEMES
    
    # Distribute posts across themes
    theme_distribution = []
    theme_index = 0
    
    for i in range(post_count):
        theme_distribution.append(themes[theme_index % len(themes)])
        theme_index += 1
    
    # Shuffle to avoid predictable patterns
    random.shuffle(theme_distribution)
    
    return theme_distribution


def select_image_for_theme(
    images: List[Dict[str, Any]],
    theme: str,
    property_name: str,
    client: OpenAI
) -> Optional[Dict[str, Any]]:
    """
    Use tag-based matching and AI to select the best image for a given theme.
    
    Args:
        images: List of image dictionaries with url, alt_text, image_tags, etc.
        theme: Theme for the post
        property_name: Name of the property
        client: OpenAI client
        
    Returns:
        Selected image dictionary or None
    """
    if not images:
        return None
    
    # Note: Hidden images are already filtered at database level, so we don't need to filter here
    
    # If only one image, return it
    if len(images) == 1:
        return images[0]
    
    # Get preferred tags for this theme
    preferred_tags = get_theme_tag_mapping(theme)
    
    # Filter images by tag matching
    matched_images = []
    
    if preferred_tags:
        # Primary match: images whose first tag matches any preferred tag
        for img in images:
            img_tags = img.get("image_tags", [])
            if img_tags and img_tags[0] in preferred_tags:
                matched_images.append(img)
        
        # Secondary match: if no primary matches, check if any tag matches
        if not matched_images:
            for img in images:
                img_tags = img.get("image_tags", [])
                if img_tags and any(tag in preferred_tags for tag in img_tags):
                    matched_images.append(img)
    
    # Use matched images if available, otherwise fall back to all images
    candidate_images = matched_images if matched_images else images
    
    # If only one candidate, return it
    if len(candidate_images) == 1:
        return candidate_images[0]
    
    # Prepare image information for LLM
    image_info = []
    for idx, img in enumerate(candidate_images):
        img_tags = img.get("image_tags", [])
        info = {
            "index": idx,
            "url": img.get("image_url", ""),
            "alt_text": img.get("alt_text", "") or "",
            "page_url": img.get("page_url", "") or "",
            "tags": img_tags if img_tags else ["uncategorized"]
        }
        image_info.append(info)
    
    # Build tag context for prompt
    tag_context = ""
    if preferred_tags and matched_images:
        tag_context = f"\nNote: These images are pre-filtered to match the theme's preferred tags: {', '.join(preferred_tags)}. Prioritize images with matching tags."
    elif preferred_tags:
        tag_context = f"\nNote: No images matched the preferred tags ({', '.join(preferred_tags)}), so all available images are shown. Select the best match for the theme."
    
    try:
        prompt = f"""You are selecting the best image for an Instagram post about a property called "{property_name}".

Theme: {theme}
{tag_context}

Available images:
{json.dumps(image_info, indent=2)}

Select the BEST image (by index) for this theme. Consider:
- Visual quality and appeal
- Relevance to the theme
- Tag matching (if tags are available)
- Instagram-friendly composition
- How well it represents the property

Return ONLY the index number (0-based) of the selected image, nothing else."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at selecting images for social media marketing."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=10
        )
        
        selected_index_str = response.choices[0].message.content.strip()
        selected_index = int(selected_index_str)
        
        if 0 <= selected_index < len(candidate_images):
            return candidate_images[selected_index]
        else:
            # Fallback to random selection
            return random.choice(candidate_images)
            
    except Exception as e:
        print(f"⚠ Warning: Error in AI image selection: {e}")
        # Fallback to random selection
        return random.choice(candidate_images)


def generate_caption(
    theme: str,
    property_data: Dict[str, Any],
    brand_tone: Optional[Dict[str, Any]],
    theme_specific_data: Dict[str, Any],
    client: OpenAI
) -> str:
    """
    Generate Instagram caption using AI based on theme and brand tone.
    
    Args:
        theme: Theme for the post
        property_data: Basic property information
        brand_tone: Brand tone data (writing style, emotional tone, etc.)
        theme_specific_data: Data specific to the theme (amenities, offers, etc.)
        client: OpenAI client
        
    Returns:
        Generated caption text
    """
    property_name = property_data.get("property_name", "this property")
    city = property_data.get("city", "")
    state = property_data.get("state", "")
    
    # Build tone instructions
    tone_instructions = ""
    if brand_tone:
        writing_style = brand_tone.get("writing_style", {})
        emotional_tone = brand_tone.get("emotional_tone", {})
        tone_tags = brand_tone.get("tone_tags", [])
        
        formality = writing_style.get("formality_level", "moderate")
        warmth = emotional_tone.get("warmth", "neutral")
        energy = emotional_tone.get("energy_level", "moderate")
        
        tone_instructions = f"""
Brand Tone Guidelines:
- Formality: {formality}
- Warmth: {warmth}
- Energy: {energy}
- Tone tags: {', '.join(tone_tags) if tone_tags else 'none specified'}

Match this tone in your caption."""
    
    # Build theme-specific content
    theme_content = ""
    if theme == "lifestyle":
        theme_content = f"""Focus on the living experience and community feel at {property_name}. 
Describe what it's like to live there, the atmosphere, and the lifestyle benefits."""
    elif theme == "amenities":
        amenities = theme_specific_data.get("amenities", {})
        building_amenities = amenities.get("building_amenities", [])
        apartment_amenities = amenities.get("apartment_amenities", [])
        
        amenity_list = []
        if building_amenities:
            amenity_list.extend([a.get("name", "") if isinstance(a, dict) else str(a) for a in building_amenities[:5]])
        if apartment_amenities:
            amenity_list.extend([a.get("name", "") if isinstance(a, dict) else str(a) for a in apartment_amenities[:5]])
        
        theme_content = f"""Highlight the amenities at {property_name}. 
Available amenities include: {', '.join(amenity_list) if amenity_list else 'various amenities'}.
Focus on how these amenities enhance the living experience."""
    elif theme == "floor_plans":
        floor_plans = theme_specific_data.get("floor_plans", [])
        if floor_plans:
            fp = floor_plans[0]  # Use first floor plan
            theme_content = f"""Showcase a floor plan at {property_name}.
Details: {fp.get('name', '')} - {fp.get('bedrooms', 'N/A')} bed, {fp.get('bathrooms', 'N/A')} bath, {fp.get('size_sqft', 'N/A')} sq ft.
Price: {fp.get('price_string', 'Contact for pricing')}"""
        else:
            theme_content = f"""Highlight the floor plans and living spaces available at {property_name}."""
    elif theme == "special_offers":
        offers = theme_specific_data.get("offers", [])
        if offers:
            offer = offers[0]  # Use first offer
            theme_content = f"""Promote a special offer at {property_name}.
Offer: {offer.get('offer_description', '')}
Valid until: {offer.get('valid_until', 'Limited time')}
Details: {offer.get('descriptive_text', '')}"""
        else:
            theme_content = f"""Highlight current promotions and special offers available at {property_name}."""
    elif theme == "reviews":
        reviews_summary = theme_specific_data.get("reviews_summary", {})
        rating = reviews_summary.get("overall_rating")
        review_count = reviews_summary.get("review_count")
        sentiment = reviews_summary.get("sentiment_summary", "")
        
        theme_content = f"""Share what residents love about {property_name}.
Rating: {rating}/5 stars ({review_count} reviews) if available.
Sentiment highlights: {sentiment if sentiment else 'Positive resident feedback'}"""
    elif theme == "location":
        theme_content = f"""Highlight the location benefits of {property_name} in {city}, {state}.
Focus on nearby attractions, commute benefits, neighborhood features, and location advantages."""
    
    try:
        prompt = f"""Write an engaging Instagram caption for a property called "{property_name}" located in {city}, {state}.

Theme: {theme}

{tone_instructions}

{theme_content}

Requirements:
- Length: 75-125 words (Instagram-friendly, concise and punchy)
- Engaging and authentic
- Include emojis sparingly (2-3 max)
- Match the brand tone specified above
- Focus on benefits and lifestyle
- Be inviting and warm
- Be concise - avoid unnecessary words or repetition
- Get to the point quickly while maintaining warmth

Write only the caption text, no hashtags or CTAs."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert social media copywriter specializing in real estate marketing. You write concise, engaging captions optimized for Instagram."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        caption = response.choices[0].message.content.strip()
        return caption
        
    except Exception as e:
        print(f"⚠ Warning: Error generating caption: {e}")
        # Fallback caption
        return f"Welcome to {property_name} in {city}, {state}! Experience the perfect blend of comfort and convenience. 🏠✨"


def generate_hashtags(
    property_data: Dict[str, Any],
    theme: str,
    brand_tone: Optional[Dict[str, Any]],
    client: OpenAI
) -> List[str]:
    """
    Generate relevant hashtags for the post.
    
    Args:
        property_data: Basic property information
        theme: Theme for the post
        client: OpenAI client
        
    Returns:
        List of hashtag strings (without #)
    """
    property_name = property_data.get("property_name", "")
    city = property_data.get("city", "")
    state = property_data.get("state", "")
    
    # Build base hashtags
    base_hashtags = []
    
    # Property name hashtag (sanitized)
    if property_name:
        prop_hashtag = property_name.replace(" ", "").replace("-", "").replace("'", "")
        base_hashtags.append(prop_hashtag)
    
    # Location hashtags
    if city:
        city_hashtag = city.replace(" ", "").replace("-", "")
        base_hashtags.append(f"{city_hashtag}Apartments")
        base_hashtags.append(f"{city_hashtag}Living")
    
    if state:
        base_hashtags.append(f"{state}Apartments")
    
    # Theme-specific hashtags
    theme_hashtags = {
        "lifestyle": ["LuxuryLiving", "CommunityLiving", "ModernLiving"],
        "amenities": ["LuxuryAmenities", "ResortStyleLiving", "AmenityRich"],
        "floor_plans": ["FloorPlans", "NewHome", "SpaciousLiving"],
        "special_offers": ["SpecialOffer", "MoveInSpecial", "LimitedTime"],
        "reviews": ["FiveStarLiving", "ResidentReviews", "HappyResidents"],
        "location": ["PrimeLocation", "ConvenientLiving", "GreatLocation"]
    }
    
    base_hashtags.extend(theme_hashtags.get(theme, []))
    
    # Generic real estate hashtags
    generic_hashtags = [
        "ApartmentsForRent",
        "ApartmentLiving",
        "FindYourHome",
        "Rentals",
        "PropertyManagement"
    ]
    
    try:
        # Use AI to generate additional creative hashtags
        prompt = f"""Generate 5-8 creative, relevant hashtags for an Instagram post about a property called "{property_name}" in {city}, {state}.

Theme: {theme}
Base hashtags already included: {', '.join(base_hashtags[:5])}

Generate additional hashtags that are:
- Relevant to the theme
- Instagram-appropriate
- Not too generic
- Mix of specific and general

Return ONLY a comma-separated list of hashtags (without # symbols), nothing else."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at generating social media hashtags."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=100
        )
        
        ai_hashtags_str = response.choices[0].message.content.strip()
        ai_hashtags = [h.strip().replace("#", "") for h in ai_hashtags_str.split(",") if h.strip()]
        
        # Combine base and AI hashtags, limit to 15 total
        all_hashtags = base_hashtags + ai_hashtags
        return all_hashtags[:15]
        
    except Exception as e:
        print(f"⚠ Warning: Error generating hashtags: {e}")
        # Return base hashtags only
        return base_hashtags[:15]


def generate_cta(used_ctas: List[str]) -> str:
    """
    Generate a CTA, avoiding repetition.
    
    Args:
        used_ctas: List of CTAs already used
        
    Returns:
        CTA string
    """
    available_ctas = [cta for cta in CTA_OPTIONS if cta not in used_ctas]
    
    if not available_ctas:
        # Reset if all CTAs used
        available_ctas = CTA_OPTIONS
    
    return random.choice(available_ctas)


def format_ready_to_post_text(caption: str, hashtags: List[str], cta: str) -> str:
    """
    Format the complete ready-to-post text.
    
    Args:
        caption: Caption text
        hashtags: List of hashtags (without #)
        cta: Call-to-action text
        
    Returns:
        Formatted ready-to-post text
    """
    hashtag_text = " ".join([f"#{tag}" for tag in hashtags])
    
    return f"""{caption}

{cta}

{hashtag_text}"""


def download_image(image_url: str) -> Optional[Image.Image]:
    """
    Download an image from URL and return PIL Image.
    
    Args:
        image_url: URL of the image
        
    Returns:
        PIL Image or None if download fails
    """
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        image = Image.open(io.BytesIO(response.content))
        return image
        
    except Exception as e:
        print(f"⚠ Warning: Error downloading image {image_url}: {e}")
        return None


def hex_to_rgb(hex_color: str) -> tuple:
    """
    Convert hex color to RGB tuple.
    
    Args:
        hex_color: Hex color string (e.g., "#FF0000" or "FF0000")
        
    Returns:
        RGB tuple (r, g, b)
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_brand_colors(branding_data: Optional[Dict[str, Any]]) -> tuple:
    """
    Extract brand colors from branding data.
    
    Args:
        branding_data: Branding data dictionary
        
    Returns:
        Tuple of (primary_color, secondary_color) as RGB tuples, or defaults
    """
    default_primary = (59, 130, 246)  # Blue
    default_secondary = (147, 197, 253)  # Light blue
    
    if not branding_data:
        return (default_primary, default_secondary)
    
    color_scheme = branding_data.get("colorScheme", {})
    colors = branding_data.get("colors", {})
    
    primary_color = None
    secondary_color = None
    
    # Try to get primary color
    if color_scheme:
        primary_color = color_scheme.get("primary") or color_scheme.get("primaryColor")
    
    if not primary_color and colors:
        primary_color = colors.get("primary") or colors.get("primaryColor")
    
    # Try to get secondary color
    if color_scheme:
        secondary_color = color_scheme.get("secondary") or color_scheme.get("accent")
    
    if not secondary_color and colors:
        secondary_color = colors.get("secondary") or colors.get("accent")
    
    # Convert to RGB if found
    if primary_color:
        try:
            if isinstance(primary_color, str):
                primary_color = hex_to_rgb(primary_color)
        except:
            primary_color = default_primary
    else:
        primary_color = default_primary
    
    if secondary_color:
        try:
            if isinstance(secondary_color, str):
                secondary_color = hex_to_rgb(secondary_color)
        except:
            secondary_color = default_secondary
    else:
        secondary_color = default_secondary
    
    return (primary_color, secondary_color)


def create_mockup(
    image_url: str,
    caption: str,
    branding_data: Optional[Dict[str, Any]],
    output_path: str
) -> Optional[str]:
    """
    Create a visual mockup of the Instagram post.
    
    Args:
        image_url: URL of the property image
        caption: Caption text
        branding_data: Branding data for colors/fonts
        output_path: Path to save the mockup
        
    Returns:
        Path to saved mockup or None if failed
    """
    try:
        # Download the image
        img = download_image(image_url)
        if not img:
            return None
        
        # Instagram square format: 1080x1080
        target_size = (1080, 1080)
        
        # Resize and crop to square
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Create square canvas
        mockup = Image.new("RGB", target_size, (255, 255, 255))
        
        # Center the image
        img_width, img_height = img.size
        x_offset = (target_size[0] - img_width) // 2
        y_offset = (target_size[1] - img_height) // 2
        mockup.paste(img, (x_offset, y_offset))
        
        # Get brand colors
        primary_color, secondary_color = get_brand_colors(branding_data)
        
        # Add border/frame (10px border)
        border_width = 10
        draw = ImageDraw.Draw(mockup)
        draw.rectangle(
            [(border_width, border_width), (target_size[0] - border_width, target_size[1] - border_width)],
            outline=primary_color,
            width=border_width
        )
        
        # Add caption preview overlay at bottom (first 2-3 lines)
        caption_lines = caption.split("\n")[:3]
        caption_preview = "\n".join(caption_lines)
        
        # Try to use a nice font, fallback to default
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
        
        # Create text overlay background
        overlay_height = 200
        overlay = Image.new("RGBA", (target_size[0], overlay_height), (0, 0, 0, 200))
        mockup.paste(overlay, (0, target_size[1] - overlay_height), overlay)
        
        # Add text
        draw = ImageDraw.Draw(mockup)
        text_y = target_size[1] - overlay_height + 20
        
        # Wrap text to fit
        max_width = target_size[0] - 40
        words = caption_preview.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Draw text lines
        for i, line in enumerate(lines[:3]):  # Max 3 lines
            draw.text((20, text_y + i * 30), line, fill=(255, 255, 255), font=font)
        
        # Save mockup
        mockup.save(output_path, "PNG", quality=95)
        return output_path
        
    except Exception as e:
        print(f"⚠ Warning: Error creating mockup: {e}")
        return None


def get_tool_definition():
    """Returns the tool definition for OpenAI function calling."""
    return {
        "type": "function",
        "function": {
            "name": "generate_social_posts",
            "description": "Generate Instagram single-image social media posts for a property using brand identity, images, and property data. Creates AI-generated captions, hashtags, CTAs, and visual mockups. Posts are saved to the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "string",
                        "description": "The ID of the property to generate posts for"
                    },
                    "post_count": {
                        "type": "integer",
                        "description": "Number of posts to generate (default: 8, range: 5-10)",
                        "default": 8
                    },
                    "themes": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["lifestyle", "amenities", "floor_plans", "special_offers", "reviews", "location"]
                        },
                        "description": "Optional list of specific themes to cover. If not provided, uses all available themes."
                    }
                },
                "required": ["property_id"]
            }
        }
    }


def execute(arguments):
    """
    Execute the generate_social_posts tool.
    
    Generates Instagram posts for a property using brand identity, images, and property data.
    
    Args:
        arguments: Dictionary containing tool arguments
            - property_id (str, required): Property ID
            - post_count (int, optional): Number of posts (default: 8)
            - themes (list, optional): Specific themes to use
            
    Returns:
        Dictionary with generated posts and summary
    """
    property_id = arguments.get("property_id")
    post_count = arguments.get("post_count", 8)
    themes = arguments.get("themes")
    
    if not property_id:
        return {
            "error": "property_id is required",
            "posts": []
        }
    
    # Validate post count
    post_count = max(5, min(10, post_count))
    
    print(f"Generating {post_count} social media posts for property {property_id}")
    
    try:
        # Initialize clients
        openai_client = get_openai_client()
        property_repo = PropertyRepository()
        
        # 1. Collect all data
        print("📊 Collecting property data...")
        
        property_obj = property_repo.get_property_by_id(property_id)
        if not property_obj:
            return {
                "error": f"Property with ID {property_id} not found",
                "posts": []
            }
        
        property_data = {
            "property_name": property_obj.property_name or "",
            "city": property_obj.city or "",
            "state": property_obj.state or "",
            "street_address": property_obj.street_address or "",
            "website_url": property_obj.website_url or ""
        }
        
        # Get brand identity
        branding = property_repo.get_branding_by_property_id(property_id)
        branding_data = branding.branding_data if branding else None
        brand_tone = branding_data.get("tone") if branding_data else None
        
        # Get images (exclude hidden at database level)
        images = property_repo.get_visible_property_images(property_id)
        image_dicts = [
            {
                "image_url": img.image_url,
                "alt_text": img.alt_text,
                "page_url": img.page_url,
                "is_hidden": img.is_hidden,
                "image_tags": img.image_tags or []
            }
            for img in images
        ]
        
        if not image_dicts:
            return {
                "error": "No images found for this property. Please extract images first.",
                "posts": []
            }
        
        # Get amenities
        amenities_obj = property_repo.get_amenities_by_property_id(property_id)
        amenities_data = amenities_obj.amenities_data if amenities_obj else {}
        
        # Get floor plans
        floor_plans = property_repo.get_floor_plans_by_property_id(property_id)
        floor_plan_dicts = [
            {
                "name": fp.name,
                "size_sqft": fp.size_sqft,
                "bedrooms": fp.bedrooms,
                "bathrooms": fp.bathrooms,
                "price_string": fp.price_string,
                "min_price": fp.min_price,
                "max_price": fp.max_price,
                "available_units": fp.available_units,
                "is_available": fp.is_available
            }
            for fp in floor_plans
        ]
        
        # Get special offers
        offers = property_repo.get_special_offers_by_property_id(property_id)
        offer_dicts = [
            {
                "offer_description": offer.offer_description,
                "valid_until": offer.valid_until,
                "descriptive_text": offer.descriptive_text,
                "floor_plan_id": offer.floor_plan_id
            }
            for offer in offers
        ]
        
        # Get reviews summary
        reviews_summary_obj = property_repo.get_reviews_summary_by_property_id(property_id)
        reviews_summary_data = {
            "overall_rating": reviews_summary_obj.overall_rating if reviews_summary_obj else None,
            "review_count": reviews_summary_obj.review_count if reviews_summary_obj else None,
            "sentiment_summary": reviews_summary_obj.sentiment_summary if reviews_summary_obj else None
        }
        
        print(f"✓ Collected data: {len(image_dicts)} images, branding: {'yes' if branding_data else 'no'}")
        
        # 2. Distribute themes
        theme_distribution = distribute_themes(post_count, themes)
        print(f"✓ Theme distribution: {theme_distribution}")
        
        # 3. Generate posts
        generated_posts = []
        used_ctas = []
        used_images = set()  # Track used images to avoid duplicates
        
        # Create output directory for mockups
        mockup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mockups")
        os.makedirs(mockup_dir, exist_ok=True)
        
        for i, theme in enumerate(theme_distribution):
            print(f"\n📝 Generating post {i+1}/{post_count} (theme: {theme})...")
            
            # Select image
            available_images = [img for img in image_dicts if img["image_url"] not in used_images]
            if not available_images:
                # Reset if all images used
                used_images.clear()
                available_images = image_dicts
            
            selected_image = select_image_for_theme(
                available_images,
                theme,
                property_data["property_name"],
                openai_client
            )
            
            if not selected_image:
                print(f"⚠ Warning: Could not select image for post {i+1}, skipping")
                continue
            
            used_images.add(selected_image["image_url"])
            
            # Prepare theme-specific data
            theme_data = {
                "amenities": amenities_data,
                "floor_plans": floor_plan_dicts,
                "offers": offer_dicts,
                "reviews_summary": reviews_summary_data
            }
            
            # Generate caption
            caption = generate_caption(
                theme,
                property_data,
                brand_tone,
                theme_data,
                openai_client
            )
            
            # Generate hashtags
            hashtags = generate_hashtags(
                property_data,
                theme,
                brand_tone,
                openai_client
            )
            
            # Generate CTA
            cta = generate_cta(used_ctas)
            used_ctas.append(cta)
            
            # Format ready-to-post text
            ready_to_post = format_ready_to_post_text(caption, hashtags, cta)
            
            # Create mockup
            mockup_filename = f"post_{property_id}_{i+1}.png"
            mockup_path = os.path.join(mockup_dir, mockup_filename)
            mockup_url = None
            
            mockup_result = create_mockup(
                selected_image["image_url"],
                caption,
                branding_data,
                mockup_path
            )
            
            if mockup_result:
                # For now, store relative path. In production, upload to cloud storage
                mockup_url = f"mockups/{mockup_filename}"
            
            # Create structured data
            structured_data = {
                "theme": theme,
                "image": {
                    "url": selected_image["image_url"],
                    "alt_text": selected_image.get("alt_text"),
                    "page_url": selected_image.get("page_url")
                },
                "caption": caption,
                "hashtags": hashtags,
                "cta": cta,
                "platform": "instagram",
                "post_type": "single_image"
            }
            
            # Save to database
            social_post = PropertySocialPost(
                property_id=property_id,
                platform="instagram",
                post_type="single_image",
                theme=theme,
                image_url=selected_image["image_url"],
                caption=caption,
                hashtags=hashtags,
                cta=cta,
                ready_to_post_text=ready_to_post,
                mockup_image_url=mockup_url,
                structured_data=structured_data
            )
            
            post_id = property_repo.create_social_post(social_post)
            
            if post_id:
                print(f"✓ Post {i+1} created (ID: {post_id})")
                generated_posts.append({
                    "id": post_id,
                    "theme": theme,
                    "image_url": selected_image["image_url"],
                    "caption": caption,
                    "hashtags": hashtags,
                    "cta": cta,
                    "ready_to_post_text": ready_to_post,
                    "mockup_image_url": mockup_url
                })
            else:
                print(f"⚠ Warning: Failed to save post {i+1} to database")
        
        print(f"\n✅ Successfully generated {len(generated_posts)} posts")
        
        return {
            "posts": generated_posts,
            "count": len(generated_posts),
            "property_id": property_id
        }
        
    except ValueError as e:
        print(f"Error: {e}")
        return {
            "error": str(e),
            "posts": []
        }
    except Exception as e:
        print(f"Error generating social posts: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to generate social posts: {str(e)}",
            "posts": []
        }

