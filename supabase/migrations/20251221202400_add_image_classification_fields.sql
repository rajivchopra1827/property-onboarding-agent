-- Add image classification fields to property_images table
-- This migration adds support for AI-powered image classification with tags, confidence scores, and quality scores

-- Add image_tags column (JSONB array of tag strings)
ALTER TABLE property_images 
ADD COLUMN IF NOT EXISTS image_tags JSONB DEFAULT '[]'::jsonb;

-- Add classification_confidence column (0.0-1.0)
ALTER TABLE property_images 
ADD COLUMN IF NOT EXISTS classification_confidence NUMERIC(3,2) CHECK (classification_confidence >= 0 AND classification_confidence <= 1);

-- Add quality_score column (0.0-1.0)
ALTER TABLE property_images 
ADD COLUMN IF NOT EXISTS quality_score NUMERIC(3,2) CHECK (quality_score >= 0 AND quality_score <= 1);

-- Add classification_method column
ALTER TABLE property_images 
ADD COLUMN IF NOT EXISTS classification_method TEXT;

-- Add classified_at timestamp
ALTER TABLE property_images 
ADD COLUMN IF NOT EXISTS classified_at TIMESTAMP WITH TIME ZONE;

-- Create GIN index on image_tags for efficient filtering and querying
CREATE INDEX IF NOT EXISTS idx_property_images_tags ON property_images USING GIN (image_tags);

-- Create index on quality_score for sorting
CREATE INDEX IF NOT EXISTS idx_property_images_quality_score ON property_images(quality_score DESC NULLS LAST);

-- Create index on classification_confidence for filtering
CREATE INDEX IF NOT EXISTS idx_property_images_classification_confidence ON property_images(classification_confidence DESC NULLS LAST);

-- Migrate existing image_type values to image_tags if they exist
-- This maintains backward compatibility
UPDATE property_images
SET image_tags = jsonb_build_array(image_type)
WHERE image_type IS NOT NULL 
  AND (image_tags IS NULL OR image_tags = '[]'::jsonb);


