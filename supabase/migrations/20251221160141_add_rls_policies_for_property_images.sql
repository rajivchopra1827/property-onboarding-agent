-- Enable RLS on property_images table (if not already enabled)
ALTER TABLE property_images ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "Allow all operations on property_images" ON property_images;
DROP POLICY IF EXISTS "Allow select on property_images" ON property_images;
DROP POLICY IF EXISTS "Allow update on property_images" ON property_images;
DROP POLICY IF EXISTS "Allow insert on property_images" ON property_images;

-- Create permissive policies for local development
-- For production, you'd want more restrictive policies based on user authentication

-- Allow anyone to read property_images
CREATE POLICY "Allow select on property_images"
ON property_images
FOR SELECT
USING (true);

-- Allow anyone to update property_images (for local dev - restrict in production)
CREATE POLICY "Allow update on property_images"
ON property_images
FOR UPDATE
USING (true)
WITH CHECK (true);

-- Allow anyone to insert property_images (for local dev - restrict in production)
CREATE POLICY "Allow insert on property_images"
ON property_images
FOR INSERT
WITH CHECK (true);


