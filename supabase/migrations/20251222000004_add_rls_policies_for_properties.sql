-- Enable RLS on properties table (if not already enabled)
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "Allow all operations on properties" ON properties;
DROP POLICY IF EXISTS "Allow select on properties" ON properties;
DROP POLICY IF EXISTS "Allow update on properties" ON properties;
DROP POLICY IF EXISTS "Allow insert on properties" ON properties;

-- Create permissive policies for development
-- For production, you'd want more restrictive policies based on user authentication

-- Allow anyone to read properties
CREATE POLICY "Allow select on properties"
ON properties
FOR SELECT
USING (true);

-- Allow anyone to update properties (for local dev - restrict in production)
CREATE POLICY "Allow update on properties"
ON properties
FOR UPDATE
USING (true)
WITH CHECK (true);

-- Allow anyone to insert properties (for local dev - restrict in production)
CREATE POLICY "Allow insert on properties"
ON properties
FOR INSERT
WITH CHECK (true);

