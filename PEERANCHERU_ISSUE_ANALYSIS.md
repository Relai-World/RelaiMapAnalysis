# Peerancheru Property Data Issue - Analysis & Solution

## Problem
When clicking on "Peerancheru" on the map, no properties are shown.

## Root Cause Analysis

### 1. What Happens When You Click a Location
1. Frontend sends location name (e.g., "Peerancheru") to API
2. API calls `get_properties_by_area("Peerancheru")`
3. API searches `unified_data_DataType_Raghu` table WHERE `areaname` matches "Peerancheru"
4. No matches found → 0 properties returned

### 2. The Data Mismatch
**Properties exist with these spellings:**
- `Patancheru` - 49 properties
- `Patancheruvu` - 166 properties
- `Peeramcheruvu` - 10 properties
- `Peeranchuruvu` - 8 properties
- `Peerzadiguda` - 97 properties
- `Appa Junction Peerancheru` - 4 properties

**Total: 334 properties**

**But the location name being searched is:**
- `Peerancheru` (from the map click)

### 3. Why This Happens
The `locations` table likely has "Peerancheru" as the location name, but the properties in `unified_data_DataType_Raghu` use different spellings in the `areaname` field.

## Solutions

### Option 1: Update Location Name in locations Table (RECOMMENDED)
Change the location name to match the most common spelling in properties.

**Pros:**
- Simple one-time fix
- No code changes needed
- Works immediately

**Steps:**
1. Find the location ID for Peerancheru in `locations` table
2. Update the name to "Patancheruvu" (most properties: 166)
3. Or create aliases/alternate names

### Option 2: Add Fuzzy Matching to API
Enhance the API to handle spelling variations.

**Pros:**
- Handles all spelling variations automatically
- More robust for future cases

**Cons:**
- Requires code changes
- May match unintended locations

### Option 3: Normalize Property Data
Update all property `areaname` values to use consistent spelling.

**Pros:**
- Clean data
- Prevents future issues

**Cons:**
- Requires updating 334 records
- Time-consuming
- May break existing references

## Recommended Action

**Use Option 1**: Update the location name in the `locations` table to match the property data.

Since "Patancheruvu" has the most properties (166), update the location name to "Patancheruvu" or add it as an alternate name.

## Next Steps

1. Check if "Peerancheru" exists in `locations` table
2. If yes, update its name to "Patancheruvu"
3. If no, add "Patancheruvu" as a new location with proper coordinates
4. Test by clicking the location on the map
