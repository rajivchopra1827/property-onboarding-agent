-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Properties table
CREATE TABLE properties (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  property_name TEXT,
  street_address TEXT,
  city TEXT,
  state TEXT,
  zip_code TEXT,
  phone TEXT,
  email TEXT,
  office_hours JSONB,
  website_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Property images table
CREATE TABLE property_images (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
  image_url TEXT NOT NULL,
  image_type TEXT, -- 'exterior', 'interior', 'amenity', etc.
  page_url TEXT, -- URL of the page where image was found
  alt_text TEXT,
  width INTEGER,
  height INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cache entries table (replaces file-based cache)
CREATE TABLE cache_entries (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  domain TEXT NOT NULL,
  content_type TEXT NOT NULL, -- 'markdown', 'images', etc.
  cached_data JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(domain, content_type)
);

-- Extraction sessions table (track extraction runs)
CREATE TABLE extraction_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  property_id UUID REFERENCES properties(id) ON DELETE SET NULL,
  website_url TEXT NOT NULL,
  status TEXT DEFAULT 'completed', -- 'completed', 'failed', 'in_progress'
  extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  notes TEXT
);

-- Create indexes for better query performance
CREATE INDEX idx_properties_website_url ON properties(website_url);
CREATE INDEX idx_property_images_property_id ON property_images(property_id);
CREATE INDEX idx_cache_entries_domain ON cache_entries(domain);
CREATE INDEX idx_extraction_sessions_property_id ON extraction_sessions(property_id);
CREATE INDEX idx_extraction_sessions_extracted_at ON extraction_sessions(extracted_at DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_properties_updated_at BEFORE UPDATE ON properties
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cache_entries_updated_at BEFORE UPDATE ON cache_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

