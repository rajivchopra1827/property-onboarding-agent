-- Competitor watchlist table
CREATE TABLE competitor_watchlist (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  competitor_id UUID NOT NULL REFERENCES property_competitors(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(property_id, competitor_id)
);

-- Create indexes for efficient queries
CREATE INDEX idx_competitor_watchlist_property_id ON competitor_watchlist(property_id);
CREATE INDEX idx_competitor_watchlist_competitor_id ON competitor_watchlist(competitor_id);


