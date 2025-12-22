"""
Database models and schemas for FionaFast.

Defines data structures for properties, images, and cache entries.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime


class Property:
    """Model for property information."""
    
    def __init__(
        self,
        property_name: Optional[str] = None,
        street_address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        office_hours: Optional[Dict[str, Any]] = None,
        website_url: Optional[str] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.property_name = property_name
        self.street_address = street_address
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.phone = phone
        self.email = email
        self.office_hours = office_hours
        self.website_url = website_url
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert property to dictionary for database insertion."""
        data = {}
        if self.property_name is not None:
            data["property_name"] = self.property_name
        if self.street_address is not None:
            data["street_address"] = self.street_address
        if self.city is not None:
            data["city"] = self.city
        if self.state is not None:
            data["state"] = self.state
        if self.zip_code is not None:
            data["zip_code"] = self.zip_code
        if self.phone is not None:
            data["phone"] = self.phone
        if self.email is not None:
            data["email"] = self.email
        if self.office_hours is not None:
            data["office_hours"] = self.office_hours
        if self.website_url is not None:
            data["website_url"] = self.website_url
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Property":
        """Create Property instance from database dictionary."""
        return cls(
            id=data.get("id"),
            property_name=data.get("property_name"),
            street_address=data.get("street_address"),
            city=data.get("city"),
            state=data.get("state"),
            zip_code=data.get("zip_code"),
            phone=data.get("phone"),
            email=data.get("email"),
            office_hours=data.get("office_hours"),
            website_url=data.get("website_url"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


class PropertyImage:
    """Model for property image information."""
    
    def __init__(
        self,
        image_url: str,
        property_id: Optional[str] = None,
        image_type: Optional[str] = None,
        page_url: Optional[str] = None,
        alt_text: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        is_hidden: Optional[bool] = False,
        image_tags: Optional[List[str]] = None,
        classification_confidence: Optional[float] = None,
        quality_score: Optional[float] = None,
        classification_method: Optional[str] = None,
        classified_at: Optional[datetime] = None
    ):
        self.id = id
        self.property_id = property_id
        self.image_url = image_url
        self.image_type = image_type
        self.page_url = page_url
        self.alt_text = alt_text
        self.width = width
        self.height = height
        self.created_at = created_at
        self.is_hidden = is_hidden if is_hidden is not None else False
        self.image_tags = image_tags if image_tags is not None else []
        self.classification_confidence = classification_confidence
        self.quality_score = quality_score
        self.classification_method = classification_method
        self.classified_at = classified_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert image to dictionary for database insertion."""
        data = {"image_url": self.image_url}
        if self.property_id is not None:
            data["property_id"] = self.property_id
        if self.image_type is not None:
            data["image_type"] = self.image_type
        if self.page_url is not None:
            data["page_url"] = self.page_url
        if self.alt_text is not None:
            data["alt_text"] = self.alt_text
        if self.width is not None:
            data["width"] = self.width
        if self.height is not None:
            data["height"] = self.height
        if self.is_hidden is not None:
            data["is_hidden"] = self.is_hidden
        if self.image_tags is not None and len(self.image_tags) > 0:
            data["image_tags"] = self.image_tags
        if self.classification_confidence is not None:
            data["classification_confidence"] = self.classification_confidence
        if self.quality_score is not None:
            data["quality_score"] = self.quality_score
        if self.classification_method is not None:
            data["classification_method"] = self.classification_method
        if self.classified_at is not None:
            data["classified_at"] = self.classified_at.isoformat() if isinstance(self.classified_at, datetime) else self.classified_at
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PropertyImage":
        """Create PropertyImage instance from database dictionary."""
        # Parse image_tags from JSONB if present
        image_tags = data.get("image_tags")
        if image_tags is None:
            image_tags = []
        elif isinstance(image_tags, str):
            import json
            try:
                image_tags = json.loads(image_tags)
            except (json.JSONDecodeError, TypeError):
                image_tags = []
        elif not isinstance(image_tags, list):
            image_tags = []
        
        # Parse classified_at datetime if present
        classified_at = data.get("classified_at")
        if classified_at and isinstance(classified_at, str):
            try:
                from dateutil import parser
                classified_at = parser.parse(classified_at)
            except (ImportError, ValueError, TypeError):
                pass
        
        return cls(
            id=data.get("id"),
            property_id=data.get("property_id"),
            image_url=data.get("image_url", ""),
            image_type=data.get("image_type"),
            page_url=data.get("page_url"),
            alt_text=data.get("alt_text"),
            width=data.get("width"),
            height=data.get("height"),
            created_at=data.get("created_at"),
            is_hidden=data.get("is_hidden", False),
            image_tags=image_tags,
            classification_confidence=data.get("classification_confidence"),
            quality_score=data.get("quality_score"),
            classification_method=data.get("classification_method"),
            classified_at=classified_at
        )


class PropertyBranding:
    """Model for property branding information."""
    
    def __init__(
        self,
        branding_data: Dict[str, Any],
        property_id: Optional[str] = None,
        website_url: Optional[str] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.property_id = property_id
        self.branding_data = branding_data
        self.website_url = website_url
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert branding to dictionary for database insertion."""
        data = {"branding_data": self.branding_data}
        if self.property_id is not None:
            data["property_id"] = self.property_id
        if self.website_url is not None:
            data["website_url"] = self.website_url
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PropertyBranding":
        """Create PropertyBranding instance from database dictionary."""
        return cls(
            id=data.get("id"),
            property_id=data.get("property_id"),
            branding_data=data.get("branding_data", {}),
            website_url=data.get("website_url"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


class PropertyAmenities:
    """Model for property amenities information."""
    
    def __init__(
        self,
        amenities_data: Dict[str, Any],
        property_id: Optional[str] = None,
        website_url: Optional[str] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.property_id = property_id
        self.amenities_data = amenities_data
        self.website_url = website_url
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert amenities to dictionary for database insertion."""
        data = {"amenities_data": self.amenities_data}
        if self.property_id is not None:
            data["property_id"] = self.property_id
        if self.website_url is not None:
            data["website_url"] = self.website_url
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PropertyAmenities":
        """Create PropertyAmenities instance from database dictionary."""
        return cls(
            id=data.get("id"),
            property_id=data.get("property_id"),
            amenities_data=data.get("amenities_data", {}),
            website_url=data.get("website_url"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


class PropertyFloorPlan:
    """Model for property floor plan information."""
    
    def __init__(
        self,
        name: str,
        property_id: Optional[str] = None,
        size_sqft: Optional[int] = None,
        bedrooms: Optional[int] = None,
        bathrooms: Optional[float] = None,
        price_string: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        available_units: Optional[int] = None,
        is_available: Optional[bool] = None,
        website_url: Optional[str] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.property_id = property_id
        self.name = name
        self.size_sqft = size_sqft
        self.bedrooms = bedrooms
        self.bathrooms = bathrooms
        self.price_string = price_string
        self.min_price = min_price
        self.max_price = max_price
        self.available_units = available_units
        self.is_available = is_available
        self.website_url = website_url
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert floor plan to dictionary for database insertion."""
        data = {"name": self.name}
        if self.property_id is not None:
            data["property_id"] = self.property_id
        if self.size_sqft is not None:
            data["size_sqft"] = self.size_sqft
        if self.bedrooms is not None:
            data["bedrooms"] = self.bedrooms
        if self.bathrooms is not None:
            data["bathrooms"] = self.bathrooms
        if self.price_string is not None:
            data["price_string"] = self.price_string
        if self.min_price is not None:
            data["min_price"] = self.min_price
        if self.max_price is not None:
            data["max_price"] = self.max_price
        if self.available_units is not None:
            data["available_units"] = self.available_units
        if self.is_available is not None:
            data["is_available"] = self.is_available
        if self.website_url is not None:
            data["website_url"] = self.website_url
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PropertyFloorPlan":
        """Create PropertyFloorPlan instance from database dictionary."""
        return cls(
            id=data.get("id"),
            property_id=data.get("property_id"),
            name=data.get("name", ""),
            size_sqft=data.get("size_sqft"),
            bedrooms=data.get("bedrooms"),
            bathrooms=data.get("bathrooms"),
            price_string=data.get("price_string"),
            min_price=data.get("min_price"),
            max_price=data.get("max_price"),
            available_units=data.get("available_units"),
            is_available=data.get("is_available"),
            website_url=data.get("website_url"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


class PropertySpecialOffer:
    """Model for property special offer information."""
    
    def __init__(
        self,
        offer_description: str,
        property_id: Optional[str] = None,
        floor_plan_id: Optional[str] = None,
        valid_until: Optional[str] = None,
        descriptive_text: Optional[str] = None,
        website_url: Optional[str] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.property_id = property_id
        self.floor_plan_id = floor_plan_id
        self.offer_description = offer_description
        self.valid_until = valid_until
        self.descriptive_text = descriptive_text
        self.website_url = website_url
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert special offer to dictionary for database insertion."""
        data = {"offer_description": self.offer_description}
        if self.property_id is not None:
            data["property_id"] = self.property_id
        if self.floor_plan_id is not None:
            data["floor_plan_id"] = self.floor_plan_id
        if self.valid_until is not None:
            data["valid_until"] = self.valid_until
        if self.descriptive_text is not None:
            data["descriptive_text"] = self.descriptive_text
        if self.website_url is not None:
            data["website_url"] = self.website_url
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PropertySpecialOffer":
        """Create PropertySpecialOffer instance from database dictionary."""
        return cls(
            id=data.get("id"),
            property_id=data.get("property_id"),
            floor_plan_id=data.get("floor_plan_id"),
            offer_description=data.get("offer_description", ""),
            valid_until=data.get("valid_until"),
            descriptive_text=data.get("descriptive_text"),
            website_url=data.get("website_url"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


class PropertyReviewsSummary:
    """Model for property reviews summary information."""
    
    def __init__(
        self,
        property_id: str,
        overall_rating: Optional[float] = None,
        review_count: Optional[int] = None,
        google_maps_place_id: Optional[str] = None,
        google_maps_url: Optional[str] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        sentiment_summary: Optional[str] = None,
        sentiment_summary_generated_at: Optional[datetime] = None
    ):
        self.id = id
        self.property_id = property_id
        self.overall_rating = overall_rating
        self.review_count = review_count
        self.google_maps_place_id = google_maps_place_id
        self.google_maps_url = google_maps_url
        self.created_at = created_at
        self.updated_at = updated_at
        self.sentiment_summary = sentiment_summary
        self.sentiment_summary_generated_at = sentiment_summary_generated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert reviews summary to dictionary for database insertion."""
        data = {"property_id": self.property_id}
        if self.overall_rating is not None:
            data["overall_rating"] = self.overall_rating
        if self.review_count is not None:
            data["review_count"] = self.review_count
        if self.google_maps_place_id is not None:
            data["google_maps_place_id"] = self.google_maps_place_id
        if self.google_maps_url is not None:
            data["google_maps_url"] = self.google_maps_url
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PropertyReviewsSummary":
        """Create PropertyReviewsSummary instance from database dictionary."""
        return cls(
            id=data.get("id"),
            property_id=data.get("property_id", ""),
            overall_rating=data.get("overall_rating"),
            review_count=data.get("review_count"),
            google_maps_place_id=data.get("google_maps_place_id"),
            google_maps_url=data.get("google_maps_url"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            sentiment_summary=data.get("sentiment_summary"),
            sentiment_summary_generated_at=data.get("sentiment_summary_generated_at")
        )


class PropertyReview:
    """Model for individual property review information."""
    
    def __init__(
        self,
        property_id: str,
        review_id: str,
        reviewer_name: Optional[str] = None,
        reviewer_id: Optional[str] = None,
        reviewer_url: Optional[str] = None,
        reviewer_photo_url: Optional[str] = None,
        review_text: Optional[str] = None,
        stars: Optional[int] = None,
        published_at: Optional[datetime] = None,
        review_url: Optional[str] = None,
        response_from_owner_text: Optional[str] = None,
        response_from_owner_date: Optional[datetime] = None,
        review_image_urls: Optional[List[str]] = None,
        is_local_guide: Optional[bool] = False,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.property_id = property_id
        self.review_id = review_id
        self.reviewer_name = reviewer_name
        self.reviewer_id = reviewer_id
        self.reviewer_url = reviewer_url
        self.reviewer_photo_url = reviewer_photo_url
        self.review_text = review_text
        self.stars = stars
        self.published_at = published_at
        self.review_url = review_url
        self.response_from_owner_text = response_from_owner_text
        self.response_from_owner_date = response_from_owner_date
        self.review_image_urls = review_image_urls if review_image_urls is not None else []
        self.is_local_guide = is_local_guide if is_local_guide is not None else False
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert review to dictionary for database insertion."""
        data = {
            "property_id": self.property_id,
            "review_id": self.review_id
        }
        if self.reviewer_name is not None:
            data["reviewer_name"] = self.reviewer_name
        if self.reviewer_id is not None:
            data["reviewer_id"] = self.reviewer_id
        if self.reviewer_url is not None:
            data["reviewer_url"] = self.reviewer_url
        if self.reviewer_photo_url is not None:
            data["reviewer_photo_url"] = self.reviewer_photo_url
        if self.review_text is not None:
            data["review_text"] = self.review_text
        if self.stars is not None:
            data["stars"] = self.stars
        if self.published_at is not None:
            data["published_at"] = self.published_at.isoformat() if isinstance(self.published_at, datetime) else self.published_at
        if self.review_url is not None:
            data["review_url"] = self.review_url
        if self.response_from_owner_text is not None:
            data["response_from_owner_text"] = self.response_from_owner_text
        if self.response_from_owner_date is not None:
            data["response_from_owner_date"] = self.response_from_owner_date.isoformat() if isinstance(self.response_from_owner_date, datetime) else self.response_from_owner_date
        if self.review_image_urls is not None:
            data["review_image_urls"] = self.review_image_urls
        if self.is_local_guide is not None:
            data["is_local_guide"] = self.is_local_guide
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PropertyReview":
        """Create PropertyReview instance from database dictionary."""
        # Parse datetime strings if present
        published_at = data.get("published_at")
        if published_at and isinstance(published_at, str):
            try:
                from dateutil import parser
                published_at = parser.parse(published_at)
            except (ImportError, ValueError, TypeError):
                # If dateutil not available or parsing fails, keep as string
                pass
        
        response_from_owner_date = data.get("response_from_owner_date")
        if response_from_owner_date and isinstance(response_from_owner_date, str):
            try:
                from dateutil import parser
                response_from_owner_date = parser.parse(response_from_owner_date)
            except (ImportError, ValueError, TypeError):
                # If dateutil not available or parsing fails, keep as string
                pass
        
        return cls(
            id=data.get("id"),
            property_id=data.get("property_id", ""),
            review_id=data.get("review_id", ""),
            reviewer_name=data.get("reviewer_name"),
            reviewer_id=data.get("reviewer_id"),
            reviewer_url=data.get("reviewer_url"),
            reviewer_photo_url=data.get("reviewer_photo_url"),
            review_text=data.get("review_text"),
            stars=data.get("stars"),
            published_at=published_at,
            review_url=data.get("review_url"),
            response_from_owner_text=data.get("response_from_owner_text"),
            response_from_owner_date=response_from_owner_date,
            review_image_urls=data.get("review_image_urls", []),
            is_local_guide=data.get("is_local_guide", False),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


class Competitor:
    """Model for competitor information."""
    
    def __init__(
        self,
        property_id: str,
        competitor_name: str,
        address: Optional[str] = None,
        street_address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        phone: Optional[str] = None,
        website: Optional[str] = None,
        google_maps_url: Optional[str] = None,
        place_id: Optional[str] = None,
        rating: Optional[float] = None,
        review_count: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        distance_miles: Optional[float] = None,
        id: Optional[str] = None,
        scraped_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.property_id = property_id
        self.competitor_name = competitor_name
        self.address = address
        self.street_address = street_address
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.phone = phone
        self.website = website
        self.google_maps_url = google_maps_url
        self.place_id = place_id
        self.rating = rating
        self.review_count = review_count
        self.latitude = latitude
        self.longitude = longitude
        self.distance_miles = distance_miles
        self.scraped_at = scraped_at
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert competitor to dictionary for database insertion."""
        data = {
            "property_id": self.property_id,
            "competitor_name": self.competitor_name
        }
        if self.address is not None:
            data["address"] = self.address
        if self.street_address is not None:
            data["street_address"] = self.street_address
        if self.city is not None:
            data["city"] = self.city
        if self.state is not None:
            data["state"] = self.state
        if self.zip_code is not None:
            data["zip_code"] = self.zip_code
        if self.phone is not None:
            data["phone"] = self.phone
        if self.website is not None:
            data["website"] = self.website
        if self.google_maps_url is not None:
            data["google_maps_url"] = self.google_maps_url
        if self.place_id is not None:
            data["place_id"] = self.place_id
        if self.rating is not None:
            data["rating"] = self.rating
        if self.review_count is not None:
            data["review_count"] = self.review_count
        if self.latitude is not None:
            data["latitude"] = self.latitude
        if self.longitude is not None:
            data["longitude"] = self.longitude
        if self.distance_miles is not None:
            data["distance_miles"] = self.distance_miles
        if self.scraped_at is not None:
            data["scraped_at"] = self.scraped_at.isoformat() if isinstance(self.scraped_at, datetime) else self.scraped_at
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Competitor":
        """Create Competitor instance from database dictionary."""
        scraped_at = data.get("scraped_at")
        if scraped_at and isinstance(scraped_at, str):
            try:
                from dateutil import parser
                scraped_at = parser.parse(scraped_at)
            except (ImportError, ValueError, TypeError):
                pass
        
        return cls(
            id=data.get("id"),
            property_id=data.get("property_id", ""),
            competitor_name=data.get("competitor_name", ""),
            address=data.get("address"),
            street_address=data.get("street_address"),
            city=data.get("city"),
            state=data.get("state"),
            zip_code=data.get("zip_code"),
            phone=data.get("phone"),
            website=data.get("website"),
            google_maps_url=data.get("google_maps_url"),
            place_id=data.get("place_id"),
            rating=data.get("rating"),
            review_count=data.get("review_count"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            distance_miles=data.get("distance_miles"),
            scraped_at=scraped_at,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


class PropertySocialPost:
    """Model for property social media post information."""
    
    def __init__(
        self,
        property_id: str,
        platform: str,
        post_type: str,
        theme: str,
        image_url: str,
        caption: str,
        ready_to_post_text: str,
        structured_data: Dict[str, Any],
        hashtags: Optional[List[str]] = None,
        cta: Optional[str] = None,
        mockup_image_url: Optional[str] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.property_id = property_id
        self.platform = platform
        self.post_type = post_type
        self.theme = theme
        self.image_url = image_url
        self.caption = caption
        self.hashtags = hashtags if hashtags is not None else []
        self.cta = cta
        self.ready_to_post_text = ready_to_post_text
        self.mockup_image_url = mockup_image_url
        self.structured_data = structured_data
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert social post to dictionary for database insertion."""
        data = {
            "property_id": self.property_id,
            "platform": self.platform,
            "post_type": self.post_type,
            "theme": self.theme,
            "image_url": self.image_url,
            "caption": self.caption,
            "ready_to_post_text": self.ready_to_post_text,
            "structured_data": self.structured_data
        }
        if self.hashtags is not None:
            data["hashtags"] = self.hashtags
        if self.cta is not None:
            data["cta"] = self.cta
        if self.mockup_image_url is not None:
            data["mockup_image_url"] = self.mockup_image_url
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PropertySocialPost":
        """Create PropertySocialPost instance from database dictionary."""
        return cls(
            id=data.get("id"),
            property_id=data.get("property_id", ""),
            platform=data.get("platform", "instagram"),
            post_type=data.get("post_type", "single_image"),
            theme=data.get("theme", ""),
            image_url=data.get("image_url", ""),
            caption=data.get("caption", ""),
            hashtags=data.get("hashtags", []),
            cta=data.get("cta"),
            ready_to_post_text=data.get("ready_to_post_text", ""),
            mockup_image_url=data.get("mockup_image_url"),
            structured_data=data.get("structured_data", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


class OnboardingSession:
    """Model for onboarding session information."""
    
    def __init__(
        self,
        url: str,
        property_id: Optional[str] = None,
        status: str = "started",
        current_step: Optional[str] = None,
        completed_steps: Optional[List[str]] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.property_id = property_id
        self.url = url
        self.status = status
        self.current_step = current_step
        self.completed_steps = completed_steps if completed_steps is not None else []
        self.errors = errors if errors is not None else []
        self.created_at = created_at
        self.updated_at = updated_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert onboarding session to dictionary for database insertion."""
        data = {
            "url": self.url,
            "status": self.status
        }
        if self.property_id is not None:
            data["property_id"] = self.property_id
        if self.current_step is not None:
            data["current_step"] = self.current_step
        if self.completed_steps is not None:
            data["completed_steps"] = self.completed_steps
        if self.errors is not None:
            data["errors"] = self.errors
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OnboardingSession":
        """Create OnboardingSession instance from database dictionary."""
        return cls(
            id=data.get("id"),
            property_id=data.get("property_id"),
            url=data.get("url", ""),
            status=data.get("status", "started"),
            current_step=data.get("current_step"),
            completed_steps=data.get("completed_steps", []),
            errors=data.get("errors", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )

