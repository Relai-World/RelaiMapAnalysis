
-- Create volume_trends table
CREATE TABLE IF NOT EXISTS volume_trends (
    id SERIAL PRIMARY KEY,
    location_name VARCHAR(255) NOT NULL,
    cluster VARCHAR(100),
    year_2018 INTEGER,
    year_2019 INTEGER,
    year_2020 INTEGER,
    year_2021 INTEGER,
    year_2022 INTEGER,
    year_2023 INTEGER,
    year_2024 INTEGER,
    year_2025 INTEGER,
    year_2026 INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(location_name)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_volume_trends_location ON volume_trends(location_name);

-- Create RPC function to get volume trends by location
CREATE OR REPLACE FUNCTION get_volume_trends_func(area_name TEXT)
RETURNS TABLE(
    location_name TEXT,
    cluster TEXT,
    year_2018 INTEGER,
    year_2019 INTEGER,
    year_2020 INTEGER,
    year_2021 INTEGER,
    year_2022 INTEGER,
    year_2023 INTEGER,
    year_2024 INTEGER,
    year_2025 INTEGER,
    year_2026 INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        vt.location_name::TEXT,
        vt.cluster::TEXT,
        vt.year_2018,
        vt.year_2019,
        vt.year_2020,
        vt.year_2021,
        vt.year_2022,
        vt.year_2023,
        vt.year_2024,
        vt.year_2025,
        vt.year_2026
    FROM volume_trends vt
    WHERE LOWER(vt.location_name) = LOWER(area_name);
END;
$$ LANGUAGE plpgsql;
