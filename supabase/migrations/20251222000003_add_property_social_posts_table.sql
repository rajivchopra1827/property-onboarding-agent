-- Property social media posts table
CREATE TABLE property_social_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
  platform TEXT NOT NULL DEFAULT 'instagram',
  post_type TEXT NOT NULL DEFAULT 'single_image',
  theme TEXT NOT NULL,
  image_url TEXT NOT NULL,
  caption TEXT NOT NULL,
  hashtags TEXT[] DEFAULT ARRAY[]::TEXT[],
  cta TEXT,
  ready_to_post_text TEXT NOT NULL,
  mockup_image_url TEXT,
  structured_data JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX idx_property_social_posts_property_id ON property_social_posts(property_id);
CREATE INDEX idx_property_social_posts_theme ON property_social_posts(theme);
CREATE INDEX idx_property_social_posts_platform ON property_social_posts(platform);

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_property_social_posts_updated_at BEFORE UPDATE ON property_social_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


