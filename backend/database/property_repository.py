"""
Repository for property-related database operations.

Handles CRUD operations for properties and property images.
"""

from typing import Optional, List, Dict, Any, Set
from .supabase_client import get_supabase_client
from .models import Property, PropertyImage, PropertyBranding, PropertyAmenities, PropertyFloorPlan, PropertySpecialOffer, PropertyReviewsSummary, PropertyReview, Competitor, PropertySocialPost


class PropertyRepository:
    """Repository for managing properties in the database."""
    
    def __init__(self):
        """Initialize repository with Supabase client."""
        self.client = get_supabase_client()
    
    def create_property(self, property: Property) -> Optional[str]:
        """
        Create a new property in the database.
        
        Args:
            property: Property instance to create
            
        Returns:
            ID of the created property, or None if creation failed
        """
        try:
            data = property.to_dict()
            response = self.client.table("properties").insert(data).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0].get("id")
            return None
        except Exception as e:
            print(f"Error creating property: {e}")
            return None
    
    def get_property_by_website_url(self, website_url: str) -> Optional[Property]:
        """
        Get property by website URL.
        
        Args:
            website_url: Website URL to search for
            
        Returns:
            Property instance if found, None otherwise
        """
        try:
            response = self.client.table("properties").select("*").eq("website_url", website_url).execute()
            
            if response.data and len(response.data) > 0:
                return Property.from_dict(response.data[0])
            return None
        except Exception as e:
            print(f"Error getting property by website URL: {e}")
            return None
    
    def get_property_by_id(self, property_id: str) -> Optional[Property]:
        """
        Get property by ID.
        
        Args:
            property_id: Property ID
            
        Returns:
            Property instance if found, None otherwise
        """
        try:
            response = self.client.table("properties").select("*").eq("id", property_id).execute()
            
            if response.data and len(response.data) > 0:
                return Property.from_dict(response.data[0])
            return None
        except Exception as e:
            print(f"Error getting property by ID: {e}")
            return None
    
    def get_property_by_name(self, property_name: str) -> Optional[Property]:
        """
        Get property by name (case-insensitive partial match).
        
        Args:
            property_name: Property name to search for
            
        Returns:
            Property instance if found, None otherwise
        """
        try:
            # Get all properties and filter by name (case-insensitive)
            # This is more reliable than ilike which may not be supported in all Supabase clients
            response = self.client.table("properties").select("*").execute()
            
            if response.data:
                property_name_lower = property_name.lower().strip()
                for prop_data in response.data:
                    prop_name = prop_data.get("property_name", "")
                    if property_name_lower in prop_name.lower():
                        return Property.from_dict(prop_data)
            return None
        except Exception as e:
            print(f"Error getting property by name: {e}")
            return None
    
    def update_property(self, property_id: str, property: Property) -> bool:
        """
        Update an existing property.
        
        Args:
            property_id: ID of property to update
            property: Property instance with updated data
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            data = property.to_dict()
            response = self.client.table("properties").update(data).eq("id", property_id).execute()
            return response.data is not None
        except Exception as e:
            print(f"Error updating property: {e}")
            return False
    
    def create_or_update_property(self, property: Property) -> Optional[str]:
        """
        Create a new property or update existing one based on website_url.
        
        Args:
            property: Property instance to create or update
            
        Returns:
            ID of the property (created or updated)
        """
        if property.website_url:
            existing = self.get_property_by_website_url(property.website_url)
            if existing:
                # Update existing property
                property.id = existing.id
                if self.update_property(existing.id, property):
                    return existing.id
                return None
        
        # Create new property
        return self.create_property(property)
    
    def get_existing_image_urls(self, property_id: str) -> Set[str]:
        """
        Get set of existing image URLs for a property (for duplicate checking).
        
        Args:
            property_id: ID of the property
            
        Returns:
            Set of image URLs that already exist
        """
        try:
            response = self.client.table("property_images").select("image_url").eq("property_id", property_id).execute()
            
            if response.data:
                return {img.get("image_url") for img in response.data if img.get("image_url")}
            return set()
        except Exception as e:
            print(f"Error getting existing image URLs: {e}")
            return set()
    
    def add_property_images(self, property_id: str, images: List[Dict[str, Any]]) -> int:
        """
        Add images for a property, skipping duplicates based on image_url.
        
        Args:
            property_id: ID of the property
            images: List of image dictionaries with url, page_url, alt, width, height, etc.
            
        Returns:
            Number of new images added (excluding duplicates)
        """
        if not images:
            return 0
        
        try:
            # Get existing image URLs to avoid duplicates
            existing_image_urls = self.get_existing_image_urls(property_id)
            
            # Filter out images that already exist
            image_records = []
            for img in images:
                image_url = img.get("url", "")
                # Skip if this image URL already exists for this property
                if image_url and image_url in existing_image_urls:
                    continue
                
                image_record = {
                    "property_id": property_id,
                    "image_url": image_url,
                    "page_url": img.get("page_url"),
                    "alt_text": img.get("alt"),
                    "width": img.get("width"),
                    "height": img.get("height"),
                    "image_type": img.get("image_type")  # Can be set by caller
                }
                image_records.append(image_record)
                # Add to existing set to avoid duplicates within this batch
                if image_url:
                    existing_image_urls.add(image_url)
            
            if not image_records:
                return 0
            
            # Use upsert to handle any race conditions (will respect unique constraint if it exists)
            response = self.client.table("property_images").upsert(image_records).execute()
            return len(response.data) if response.data else 0
        except Exception as e:
            print(f"Error adding property images: {e}")
            return 0
    
    def get_property_images(self, property_id: str, exclude_hidden: bool = False) -> List[PropertyImage]:
        """
        Get all images for a property.
        
        Args:
            property_id: ID of the property
            exclude_hidden: If True, only return images where is_hidden is False
            
        Returns:
            List of PropertyImage instances
        """
        try:
            query = self.client.table("property_images").select("*").eq("property_id", property_id)
            
            if exclude_hidden:
                query = query.eq("is_hidden", False)
            
            response = query.execute()
            
            if response.data:
                return [PropertyImage.from_dict(img) for img in response.data]
            return []
        except Exception as e:
            print(f"Error getting property images: {e}")
            return []
    
    def get_visible_property_images(self, property_id: str) -> List[PropertyImage]:
        """
        Get only visible (non-hidden) images for a property.
        
        Args:
            property_id: ID of the property
            
        Returns:
            List of PropertyImage instances (excluding hidden images)
        """
        return self.get_property_images(property_id, exclude_hidden=True)
    
    def update_image_visibility(self, image_id: str, is_hidden: bool) -> bool:
        """
        Update the visibility (hidden/visible) of an image.
        
        Args:
            image_id: ID of the image to update
            is_hidden: True to hide the image, False to show it
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            response = self.client.table("property_images").update({"is_hidden": is_hidden}).eq("id", image_id).execute()
            return response.data is not None
        except Exception as e:
            print(f"Error updating image visibility: {e}")
            return False
    
    def update_image_classification(
        self,
        image_id: str,
        tags: List[str],
        confidence: float,
        quality_score: float,
        method: str = "ai_vision"
    ) -> bool:
        """
        Update classification data for an image.
        
        Args:
            image_id: ID of the image to update
            tags: List of tag strings
            confidence: Overall classification confidence (0.0-1.0)
            quality_score: Image quality score (0.0-1.0)
            method: Classification method ('ai_vision', 'manual', etc.)
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            from datetime import datetime
            update_data = {
                "image_tags": tags,
                "classification_confidence": confidence,
                "quality_score": quality_score,
                "classification_method": method,
                "classified_at": datetime.now().isoformat()
            }
            response = self.client.table("property_images").update(update_data).eq("id", image_id).execute()
            return response.data is not None and len(response.data) > 0
        except Exception as e:
            print(f"Error updating image classification: {e}")
            return False
    
    def update_image_classification_by_url(
        self,
        property_id: str,
        image_url: str,
        tags: List[str],
        confidence: float,
        quality_score: float,
        method: str = "ai_vision"
    ) -> bool:
        """
        Update classification data for an image by URL.
        
        Args:
            property_id: ID of the property
            image_url: URL of the image to update
            tags: List of tag strings
            confidence: Overall classification confidence (0.0-1.0)
            quality_score: Image quality score (0.0-1.0)
            method: Classification method ('ai_vision', 'manual', etc.)
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Find image by property_id and image_url
            response = self.client.table("property_images").select("id").eq("property_id", property_id).eq("image_url", image_url).execute()
            
            if not response.data or len(response.data) == 0:
                print(f"Image not found: {image_url} for property {property_id}")
                return False
            
            image_id = response.data[0]["id"]
            return self.update_image_classification(image_id, tags, confidence, quality_score, method)
        except Exception as e:
            print(f"Error updating image classification by URL: {e}")
            return False
    
    def get_images_by_tag(self, property_id: str, tag: str) -> List[PropertyImage]:
        """
        Get images for a property filtered by tag.
        
        Args:
            property_id: ID of the property
            tag: Tag to filter by
            
        Returns:
            List of PropertyImage instances matching the tag
        """
        try:
            response = self.client.table("property_images").select("*").eq("property_id", property_id).contains("image_tags", [tag]).execute()
            
            if response.data:
                return [PropertyImage.from_dict(img) for img in response.data]
            return []
        except Exception as e:
            print(f"Error getting images by tag: {e}")
            return []
    
    def get_images_grouped_by_tags(self, property_id: str) -> Dict[str, List[PropertyImage]]:
        """
        Get images for a property grouped by their primary tag.
        
        Args:
            property_id: ID of the property
            
        Returns:
            Dictionary mapping tag names to lists of PropertyImage instances
        """
        try:
            images = self.get_property_images(property_id)
            grouped = {}
            
            for image in images:
                # Use first tag as primary tag, or 'uncategorized' if no tags
                tags = image.image_tags or []
                primary_tag = tags[0] if tags else "uncategorized"
                
                if primary_tag not in grouped:
                    grouped[primary_tag] = []
                grouped[primary_tag].append(image)
            
            return grouped
        except Exception as e:
            print(f"Error getting images grouped by tags: {e}")
            return {}
    
    def create_extraction_session(
        self,
        property_id: Optional[str],
        website_url: str,
        status: str = "completed",
        notes: Optional[str] = None
    ) -> Optional[str]:
        """
        Create an extraction session record.
        
        Args:
            property_id: ID of the property (can be None)
            website_url: Website URL that was extracted
            status: Status of extraction ('completed', 'failed', 'in_progress')
            notes: Optional notes about the extraction
            
        Returns:
            ID of the extraction session, or None if creation failed
        """
        try:
            data = {
                "website_url": website_url,
                "status": status
            }
            if property_id:
                data["property_id"] = property_id
            if notes:
                data["notes"] = notes
            
            response = self.client.table("extraction_sessions").insert(data).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0].get("id")
            return None
        except Exception as e:
            print(f"Error creating extraction session: {e}")
            return None
    
    def create_or_update_branding(
        self,
        property_id: str,
        branding_data: Dict[str, Any],
        website_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Create or update branding data for a property.
        
        Args:
            property_id: ID of the property
            branding_data: Dictionary containing branding information from Firecrawl
            website_url: Optional website URL for reference
            
        Returns:
            ID of the branding record, or None if creation/update failed
        """
        try:
            # Don't save empty branding data
            if not branding_data or branding_data == {}:
                print(f"⚠ Warning: Attempted to save empty branding data - skipping")
                return None
            
            # Check if branding already exists for this property
            existing_response = self.client.table("property_branding").select("*").eq("property_id", property_id).execute()
            
            branding_record = {
                "property_id": property_id,
                "branding_data": branding_data
            }
            if website_url:
                branding_record["website_url"] = website_url
            
            if existing_response.data and len(existing_response.data) > 0:
                # Update existing branding
                response = self.client.table("property_branding").update(branding_record).eq("property_id", property_id).execute()
                if response.data and len(response.data) > 0:
                    return response.data[0].get("id")
            else:
                # Create new branding
                response = self.client.table("property_branding").insert(branding_record).execute()
                if response.data and len(response.data) > 0:
                    return response.data[0].get("id")
            
            return None
        except Exception as e:
            print(f"Error creating or updating branding: {e}")
            return None
    
    def get_branding_by_property_id(self, property_id: str) -> Optional[PropertyBranding]:
        """
        Get branding data for a property.
        
        Args:
            property_id: ID of the property
            
        Returns:
            PropertyBranding instance if found, None otherwise
        """
        try:
            response = self.client.table("property_branding").select("*").eq("property_id", property_id).execute()
            
            if response.data and len(response.data) > 0:
                return PropertyBranding.from_dict(response.data[0])
            return None
        except Exception as e:
            print(f"Error getting branding by property ID: {e}")
            return None
    
    def create_or_update_amenities(
        self,
        property_id: str,
        amenities_data: Dict[str, Any],
        website_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Create or update amenities data for a property.
        
        Args:
            property_id: ID of the property
            amenities_data: Dictionary containing amenities information
            website_url: Optional website URL for reference
            
        Returns:
            ID of the amenities record, or None if creation/update failed
        """
        try:
            # Don't save empty amenities data
            if not amenities_data or amenities_data == {}:
                print(f"⚠ Warning: Attempted to save empty amenities data - skipping")
                return None
            
            # Check if amenities already exists for this property
            existing_response = self.client.table("property_amenities").select("*").eq("property_id", property_id).execute()
            
            amenities_record = {
                "property_id": property_id,
                "amenities_data": amenities_data
            }
            if website_url:
                amenities_record["website_url"] = website_url
            
            if existing_response.data and len(existing_response.data) > 0:
                # Update existing amenities
                response = self.client.table("property_amenities").update(amenities_record).eq("property_id", property_id).execute()
                if response.data and len(response.data) > 0:
                    return response.data[0].get("id")
            else:
                # Create new amenities
                response = self.client.table("property_amenities").insert(amenities_record).execute()
                if response.data and len(response.data) > 0:
                    return response.data[0].get("id")
            
            return None
        except Exception as e:
            print(f"Error creating or updating amenities: {e}")
            return None
    
    def get_amenities_by_property_id(self, property_id: str) -> Optional[PropertyAmenities]:
        """
        Get amenities data for a property.
        
        Args:
            property_id: ID of the property
            
        Returns:
            PropertyAmenities instance if found, None otherwise
        """
        try:
            response = self.client.table("property_amenities").select("*").eq("property_id", property_id).execute()
            
            if response.data and len(response.data) > 0:
                return PropertyAmenities.from_dict(response.data[0])
            return None
        except Exception as e:
            print(f"Error getting amenities by property ID: {e}")
            return None
    
    def create_or_update_floor_plan(self, floor_plan: PropertyFloorPlan) -> Optional[str]:
        """
        Create or update a single floor plan.
        
        Args:
            floor_plan: PropertyFloorPlan instance to create or update
            
        Returns:
            ID of the floor plan record, or None if creation/update failed
        """
        try:
            data = floor_plan.to_dict()
            
            # Check if floor plan already exists (by property_id and name)
            if floor_plan.property_id and floor_plan.name:
                existing_response = self.client.table("property_floor_plans").select("*").eq("property_id", floor_plan.property_id).eq("name", floor_plan.name).execute()
                
                if existing_response.data and len(existing_response.data) > 0:
                    # Update existing floor plan
                    response = self.client.table("property_floor_plans").update(data).eq("id", existing_response.data[0]["id"]).execute()
                    if response.data and len(response.data) > 0:
                        return response.data[0].get("id")
            
            # Create new floor plan
            response = self.client.table("property_floor_plans").insert(data).execute()
            if response.data and len(response.data) > 0:
                return response.data[0].get("id")
            
            return None
        except Exception as e:
            print(f"Error creating or updating floor plan: {e}")
            return None
    
    def add_property_floor_plans(self, property_id: str, floor_plans: List[Dict[str, Any]], website_url: Optional[str] = None) -> int:
        """
        Add multiple floor plans for a property.
        
        Args:
            property_id: ID of the property
            floor_plans: List of floor plan dictionaries with name, size_sqft, bedrooms, etc.
            website_url: Optional website URL for reference
            
        Returns:
            Number of floor plans added
        """
        if not floor_plans:
            return 0
        
        try:
            floor_plan_records = []
            for fp in floor_plans:
                floor_plan_record = {
                    "property_id": property_id,
                    "name": fp.get("name", ""),
                    "size_sqft": fp.get("size_sqft"),
                    "bedrooms": fp.get("bedrooms"),
                    "bathrooms": fp.get("bathrooms"),
                    "price_string": fp.get("price_string"),
                    "min_price": fp.get("min_price"),
                    "max_price": fp.get("max_price"),
                    "available_units": fp.get("available_units"),
                    "is_available": fp.get("is_available"),
                    "website_url": website_url
                }
                floor_plan_records.append(floor_plan_record)
            
            # Use upsert to handle duplicates (based on unique constraint)
            # Supabase will automatically handle conflicts based on the unique constraint
            response = self.client.table("property_floor_plans").upsert(floor_plan_records).execute()
            return len(response.data) if response.data else 0
        except Exception as e:
            print(f"Error adding property floor plans: {e}")
            return 0
    
    def get_floor_plans_by_property_id(self, property_id: str) -> List[PropertyFloorPlan]:
        """
        Get all floor plans for a property.
        
        Args:
            property_id: ID of the property
            
        Returns:
            List of PropertyFloorPlan instances
        """
        try:
            response = self.client.table("property_floor_plans").select("*").eq("property_id", property_id).execute()
            
            if response.data:
                return [PropertyFloorPlan.from_dict(fp) for fp in response.data]
            return []
        except Exception as e:
            print(f"Error getting floor plans by property ID: {e}")
            return []
    
    def delete_floor_plans_for_property(self, property_id: str) -> bool:
        """
        Delete all floor plans for a property (useful before re-extraction).
        
        Args:
            property_id: ID of the property
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            response = self.client.table("property_floor_plans").delete().eq("property_id", property_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting floor plans for property: {e}")
            return False
    
    def create_or_update_special_offer(self, offer: PropertySpecialOffer) -> Optional[str]:
        """
        Create or update a single special offer.
        
        Args:
            offer: PropertySpecialOffer instance to create or update
            
        Returns:
            ID of the special offer record, or None if creation/update failed
        """
        try:
            data = offer.to_dict()
            
            # Check if offer already exists (by property_id, floor_plan_id, and offer_description)
            if offer.property_id and offer.offer_description:
                query = self.client.table("property_special_offers").select("*").eq("property_id", offer.property_id).eq("offer_description", offer.offer_description)
                if offer.floor_plan_id:
                    query = query.eq("floor_plan_id", offer.floor_plan_id)
                else:
                    query = query.is_("floor_plan_id", "null")
                
                existing_response = query.execute()
                
                if existing_response.data and len(existing_response.data) > 0:
                    # Update existing offer
                    response = self.client.table("property_special_offers").update(data).eq("id", existing_response.data[0]["id"]).execute()
                    if response.data and len(response.data) > 0:
                        return response.data[0].get("id")
            
            # Create new offer
            response = self.client.table("property_special_offers").insert(data).execute()
            if response.data and len(response.data) > 0:
                return response.data[0].get("id")
            
            return None
        except Exception as e:
            print(f"Error creating or updating special offer: {e}")
            return None
    
    def add_property_special_offers(self, property_id: str, offers: List[Dict[str, Any]], website_url: Optional[str] = None) -> int:
        """
        Add multiple special offers for a property.
        
        Args:
            property_id: ID of the property
            offers: List of offer dictionaries with offer_description, valid_until, descriptive_text, floor_plan_name, etc.
            website_url: Optional website URL for reference
            
        Returns:
            Number of offers added
        """
        if not offers:
            return 0
        
        try:
            # First, get all floor plans for this property to map floor_plan_name to floor_plan_id
            floor_plans = self.get_floor_plans_by_property_id(property_id)
            floor_plan_map = {fp.name: fp.id for fp in floor_plans}
            
            offer_records = []
            for offer in offers:
                floor_plan_id = None
                floor_plan_name = offer.get("floor_plan_name")
                if floor_plan_name and floor_plan_name in floor_plan_map:
                    floor_plan_id = floor_plan_map[floor_plan_name]
                
                offer_record = {
                    "property_id": property_id,
                    "offer_description": offer.get("offer_description", ""),
                    "valid_until": offer.get("valid_until"),
                    "descriptive_text": offer.get("descriptive_text"),
                    "website_url": website_url
                }
                
                if floor_plan_id:
                    offer_record["floor_plan_id"] = floor_plan_id
                
                offer_records.append(offer_record)
            
            # Use upsert to handle duplicates (based on unique constraint)
            response = self.client.table("property_special_offers").upsert(offer_records).execute()
            return len(response.data) if response.data else 0
        except Exception as e:
            print(f"Error adding property special offers: {e}")
            return 0
    
    def get_special_offers_by_property_id(self, property_id: str, include_expired: bool = False) -> List[PropertySpecialOffer]:
        """
        Get all special offers for a property.
        
        Args:
            property_id: ID of the property
            include_expired: If False, filter out expired offers (based on valid_until date)
            
        Returns:
            List of PropertySpecialOffer instances
        """
        try:
            query = self.client.table("property_special_offers").select("*").eq("property_id", property_id)
            
            # Filter out expired offers if requested
            if not include_expired:
                from datetime import date
                today = date.today().isoformat()
                query = query.or_(f"valid_until.is.null,valid_until.gte.{today}")
            
            response = query.execute()
            
            if response.data:
                return [PropertySpecialOffer.from_dict(offer) for offer in response.data]
            return []
        except Exception as e:
            print(f"Error getting special offers by property ID: {e}")
            return []
    
    def delete_special_offers_for_property(self, property_id: str) -> bool:
        """
        Delete all special offers for a property (useful before re-extraction).
        
        Args:
            property_id: ID of the property
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            response = self.client.table("property_special_offers").delete().eq("property_id", property_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting special offers for property: {e}")
            return False
    
    def create_or_update_reviews_summary(
        self,
        property_id: str,
        overall_rating: Optional[float] = None,
        review_count: Optional[int] = None,
        google_maps_place_id: Optional[str] = None,
        google_maps_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Create or update reviews summary for a property.
        
        Args:
            property_id: ID of the property
            overall_rating: Overall rating (out of 5)
            review_count: Total number of reviews
            google_maps_place_id: Google Maps place ID
            google_maps_url: Google Maps URL for reference
            
        Returns:
            ID of the reviews summary record, or None if creation/update failed
        """
        try:
            summary_record = {
                "property_id": property_id
            }
            if overall_rating is not None:
                summary_record["overall_rating"] = overall_rating
            if review_count is not None:
                summary_record["review_count"] = review_count
            if google_maps_place_id is not None:
                summary_record["google_maps_place_id"] = google_maps_place_id
            if google_maps_url is not None:
                summary_record["google_maps_url"] = google_maps_url
            
            # Check if summary already exists
            existing_response = self.client.table("property_reviews_summary").select("*").eq("property_id", property_id).execute()
            
            if existing_response.data and len(existing_response.data) > 0:
                # Update existing summary
                response = self.client.table("property_reviews_summary").update(summary_record).eq("property_id", property_id).execute()
                if response.data and len(response.data) > 0:
                    return response.data[0].get("id")
            else:
                # Create new summary
                response = self.client.table("property_reviews_summary").insert(summary_record).execute()
                if response.data and len(response.data) > 0:
                    return response.data[0].get("id")
            
            return None
        except Exception as e:
            print(f"Error creating or updating reviews summary: {e}")
            return None
    
    def get_reviews_summary_by_property_id(self, property_id: str) -> Optional[PropertyReviewsSummary]:
        """
        Get reviews summary for a property.
        
        Args:
            property_id: ID of the property
            
        Returns:
            PropertyReviewsSummary instance if found, None otherwise
        """
        try:
            response = self.client.table("property_reviews_summary").select("*").eq("property_id", property_id).execute()
            
            if response.data and len(response.data) > 0:
                return PropertyReviewsSummary.from_dict(response.data[0])
            return None
        except Exception as e:
            print(f"Error getting reviews summary by property ID: {e}")
            return None
    
    def get_existing_review_ids(self, property_id: str) -> Set[str]:
        """
        Get set of existing review IDs for a property (for duplicate checking).
        
        Args:
            property_id: ID of the property
            
        Returns:
            Set of review IDs that already exist
        """
        try:
            response = self.client.table("property_reviews").select("review_id").eq("property_id", property_id).execute()
            
            if response.data:
                return {review.get("review_id") for review in response.data if review.get("review_id")}
            return set()
        except Exception as e:
            print(f"Error getting existing review IDs: {e}")
            return set()
    
    def create_or_update_review(self, review: PropertyReview) -> Optional[str]:
        """
        Create or update a single review.
        
        Args:
            review: PropertyReview instance to create or update
            
        Returns:
            ID of the review record, or None if creation/update failed
        """
        try:
            data = review.to_dict()
            
            # Check if review already exists (by property_id and review_id)
            if review.property_id and review.review_id:
                existing_response = self.client.table("property_reviews").select("*").eq("property_id", review.property_id).eq("review_id", review.review_id).execute()
                
                if existing_response.data and len(existing_response.data) > 0:
                    # Update existing review
                    response = self.client.table("property_reviews").update(data).eq("id", existing_response.data[0]["id"]).execute()
                    if response.data and len(response.data) > 0:
                        return response.data[0].get("id")
            
            # Create new review
            response = self.client.table("property_reviews").insert(data).execute()
            if response.data and len(response.data) > 0:
                return response.data[0].get("id")
            
            return None
        except Exception as e:
            print(f"Error creating or updating review: {e}")
            return None
    
    def add_property_reviews(self, property_id: str, reviews: List[Dict[str, Any]]) -> int:
        """
        Add multiple reviews for a property (only new ones, skipping duplicates).
        
        Args:
            property_id: ID of the property
            reviews: List of review dictionaries with review_id, reviewer_name, review_text, etc.
            
        Returns:
            Number of new reviews added (excluding duplicates)
        """
        if not reviews:
            return 0
        
        try:
            # Get existing review IDs to avoid duplicates
            existing_review_ids = self.get_existing_review_ids(property_id)
            
            # Filter out reviews that already exist
            new_reviews = []
            for review in reviews:
                review_id = review.get("review_id")
                if review_id and review_id not in existing_review_ids:
                    review_record = {
                        "property_id": property_id,
                        "review_id": review_id,
                        "reviewer_name": review.get("reviewer_name"),
                        "reviewer_id": review.get("reviewer_id"),
                        "reviewer_url": review.get("reviewer_url"),
                        "reviewer_photo_url": review.get("reviewer_photo_url"),
                        "review_text": review.get("review_text"),
                        "stars": review.get("stars"),
                        "published_at": review.get("published_at"),
                        "review_url": review.get("review_url"),
                        "response_from_owner_text": review.get("response_from_owner_text"),
                        "response_from_owner_date": review.get("response_from_owner_date"),
                        "review_image_urls": review.get("review_image_urls", []),
                        "is_local_guide": review.get("is_local_guide", False)
                    }
                    new_reviews.append(review_record)
            
            if not new_reviews:
                return 0
            
            # Insert new reviews (using upsert to handle any race conditions)
            response = self.client.table("property_reviews").upsert(new_reviews).execute()
            return len(response.data) if response.data else 0
        except Exception as e:
            print(f"Error adding property reviews: {e}")
            return 0
    
    def get_reviews_by_property_id(self, property_id: str, limit: Optional[int] = None, order_by: str = "published_at") -> List[PropertyReview]:
        """
        Get all reviews for a property.
        
        Args:
            property_id: ID of the property
            limit: Optional limit on number of reviews to return
            order_by: Field to order by (default: "published_at")
            
        Returns:
            List of PropertyReview instances
        """
        try:
            query = self.client.table("property_reviews").select("*").eq("property_id", property_id)
            
            # Order by specified field (default: published_at DESC for newest first)
            if order_by == "published_at":
                query = query.order("published_at", desc=True)
            elif order_by:
                query = query.order(order_by, desc=True)
            
            # Apply limit if specified
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            
            if response.data:
                return [PropertyReview.from_dict(review) for review in response.data]
            return []
        except Exception as e:
            print(f"Error getting reviews by property ID: {e}")
            return []
    
    def get_positive_reviews(self, property_id: str, limit: int = 5) -> List[PropertyReview]:
        """
        Get positive reviews (5 stars) for a property, ordered by most recent first.
        
        Args:
            property_id: ID of the property
            limit: Maximum number of reviews to return (default: 5)
            
        Returns:
            List of PropertyReview instances with 5 stars
        """
        try:
            query = self.client.table("property_reviews").select("*").eq("property_id", property_id).eq("stars", 5)
            query = query.order("published_at", desc=True).limit(limit)
            
            response = query.execute()
            
            if response.data:
                return [PropertyReview.from_dict(review) for review in response.data]
            return []
        except Exception as e:
            print(f"Error getting positive reviews: {e}")
            return []
    
    def get_negative_reviews(self, property_id: str, limit: int = 5) -> List[PropertyReview]:
        """
        Get negative reviews (1-3 stars) for a property, ordered by most recent first.
        
        Args:
            property_id: ID of the property
            limit: Maximum number of reviews to return (default: 5)
            
        Returns:
            List of PropertyReview instances with 1, 2, or 3 stars
        """
        try:
            query = self.client.table("property_reviews").select("*").eq("property_id", property_id)
            query = query.in_("stars", [1, 2, 3])
            query = query.order("published_at", desc=True).limit(limit)
            
            response = query.execute()
            
            if response.data:
                return [PropertyReview.from_dict(review) for review in response.data]
            return []
        except Exception as e:
            print(f"Error getting negative reviews: {e}")
            return []
    
    def update_reviews_sentiment_summary(self, property_id: str, sentiment_summary: str) -> bool:
        """
        Update the sentiment summary for a property's reviews.
        
        Args:
            property_id: ID of the property
            sentiment_summary: The generated sentiment summary text
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            from datetime import datetime
            update_data = {
                "sentiment_summary": sentiment_summary,
                "sentiment_summary_generated_at": datetime.now().isoformat()
            }
            response = self.client.table("property_reviews_summary").update(update_data).eq("property_id", property_id).execute()
            return response.data is not None
        except Exception as e:
            print(f"Error updating reviews sentiment summary: {e}")
            return False
    
    def add_competitor(self, competitor: Competitor) -> Optional[str]:
        """
        Add a competitor for a property.
        
        Args:
            competitor: Competitor instance to add
            
        Returns:
            ID of the created competitor, or None if creation failed
        """
        try:
            data = competitor.to_dict()
            response = self.client.table("property_competitors").insert(data).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0].get("id")
            return None
        except Exception as e:
            print(f"Error adding competitor: {e}")
            return None
    
    def add_competitors(self, property_id: str, competitors: List[Competitor]) -> int:
        """
        Add multiple competitors for a property.
        Skips duplicates based on place_id.
        
        Args:
            property_id: ID of the property
            competitors: List of Competitor instances to add
            
        Returns:
            Number of competitors added (excluding duplicates)
        """
        if not competitors:
            return 0
        
        try:
            # Get existing place_ids for this property to avoid duplicates
            existing_response = self.client.table("property_competitors").select("place_id").eq("property_id", property_id).execute()
            existing_place_ids = {c.get("place_id") for c in (existing_response.data or []) if c.get("place_id")}
            
            # Filter out duplicates and prepare data
            competitor_records = []
            for competitor in competitors:
                # Skip if place_id already exists
                if competitor.place_id and competitor.place_id in existing_place_ids:
                    continue
                
                competitor_dict = competitor.to_dict()
                competitor_records.append(competitor_dict)
                
                # Add to existing set to avoid duplicates within this batch
                if competitor.place_id:
                    existing_place_ids.add(competitor.place_id)
            
            if not competitor_records:
                return 0
            
            response = self.client.table("property_competitors").insert(competitor_records).execute()
            return len(response.data) if response.data else 0
        except Exception as e:
            print(f"Error adding competitors: {e}")
            return 0
    
    def get_competitors_by_property_id(self, property_id: str) -> List[Competitor]:
        """
        Get all competitors for a property.
        
        Args:
            property_id: ID of the property
            
        Returns:
            List of Competitor instances
        """
        try:
            response = self.client.table("property_competitors").select("*").eq("property_id", property_id).order("distance_miles", desc=False).execute()
            
            if response.data:
                return [Competitor.from_dict(competitor) for competitor in response.data]
            return []
        except Exception as e:
            print(f"Error getting competitors by property ID: {e}")
            return []
    
    def create_social_post(self, social_post: PropertySocialPost) -> Optional[str]:
        """
        Create a new social media post for a property.
        
        Args:
            social_post: PropertySocialPost instance to create
            
        Returns:
            ID of the created post, or None if creation failed
        """
        try:
            data = social_post.to_dict()
            response = self.client.table("property_social_posts").insert(data).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0].get("id")
            return None
        except Exception as e:
            print(f"Error creating social post: {e}")
            return None
    
    def get_property_social_posts(self, property_id: str) -> List[PropertySocialPost]:
        """
        Get all social media posts for a property.
        
        Args:
            property_id: ID of the property
            
        Returns:
            List of PropertySocialPost instances
        """
        try:
            response = self.client.table("property_social_posts").select("*").eq("property_id", property_id).order("created_at", desc=False).execute()
            
            if response.data:
                return [PropertySocialPost.from_dict(post) for post in response.data]
            return []
        except Exception as e:
            print(f"Error getting social posts by property ID: {e}")
            return []

