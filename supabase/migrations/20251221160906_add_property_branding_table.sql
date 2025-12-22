-- Property branding table
CREATE TABLE property_branding (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
  branding_data JSONB NOT NULL,
  website_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(property_id)
);

-- Create index for better query performance
CREATE INDEX idx_property_branding_property_id ON property_branding(property_id);

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_property_branding_updated_at BEFORE UPDATE ON property_branding
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


