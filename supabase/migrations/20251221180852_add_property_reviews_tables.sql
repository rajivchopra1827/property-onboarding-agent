-- Property reviews summary table
CREATE TABLE property_reviews_summary (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
  overall_rating NUMERIC(3,2), -- Rating out of 5 (e.g., 4.8)
  review_count INTEGER, -- Total number of reviews
  google_maps_place_id TEXT, -- Google Maps place ID
  google_maps_url TEXT, -- Google Maps URL for reference
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(property_id)
);

-- Property reviews table
CREATE TABLE property_reviews (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
  review_id TEXT NOT NULL, -- Unique Google review ID for deduplication
  reviewer_name TEXT,
  reviewer_id TEXT,
  reviewer_url TEXT,
  reviewer_photo_url TEXT,
  review_text TEXT,
  stars INTEGER, -- Rating 1-5
  published_at TIMESTAMP WITH TIME ZONE, -- Review publication date
  review_url TEXT,
  response_from_owner_text TEXT, -- Property owner's response if any
  response_from_owner_date TIMESTAMP WITH TIME ZONE, -- Response date
  review_image_urls JSONB, -- Array of image URLs attached to review
  is_local_guide BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(property_id, review_id) -- Prevent duplicate reviews
);

-- Create indexes for better query performance
CREATE INDEX idx_property_reviews_summary_property_id ON property_reviews_summary(property_id);
CREATE INDEX idx_property_reviews_property_id ON property_reviews(property_id);
CREATE INDEX idx_property_reviews_review_id ON property_reviews(review_id);
CREATE INDEX idx_property_reviews_published_at ON property_reviews(published_at DESC); -- For sorting by date

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_property_reviews_summary_updated_at BEFORE UPDATE ON property_reviews_summary
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_property_reviews_updated_at BEFORE UPDATE ON property_reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


