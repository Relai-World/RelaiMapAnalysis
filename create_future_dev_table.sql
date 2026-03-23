-- Create future_dev table for storing future development articles
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS future_dev (
    id BIGSERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL,
    location_name VARCHAR(255) NOT NULL,
    source VARCHAR(255),
    url TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    published_at TIMESTAMP,
    year_mentioned INTEGER,
    scraped_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_future_dev_location_id ON future_dev(location_id);
CREATE INDEX IF NOT EXISTS idx_future_dev_location_name ON future_dev(location_name);
CREATE INDEX IF NOT EXISTS idx_future_dev_year ON future_dev(year_mentioned);
CREATE INDEX IF NOT EXISTS idx_future_dev_url ON future_dev(url);

-- Enable Row Level Security (optional, adjust policies as needed)
ALTER TABLE future_dev ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (adjust based on your security needs)
CREATE POLICY "Enable all access for future_dev" ON future_dev
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Add comment
COMMENT ON TABLE future_dev IS 'Stores scraped articles about future developments in Hyderabad locations (2022-2030)';
