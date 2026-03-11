# Testing the Properties Panel Feature

## 🧪 Test Scenarios

### Test 1: Basic Flow
1. Open the app in browser
2. Click on any location pin (e.g., "Gachibowli")
3. **Expected**: 
   - Left intel card shows location analytics
   - Right properties panel slides in
   - Property cards appear with images, names, prices

### Test 2: Property Detail View
1. After properties panel is open
2. Click on any property card
3. **Expected**:
   - Detail drawer slides over from right
   - Shows full property information in organized sections
   - Gallery images scroll horizontally
   - All sections render properly

### Test 3: Navigation
1. In detail drawer, click "← Back" button
2. **Expected**: Returns to properties list
3. Click "✕" close button on properties panel
4. **Expected**: Both panels close

### Test 4: Empty State
1. Click on a location with no properties
2. **Expected**: Shows "No properties found" message

### Test 5: Error Handling
1. Disconnect from internet
2. Click on a location
3. **Expected**: Shows error message gracefully

## 🔍 What to Check

### Visual Checks
- [ ] Properties panel slides smoothly from right
- [ ] Property cards have proper spacing and alignment
- [ ] Images load correctly (or show placeholder)
- [ ] Badges have correct colors (green/orange/red)
- [ ] Detail drawer overlays properties panel correctly
- [ ] Typography is consistent with rest of app
- [ ] Gold/cream theme is maintained

### Functional Checks
- [ ] Clicking location opens properties panel
- [ ] Clicking property card opens detail drawer
- [ ] Back button returns to property list
- [ ] Close buttons work on both panels
- [ ] Multiple locations can be selected sequentially
- [ ] Panel states don't conflict with amenities panel

### Data Checks
- [ ] Property names display correctly
- [ ] Prices format properly (₹X.XX Cr)
- [ ] BHK configurations show correctly
- [ ] Builder names appear
- [ ] Status badges match construction_status
- [ ] Google ratings display when available
- [ ] All detail sections populate with data

## 🐛 Common Issues & Fixes

### Issue: Properties panel doesn't open
**Fix**: Check browser console for API errors. Ensure backend is running.

### Issue: Images don't load
**Fix**: Check if `images` field in database contains valid JSON array of URLs.

### Issue: Detail drawer shows "Loading..." forever
**Fix**: Check `/api/v1/properties/{id}` endpoint response in Network tab.

### Issue: Panels overlap incorrectly
**Fix**: Check CSS classes `.open` and `.detail-open` are being applied.

## 📱 Browser Testing

Test on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Chrome
- [ ] Mobile Safari

## 🎯 Performance Checks

- [ ] Properties load within 2 seconds
- [ ] Detail view loads within 1 second
- [ ] Smooth animations (60fps)
- [ ] No memory leaks when opening/closing multiple times
- [ ] Images lazy load properly

## 📊 Test Data

### Locations with Many Properties
- Kompally (653 properties)
- Tellapur (413 properties)
- Bachupally (405 properties)

### Locations to Test
- Gachibowli
- Kondapur
- Kukatpally
- Miyapur
- Kokapet

## ✅ Success Criteria

Feature is working correctly if:
1. Properties panel opens when location is clicked
2. Property cards display with correct information
3. Detail drawer opens when card is clicked
4. All sections in detail view render properly
5. Navigation (back/close) works smoothly
6. No console errors
7. UI matches the luxury theme
8. Performance is acceptable (<2s load times)

---

**Ready to Test!** 🚀

Start your backend server and open the frontend to begin testing.
