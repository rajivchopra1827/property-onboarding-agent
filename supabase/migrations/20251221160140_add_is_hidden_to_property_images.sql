-- Add is_hidden column to property_images table (if it doesn't exist)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'property_images' AND column_name = 'is_hidden'
    ) THEN
        ALTER TABLE property_images 
        ADD COLUMN is_hidden BOOLEAN DEFAULT FALSE NOT NULL;
    END IF;
END $$;

-- Create index for efficient filtering (if it doesn't exist)
CREATE INDEX IF NOT EXISTS idx_property_images_is_hidden ON property_images(is_hidden);

