-- Add unique constraint on (property_id, image_url) to prevent duplicate images
-- This ensures that each image URL can only appear once per property

-- First, delete any existing duplicates (keeping the oldest one)
-- This is safe to run multiple times
WITH duplicates_to_keep AS (
    SELECT DISTINCT ON (property_id, image_url)
        id
    FROM property_images
    ORDER BY property_id, image_url, created_at ASC, id ASC
)
DELETE FROM property_images
WHERE id NOT IN (SELECT id FROM duplicates_to_keep)
AND (property_id, image_url) IN (
    SELECT property_id, image_url
    FROM property_images
    GROUP BY property_id, image_url
    HAVING COUNT(*) > 1
);

-- Now add the unique constraint
-- This will prevent future duplicates at the database level
DO $$ 
BEGIN
    -- Check if constraint already exists before adding it
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'property_images_property_id_image_url_unique'
    ) THEN
        ALTER TABLE property_images 
        ADD CONSTRAINT property_images_property_id_image_url_unique 
        UNIQUE (property_id, image_url);
    END IF;
END $$;

-- Create an index to improve query performance for duplicate checks
CREATE INDEX IF NOT EXISTS idx_property_images_property_id_image_url 
ON property_images(property_id, image_url);


