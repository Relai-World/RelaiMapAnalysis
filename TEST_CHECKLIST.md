# Consultation Report - Test Checklist

## Pre-Testing Setup

- [ ] Backend running: `python api.py`
- [ ] Frontend accessible in browser
- [ ] Browser console open (F12) for monitoring
- [ ] No JavaScript errors on page load

---

## Test 1: Session Tracking

### Actions
- [ ] Click on 3-5 different locations on map
- [ ] View 5-10 property details
- [ ] Add 2-3 properties to comparison

### Verify in Console
- [ ] See: `📋 Consultation session started`
- [ ] See: `📍 Location viewed: [area name]`
- [ ] See: `🏠 Property viewed: [property name]`
- [ ] See: `📊 Properties compared: [count]`

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 2: Map Capture Button

### Actions
- [ ] Look for button in top-right corner of map
- [ ] Button shows: "📸 Capture Map View"
- [ ] Enable 2-3 layers (Metro, Floods, etc.)
- [ ] Zoom to interesting area
- [ ] Click capture button

### Verify
- [ ] Button briefly turns green
- [ ] Notification: "Map view captured!"
- [ ] Console shows: `📸 Map state captured`
- [ ] Capture multiple views (3-5 times)

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 3: Export Menu

### Actions
- [ ] Open comparison modal (compare 2+ properties)
- [ ] Click "📥 Export" button
- [ ] Export menu appears

### Verify Menu Shows
- [ ] 📋 Consultation Report option (first)
- [ ] 📄 Comparison PDF option
- [ ] 📊 Export as CSV option
- [ ] Cancel button

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 4: Consultation Report Modal

### Actions
- [ ] Click "📋 Consultation Report" in export menu
- [ ] Modal appears

### Verify Modal Contains
- [ ] Title: "📋 Generate Consultation Report"
- [ ] Description text
- [ ] Client Name field (optional)
- [ ] Consultant Name field (optional)
- [ ] Expert Recommendations textarea
- [ ] Session statistics showing:
  - [ ] Locations Explored: [number]
  - [ ] Properties Viewed: [number]
  - [ ] Map Screenshots: [number]
- [ ] Cancel button
- [ ] Generate Report button

### Fill Out Form
- [ ] Enter client name: "Test Client"
- [ ] Enter consultant name: "Test Consultant"
- [ ] Enter recommendations: "This is a test recommendation..."

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 5: PDF Generation

### Actions
- [ ] Click "Generate Report" button
- [ ] Wait for generation

### Verify
- [ ] Modal closes
- [ ] Notification: "Generating consultation report..."
- [ ] PDF downloads automatically (check Downloads folder)
- [ ] Success notification: "Consultation report generated successfully!"
- [ ] No errors in console

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 6: PDF Content - Cover Page

### Open Downloaded PDF

### Verify Page 1 Contains
- [ ] Title: "Property Consultation Report"
- [ ] Date and time
- [ ] Client name: "Test Client"
- [ ] Consultant name: "Test Consultant"
- [ ] Session duration
- [ ] 3 colored stat cards showing counts
- [ ] List of locations explored
- [ ] List of properties viewed

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 7: PDF Content - Map Screenshots

### Verify Map Pages
- [ ] Each captured map appears as separate page
- [ ] Timestamp shown for each
- [ ] Zoom level shown
- [ ] Active layers listed
- [ ] Screenshot is clear and readable
- [ ] All captured maps included

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 8: PDF Content - Property Comparison

### Verify Comparison Section
- [ ] Section title: "Property Comparison"
- [ ] Full comparison table included
- [ ] All sections present:
  - [ ] 💰 Pricing
  - [ ] 🏗️ Project Information
  - [ ] 📐 Unit Specifications
  - [ ] 📍 Location & Ratings
  - [ ] 🏊 Amenities
  - [ ] 📋 Property Reviews
- [ ] No close/export buttons visible
- [ ] Data is readable and formatted correctly

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 9: PDF Content - Location Insights

### Verify Insights Section
- [ ] Section title: "Location Insights"
- [ ] Card for each location explored
- [ ] Each card shows:
  - [ ] Location name
  - [ ] 4 grid scores (Connectivity, Amenities, Growth, Investment)
  - [ ] Key highlights (if available)
  - [ ] Concerns (if available)
- [ ] Professional formatting with colors

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 10: PDF Content - Expert Recommendations

### Verify Recommendations Section
- [ ] Section title: "Expert Recommendations"
- [ ] Expert notes displayed: "This is a test recommendation..."
- [ ] "Recommended Next Steps" section
- [ ] Follow-up information
- [ ] Professional formatting

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 11: PDF Quality

### Verify Overall Quality
- [ ] All text is readable
- [ ] No overlapping text
- [ ] Images are clear (not blurry)
- [ ] Colors look professional
- [ ] Special characters render correctly (₹, emojis)
- [ ] Page breaks are appropriate
- [ ] No UI buttons in PDF
- [ ] Professional appearance

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 12: Edge Cases

### Test Without Map Screenshots
- [ ] Don't capture any maps
- [ ] Generate report
- [ ] Verify: Report skips map section, includes others

### Test Without Expert Notes
- [ ] Leave expert notes blank
- [ ] Generate report
- [ ] Verify: Report skips recommendations section

### Test With Many Screenshots
- [ ] Capture 5+ map views
- [ ] Generate report
- [ ] Verify: All screenshots included, PDF size reasonable

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 13: Multiple Reports

### Actions
- [ ] Generate first report
- [ ] Capture more maps
- [ ] View more properties
- [ ] Generate second report

### Verify
- [ ] Second report includes new data
- [ ] Both reports download successfully
- [ ] No interference between reports

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 14: Mobile Responsiveness (Optional)

### On Mobile Device or Narrow Browser
- [ ] Map capture button visible and clickable
- [ ] Export menu displays correctly
- [ ] Modal fits screen
- [ ] Form fields are usable
- [ ] Buttons are tappable

**Status**: ⬜ Pass / ⬜ Fail / ⬜ Skipped

---

## Test 15: Browser Compatibility

### Test in Different Browsers
- [ ] Chrome: ⬜ Pass / ⬜ Fail
- [ ] Edge: ⬜ Pass / ⬜ Fail
- [ ] Firefox: ⬜ Pass / ⬜ Fail
- [ ] Safari: ⬜ Pass / ⬜ Fail / ⬜ Skipped

**Status**: ⬜ Pass / ⬜ Fail

---

## Final Verification

### Overall Assessment
- [ ] All core features working
- [ ] PDF generates successfully
- [ ] Report content is complete
- [ ] Formatting is professional
- [ ] No critical bugs found

### Performance
- [ ] PDF generation time acceptable (< 15 seconds)
- [ ] File size reasonable (< 10 MB)
- [ ] No browser freezing

### User Experience
- [ ] Interface is intuitive
- [ ] Buttons are easy to find
- [ ] Modal is clear and helpful
- [ ] Notifications are informative

---

## Issues Found

### Critical Issues (Must Fix)
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

### Minor Issues (Nice to Fix)
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

### Suggestions for Improvement
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

---

## Sign-Off

**Tester Name**: _______________________
**Date**: _______________________
**Overall Status**: ⬜ PASS / ⬜ FAIL / ⬜ PASS WITH ISSUES

**Notes**:
_________________________________________________
_________________________________________________
_________________________________________________
_________________________________________________

---

## Next Steps After Testing

### If All Tests Pass ✅
- [ ] Show to team for feedback
- [ ] Test with real consultation
- [ ] Gather client reactions
- [ ] Plan Phase 2 enhancements

### If Issues Found ❌
- [ ] Document all issues
- [ ] Prioritize fixes
- [ ] Fix critical issues
- [ ] Re-test

---

**Ready to test!** Follow this checklist step-by-step. 🚀
