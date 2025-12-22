-- Property special offers table
CREATE TABLE property_special_offers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
  floor_plan_id UUID REFERENCES property_floor_plans(id) ON DELETE CASCADE, -- Optional: for floor plan-specific offers
  offer_description TEXT NOT NULL, -- What the offer is (e.g., "First month free", "$500 off moving costs")
  valid_until DATE, -- When the offer expires (null if no expiration date)
  descriptive_text TEXT, -- Additional details about the offer
  website_url TEXT, -- For reference
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(property_id, floor_plan_id, offer_description) -- Prevent duplicate offers
);

-- Create indexes for better query performance
CREATE INDEX idx_property_special_offers_property_id ON property_special_offers(property_id);
CREATE INDEX idx_property_special_offers_floor_plan_id ON property_special_offers(floor_plan_id);
CREATE INDEX idx_property_special_offers_valid_until ON property_special_offers(valid_until); -- For filtering expired offers

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_property_special_offers_updated_at BEFORE UPDATE ON property_special_offers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


