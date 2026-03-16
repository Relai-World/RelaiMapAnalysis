# Peerancheru Spelling Fix - CORRECT SOLUTION

## Problem
Clicking "Peerancheru" on the map shows 0 properties.

## Root Cause
**SPELLING MISMATCH:**
- Location name in `locations` table: `Peerancheru`
- Property areaname in `unified_data_DataType_Raghu`: `Peeramcheruvu`

When the API searches for "Peerancheru", it doesn't match "Peeramcheruvu", so 0 properties are returned.

## Solution
Update the location name from "Peerancheru" to "Peeramcheruvu" to match the property data.

## Properties Available
- `Peeramcheruvu`: 10 properties
- `Peeranchuruvu`: 8 properties (different location)

## How to Fix

### Run SQL in Supabase SQL Editor:
```sql
-- Update locations table
UPDATE locations 
SET name = 'Peeramcheruvu'
WHERE name = 'Peerancheru';

-- Update news table if needed
UPDATE news_balanced_corpus_1
SET location = 'Peeramcheruvu'
WHERE location = 'Peerancheru';
```

Or run the complete script:
```bash
# In Supabase SQL Editor, run:
fix_peerancheru_spelling.sql
```

## Result
- **Before**: "Peerancheru" → 0 properties
- **After**: "Peeramcheruvu" → 10 properties

## Files
- `fix_peerancheru_spelling.sql` - SQL script to run in Supabase
- `api.py` - Added `get_db()` function (still needed for properties endpoint)

## Important Notes
1. "Appa Junction Peerancheru" is a DIFFERENT location from "Peeramcheruvu"
2. "Patancheru" is also a DIFFERENT location (49 properties)
3. "Peeranchuruvu" is also a DIFFERENT location (8 properties)
4. Only "Peeramcheruvu" (10 properties) should show for this location

## Next Steps
1. Run `fix_peerancheru_spelling.sql` in Supabase SQL Editor
2. Restart API server: `python api.py`
3. Test by clicking "Peeramcheruvu" on the map (name will be updated)
