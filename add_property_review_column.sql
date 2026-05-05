-- Add Property_Review column to unified_data_DataType_Raghu table if it doesn't exist

-- Check if column exists and add if not
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'unified_data_DataType_Raghu' 
        AND column_name = 'Property_Review'
    ) THEN
        ALTER TABLE "unified_data_DataType_Raghu" 
        ADD COLUMN "Property_Review" TEXT;
        
        RAISE NOTICE 'Property_Review column added successfully';
    ELSE
        RAISE NOTICE 'Property_Review column already exists';
    END IF;
END $$;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_property_review 
ON "unified_data_DataType_Raghu" ("Property_Review") 
WHERE "Property_Review" IS NOT NULL;
