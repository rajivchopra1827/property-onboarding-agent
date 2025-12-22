-- Property floor plans table
CREATE TABLE property_floor_plans (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  size_sqft INTEGER,
  bedrooms INTEGER,
  bathrooms DECIMAL(3,1), -- Supports half baths (e.g., 1.5, 2.5)
  price_string TEXT, -- Original price string from website (e.g., "$1,200-$1,500", "Starting at $1,200")
  min_price DECIMAL(10,2), -- Parsed minimum price in dollars
  max_price DECIMAL(10,2), -- Parsed maximum price in dollars
  available_units INTEGER, -- Number of available units (null if not specified)
  is_available BOOLEAN, -- Availability status (true/false/null)
  website_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(property_id, name) -- Prevent duplicate floor plans for the same property
);

-- Create index for better query performance
CREATE INDEX idx_property_floor_plans_property_id ON property_floor_plans(property_id);
CREATE INDEX idx_property_floor_plans_bedrooms ON property_floor_plans(bedrooms);
CREATE INDEX idx_property_floor_plans_min_price ON property_floor_plans(min_price);

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_property_floor_plans_updated_at BEFORE UPDATE ON property_floor_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


