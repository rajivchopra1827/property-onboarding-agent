/**
 * TypeScript type definitions for Property and PropertyImage
 * Matching the database models from backend/database/models.py
 */

export interface Property {
  id: string;
  property_name: string | null;
  street_address: string | null;
  city: string | null;
  state: string | null;
  zip_code: string | null;
  phone: string | null;
  email: string | null;
  office_hours: Record<string, any> | null;
  website_url: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface PropertyImage {
  id: string;
  property_id: string | null;
  image_url: string;
  image_type: string | null;
  page_url: string | null;
  alt_text: string | null;
  width: number | null;
  height: number | null;
  created_at: string | null;
  is_hidden: boolean;
  image_tags?: string[];
  classification_confidence?: number;
  quality_score?: number;
  classification_method?: string;
  classified_at?: string | null;
}

export interface BrandingColors {
  primary?: string;
  secondary?: string;
  accent?: string;
  background?: string;
  textPrimary?: string;
  textSecondary?: string;
  [key: string]: string | undefined;
}

export interface BrandingFont {
  family?: string;
  [key: string]: any;
}

export interface ToneWritingStyle {
  formality_level?: string;
  professional_level?: string;
  technical_level?: string;
}

export interface ToneEmotionalTone {
  warmth?: string;
  energy_level?: string;
  inviting_level?: string;
}

export interface BrandingTone {
  writing_style?: ToneWritingStyle;
  emotional_tone?: ToneEmotionalTone;
  voice_characteristics?: string[];
  tone_tags?: string[];
  description?: string;
}

export interface BrandingData {
  colorScheme?: string;
  logo?: string;
  colors?: BrandingColors;
  fonts?: BrandingFont[];
  typography?: Record<string, any>;
  spacing?: Record<string, any>;
  components?: Record<string, any>;
  tone?: BrandingTone;
  [key: string]: any;
}

export interface PropertyBranding {
  id: string;
  property_id: string | null;
  branding_data: BrandingData;
  website_url: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface Amenity {
  name: string;
  description?: string;
  category?: string;
}

export interface AmenitiesData {
  building_amenities: Amenity[];
  apartment_amenities: Amenity[];
}

export interface PropertyAmenities {
  id: string;
  property_id: string | null;
  amenities_data: {
    building_amenities?: string[];
    apartment_amenities?: string[];
  };
  website_url: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface PropertyFloorPlan {
  id: string;
  property_id: string | null;
  name: string;
  size_sqft: number | null;
  bedrooms: number | null;
  bathrooms: number | null;
  price_string: string | null;
  min_price: number | null;
  max_price: number | null;
  available_units: number | null;
  is_available: boolean | null;
  website_url: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface PropertySpecialOffer {
  id: string;
  property_id: string | null;
  floor_plan_id: string | null;
  offer_description: string;
  valid_until: string | null;
  descriptive_text: string | null;
  website_url: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface PropertyReview {
  id: string;
  property_id: string | null;
  review_id: string;
  reviewer_name: string | null;
  reviewer_id: string | null;
  reviewer_url: string | null;
  reviewer_photo_url: string | null;
  review_text: string | null;
  stars: number | null;
  published_at: string | null;
  review_url: string | null;
  response_from_owner_text: string | null;
  response_from_owner_date: string | null;
  review_image_urls: string[] | null;
  is_local_guide: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface PropertyReviewsSummary {
  id: string;
  property_id: string | null;
  overall_rating: number | null;
  review_count: number | null;
  google_maps_place_id: string | null;
  google_maps_url: string | null;
  sentiment_summary: string | null;
  sentiment_summary_generated_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface Competitor {
  id: string;
  property_id: string | null;
  competitor_name: string;
  address: string | null;
  street_address: string | null;
  city: string | null;
  state: string | null;
  zip_code: string | null;
  phone: string | null;
  website: string | null;
  google_maps_url: string | null;
  place_id: string | null;
  rating: number | null;
  review_count: number | null;
  latitude: number | null;
  longitude: number | null;
  distance_miles: number | null;
  scraped_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface CompetitorWatchlist {
  id: string;
  property_id: string;
  competitor_id: string;
  created_at: string;
}

export interface PropertySocialPost {
  id: string;
  property_id: string;
  platform: string;
  post_type: string;
  theme: string;
  image_url: string;
  caption: string;
  hashtags: string[];
  cta: string | null;
  ready_to_post_text: string;
  mockup_image_url: string | null;
  structured_data: Record<string, any>;
  is_video: boolean;
  video_url: string | null;
  video_generation_status: 'pending' | 'processing' | 'completed' | 'failed' | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface OnboardingSession {
  id: string;
  property_id: string | null;
  url: string;
  status: string;
  current_step: string | null;
  completed_steps: string[];
  errors: Array<{ extraction_type?: string; error?: string; message?: string }>;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// COMPARISON FEATURE TYPES
// ============================================================================

/**
 * Property with all related data loaded for comparison
 */
export interface PropertyWithAllData {
  property: Property;
  floorPlans: PropertyFloorPlan[];
  amenities: PropertyAmenities | null;
  reviewsSummary: PropertyReviewsSummary | null;
  specialOffers: PropertySpecialOffer[];
}

/**
 * Floor plan with calculated metrics for comparison
 */
export interface FloorPlanWithMetrics extends PropertyFloorPlan {
  pricePerSqft: number | null;
  effectiveRent: number | null;
  isBestPrice: boolean;
  isBestValue: boolean;
}

/**
 * Quick metrics for comparison grid
 */
export interface QuickMetrics {
  propertyId: string;
  propertyName: string;
  overallRating: number | null;
  reviewCount: number | null;
  reviewConfidence: number | null;
  studioPrice: number | null;
  oneBrPrice: number | null;
  twoBrPrice: number | null;
  threeBrPrice: number | null;
  startingPrice: number | null;
  amenityCount: number;
}

/**
 * Normalized amenity mapping
 */
export interface NormalizedAmenity {
  rawName: string;
  normalizedName: string;
  confidence: number | null;
}

/**
 * Amenity for comparison matrix (uses normalized names)
 */
export interface AmenityComparison {
  name: string; // Normalized name (ONLY this is shown to users)
  rawNames: string[]; // All raw names that map to this (stored but hidden from UI)
  category: 'building' | 'apartment';
  availability: Map<string, boolean | null>; // Based on normalized grouping
}

/**
 * Comparison highlight types
 */
export type HighlightType = 'best' | 'worst' | 'unique' | 'missing' | 'neutral';

/**
 * Cell highlight information
 */
export interface CellHighlight {
  type: HighlightType;
  reason?: string;
}
