-- =====================================================
-- CREATE FUTURE DEVELOPMENT SCRAPING TABLE
-- Run this in Supabase SQL Editor
-- =====================================================

-- Create the table
CREATE TABLE IF NOT EXISTS future_development_scrap (
    id BIGSERIAL PRIMARY KEY,
    location_id INTEGER,
    location_name VARCHAR(255),
    source VARCHAR(255),
    url TEXT UNIQUE,
    content TEXT,
    published_at TIMESTAMP,
    year_mentioned INTEGER,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_url_future_dev UNIQUE(url)
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_future_dev_location_id ON future_development_scrap(location_id);
CREATE INDEX IF NOT EXISTS idx_future_dev_year ON future_development_scrap(year_mentioned);
CREATE INDEX IF NOT EXISTS idx_future_dev_scraped_at ON future_development_scrap(scraped_at);

-- Add foreign key constraint to locations table
ALTER TABLE future_development_scrap 
ADD CONSTRAINT fk_future_dev_location 
FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE;

-- Grant permissions (if needed for anon access)
-- GRANT SELECT ON future_development_scrap TO anon;

-- Verify table creation
SELECT 'future_development_scrap table created successfully!' as status;
SELECT COUNT(*) as total_records FROM future_development_scrap;
