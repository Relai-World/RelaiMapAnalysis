# Quick Start Guide - Property Comparison Feature

## 🚀 Start the Application

### 1. Start Backend
```bash
python api.py
```
✅ Backend running on: http://localhost:8000

### 2. Open Frontend
Open browser to: http://localhost:5501 (or your configured port)

---

## 🧪 Test the Features

### Test Property Reviews
1. Search and compare 2-3 properties
2. Scroll to "📋 Property Reviews" section
3. Wait for reviews to load (shows "Fetching property review...")
4. Verify reviews are:
   - ✅ Unique insights (not repeating table data)
   - ✅ Complete sentences
   - ✅ Realistic about location issues
   - ✅ Helpful for decision-making

### Test PDF Export
1. Click "Export to PDF" button
2. Wait for "Generating PDF..." notification
3. Check downloaded PDF contains:
   - ✅ All property columns
   - ✅ All sections (Pricing, Project Info, Specs, Location, Amenities, Reviews)
   - ✅ Proper formatting and colors
   - ✅ Property reviews included

---

## 🔧 Troubleshooting

### Reviews Not Loading
- Check backend is running: `python api.py`
- Check browser console (F12) for errors
- Verify `PERPLEXITY_API_KEY` in `.env` file

### PDF Export Not Working
- Check browser console (F12) for errors
- Verify html2pdf.js is loaded (check Network tab)
- Try refreshing the page

### Old/Bad Reviews
Clear and regenerate:
```sql
UPDATE "unified_data_DataType_Raghu" SET "Property_Review" = NULL;
```
Then restart backend: `python api.py`

---

## 📋 What Was Fixed

### PDF Export
- ❌ **Before**: Garbled text, missing sections, poor layout
- ✅ **After**: Clean capture of actual UI, all sections included, professional quality

### Property Reviews
- ❌ **Before**: Repeated table data, incomplete sentences, unrealistic
- ✅ **After**: Unique insights, complete sentences, realistic and helpful

---

## 📁 Key Files

### Backend
- `api.py` - Property review endpoint (lines 860-1050)

### Frontend
- `frontend/comparison-ui.js` - Review rendering & PDF export
- `frontend/index.html` - Library imports

### Database
- `add_property_review_column.sql` - Schema update
- `clear_property_reviews.sql` - Clear old reviews

---

## 🎯 Success Checklist

- [ ] Backend running on port 8000
- [ ] Frontend accessible in browser
- [ ] Can compare multiple properties
- [ ] Property reviews load and display correctly
- [ ] Reviews provide unique insights (not repeating table data)
- [ ] Reviews are complete sentences
- [ ] PDF export works
- [ ] PDF contains all sections including reviews
- [ ] PDF formatting looks professional

---

## 💡 Tips

1. **First Time Setup**: Clear old reviews to get new improved ones
2. **Performance**: Reviews are cached in database for fast loading
3. **Quality**: If a review isn't helpful, clear it and regenerate
4. **PDF Size**: A3 landscape format fits wide comparison tables better
5. **Browser**: Works best in Chrome/Edge (html2pdf compatibility)

---

## 🔑 Environment Variables

Required in `.env` file:
```env
PERPLEXITY_API_KEY=your_key_here
SUPABASE_URL=your_url_here
SUPABASE_KEY=your_key_here
GOOGLE_PLACES_API_KEY=your_key_here
```

---

**Status**: ✅ Ready to test!
