-- Amenity normalization mappings table
-- Stores mappings between raw amenity names and normalized canonical names
CREATE TABLE amenity_normalizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  raw_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  category TEXT NOT NULL, -- 'building' or 'apartment'
  confidence_score DECIMAL(3,2), -- 0.00 to 1.00
  source TEXT DEFAULT 'ai', -- 'ai', 'manual', 'taxonomy'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(raw_name, category)
);

-- Create indexes for better query performance
CREATE INDEX idx_amenity_normalizations_raw_name ON amenity_normalizations(raw_name);
CREATE INDEX idx_amenity_normalizations_normalized_name ON amenity_normalizations(normalized_name);
CREATE INDEX idx_amenity_normalizations_category ON amenity_normalizations(category);

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_amenity_normalizations_updated_at BEFORE UPDATE ON amenity_normalizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
