# Location Verification System - User Guide

## 📋 Overview

This system verifies ALL location coordinates in your database using Google Places API and provides:
- **Dry-run report** before making any changes
- **Budget-friendly** rate limiting (1.5s between API calls)
- **Safety checks** for large moves requiring manual review
- **Automatic backup** SQL scripts

## 🚀 How to Use

### Step 1: Run Verification (Dry Run)
```bash
python verify_and_fix_all_locations.py
```
- Select option `1`
- Wait for completion (~8-10 minutes for all locations)
- Reviews 3 generated files

### Step 2: Review the Reports

The system generates 3 files:

#### 1. **JSON Report** (`location_verification_dryrun_YYYYMMDD_HHMMSS.json`)
Complete detailed data for every location with:
- Current vs new coordinates
- Distance of move
- Recommended action
- Google Places data

#### 2. **CSV Report** (`location_verification_changes.csv`)
Excel-compatible spreadsheet for easy filtering and sorting

#### 3. **SQL Backup** (`locations_backup_YYYYMMDD_HHMMSS.sql`)
Rollback script to restore original coordinates if needed

### Step 3: Apply Updates
```bash
python verify_and_fix_all_locations.py
```
- Select option `2`
- Review summary
- Confirm with `yes` to apply updates

## 📊 Action Categories

The system categorizes each location:

| Category | Distance | Action |
|----------|----------|--------|
| **KEEP** | < 300m | Already accurate, no change |
| **UPDATE_MINOR** | 300m - 800m | Minor adjustment recommended |
| **UPDATE_MAJOR** | 800m - 2km | Significant improvement |
| **REVIEW_REQUIRED** | > 2km | Manual verification needed |
| **SKIP_NO_DATA** | N/A | Google returned no results |
| **SKIP_NON_HYD** | N/A | Non-Hyderabad location |

## ⚠️ Important Notes

### Budget Management
- **Rate Limit**: 1.5 seconds between API calls
- **Estimated Cost**: ~346 calls × $0.007 = ~$2.42 per full run
- **Recommendation**: Run monthly or when adding new locations

### Mixed City Data Issue
Your database contains both:
- **Hyderabad locations** (primary focus)
- **Bengaluru locations** (need separate verification)

The system flags Bengaluru locations but doesn't auto-update them due to large coordinate differences.

### Common Issues Found

1. **Appa Junction**: Currently at wrong location, needs 8.8km move
2. **Ashok Nagar**: Needs 10.77km correction
3. **Bacharam**: Ambiguous - could be Hyderabad or different Bacharam (129km away!)

## 🔧 Configuration

Edit these values in the script if needed:

```python
GOOGLE_API_KEY = "AIzaSyBi0vpchEjZNY3WL8fja0488QlXzhD6s-0"
RATE_LIMIT_DELAY = 1.5  # seconds
MAX_MOVE_DISTANCE_KM = 2.0  # review threshold
```

## 📁 Output Files Example

After running, you'll see files like:
```
location_verification_dryrun_20260312_143022.json
location_verification_changes.csv
locations_backup_20260312_143022.sql
```

## ✅ Best Practices

1. **Always run dry-run first** - Never skip the report review
2. **Check REVIEW_REQUIRED items** - These need your attention
3. **Keep backup SQL files** - Don't delete them immediately
4. **Run during off-peak** - API calls take time, don't rush
5. **Verify high-impact locations** - Check major moves manually

## 🆘 Troubleshooting

### Script hangs or stops
- Check internet connection
- Verify Google API key is valid
- Check API quota in Google Cloud Console

### Too many "No Result" locations
- Some localities may not exist in Google's database
- Try alternative spellings
- Consider using OpenStreetMap as fallback

### API costs too high
- Increase `RATE_LIMIT_DELAY` to reduce requests/minute
- Run only for specific locations (modify the query)
- Use cached results from previous runs

## 📞 Next Steps After Verification

1. Review CSV report in Excel
2. Manually verify "REVIEW_REQUIRED" locations on Google Maps
3. Apply updates with option 2
4. Test your frontend map to confirm improvements
5. Document any locations that needed manual intervention

---

**Generated**: March 12, 2026  
**System Version**: 1.0  
**API Provider**: Google Places + Geocoding
