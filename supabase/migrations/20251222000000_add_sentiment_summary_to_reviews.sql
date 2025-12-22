-- Add sentiment_summary and sentiment_summary_generated_at columns to property_reviews_summary table
ALTER TABLE property_reviews_summary
ADD COLUMN IF NOT EXISTS sentiment_summary TEXT,
ADD COLUMN IF NOT EXISTS sentiment_summary_generated_at TIMESTAMP WITH TIME ZONE;

-- Create index for sentiment_summary_generated_at for efficient queries
CREATE INDEX IF NOT EXISTS idx_property_reviews_summary_sentiment_generated_at 
ON property_reviews_summary(sentiment_summary_generated_at DESC);


