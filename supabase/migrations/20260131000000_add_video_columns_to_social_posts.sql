-- Add video columns to property_social_posts table
-- Supports video reel generation feature

-- Add video_url column for storing generated video URLs
ALTER TABLE property_social_posts
ADD COLUMN IF NOT EXISTS video_url TEXT;

-- Add is_video flag to distinguish video posts from image posts
ALTER TABLE property_social_posts
ADD COLUMN IF NOT EXISTS is_video BOOLEAN DEFAULT FALSE;

-- Add video generation metadata (duration, model used, etc.)
ALTER TABLE property_social_posts
ADD COLUMN IF NOT EXISTS video_metadata JSONB;

-- Create index for filtering video posts
CREATE INDEX IF NOT EXISTS idx_property_social_posts_is_video
ON property_social_posts(is_video);

-- Add comment for documentation
COMMENT ON COLUMN property_social_posts.video_url IS 'URL to the generated video reel (null for static image posts)';
COMMENT ON COLUMN property_social_posts.is_video IS 'True if this post has a generated video reel';
COMMENT ON COLUMN property_social_posts.video_metadata IS 'Video generation metadata: duration, model, generation_time, cost, etc.';
