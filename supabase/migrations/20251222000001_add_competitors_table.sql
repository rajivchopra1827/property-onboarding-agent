-- Property competitors table
CREATE TABLE property_competitors (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  competitor_name TEXT NOT NULL,
  address TEXT,
  street_address TEXT,
  city TEXT,
  state TEXT,
  zip_code TEXT,
  phone TEXT,
  website TEXT,
  google_maps_url TEXT,
  place_id TEXT,
  rating NUMERIC,
  review_count INTEGER,
  latitude NUMERIC,
  longitude NUMERIC,
  distance_miles NUMERIC,
  scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient queries
CREATE INDEX idx_property_competitors_property_id ON property_competitors(property_id);
CREATE INDEX idx_property_competitors_place_id ON property_competitors(place_id);
CREATE INDEX idx_property_competitors_created_at ON property_competitors(created_at DESC);

-- Create trigger to automatically update updated_at timestamp
CREATE TRIGGER update_property_competitors_updated_at BEFORE UPDATE ON property_competitors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

