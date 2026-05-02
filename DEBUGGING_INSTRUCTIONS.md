# Debugging Instructions - Comparison Feature

## Current Issue

The comparison modal shows "Failed to Load Comparison" error even after fixing the script loading order.

## Quick Debugging Steps

### Step 1: Clear Browser Cache
**This is the most important step!**

1. Press **Ctrl+Shift+Delete** (Windows) or **Cmd+Shift+Delete** (Mac)
2. Select "Cached images and files"
3. Click "Clear data"
4. **Hard refresh** the page: **Ctrl+F5** (Windows) or **Cmd+Shift+R** (Mac)

### Step 2: Check Browser Console

1. Press **F12** to open Developer Tools
2. Go to **Console** tab
3. Look for any **red error messages**
4. Share the error messages if you see any

### Step 3: Run Dependency Check

In the browser console, paste and run:

```javascript
console.log('=== DEPENDENCY CHECK ===');
console.log('callSupabaseRPC:', typeof callSupabaseRPC);
console.log('comparisonManager:', typeof window.comparisonManager);
console.log('comparisonUI:', typeof window.comparisonUI);

if (window.comparisonManager) {
  console.log('Property count:', window.comparisonManager.getPropertyCount());
  console.log('Property IDs:', window.comparisonManager.getPropertyIds());
}
```

**Expected output:**
```
callSupabaseRPC: function
comparisonManager: object
comparisonUI: object
Property count: 4 (or however many you added)
Property IDs: [12345, 67890, ...]
```

### Step 4: Test Property Fetch

In the browser console, paste and run:

```javascript
// Replace 53384 with an actual property ID from your comparison
const testId = window.comparisonManager.getPropertyIds()[0];
console.log('Testing property ID:', testId);

callSupabaseRPC('get_property_by_id_func', { prop_id: testId })
  .then(data => {
    console.log('✅ SUCCESS! Property data:', data);
  })
  .catch(error => {
    console.error('❌ ERROR:', error);
    console.error('Message:', error.message);
  });
```

### Step 5: Use Test Page

1. Open `test_comparison.html` in your browser
2. Click "Run Check" in section 1
3. Enter a property ID and click "Fetch Property" in section 2
4. Follow the test results

## Common Issues & Solutions

### Issue 1: "callSupabaseRPC is not defined"

**Cause:** Browser is still using cached old version of scripts

**Solution:**
1. Clear browser cache completely
2. Hard refresh (Ctrl+F5)
3. Check that `app.js?v=6.2` is loading (Network tab in DevTools)

### Issue 2: "Property not found" or empty array

**Cause:** Property ID doesn't exist in database

**Solution:**
1. Verify property IDs are valid
2. Try with a known good property ID (e.g., 53384)
3. Check Supabase database to confirm property exists

### Issue 3: "get_property_by_id_func does not exist"

**Cause:** Supabase RPC function not created or wrong permissions

**Solution:**
1. Check if function exists in Supabase SQL Editor:
   ```sql
   SELECT * FROM pg_proc WHERE proname = 'get_property_by_id_func';
   ```
2. If not found, run the SQL from `supabase_functions.sql`
3. Grant permissions:
   ```sql
   GRANT EXECUTE ON FUNCTION get_property_by_id_func(integer) TO anon, authenticated;
   ```

### Issue 4: CORS error

**Cause:** Supabase CORS settings or wrong URL

**Solution:**
1. Check `.env` file has correct Supabase URL and key
2. Verify Supabase project is active
3. Check Supabase dashboard for CORS settings

### Issue 5: Network error / Failed to fetch

**Cause:** Network connectivity or Supabase down

**Solution:**
1. Check internet connection
2. Check Supabase status: https://status.supabase.com/
3. Verify Supabase project is not paused

## Manual Test in Console

Run this complete test in browser console:

```javascript
async function fullTest() {
  console.log('🧪 Starting full comparison test...\n');
  
  // 1. Check dependencies
  console.log('1️⃣ Dependencies:');
  console.log('  callSupabaseRPC:', typeof callSupabaseRPC);
  console.log('  comparisonManager:', typeof window.comparisonManager);
  console.log('  comparisonUI:', typeof window.comparisonUI);
  
  if (typeof callSupabaseRPC === 'undefined') {
    console.error('❌ STOP: callSupabaseRPC not found!');
    return;
  }
  
  // 2. Check comparison state
  console.log('\n2️⃣ Comparison state:');
  const ids = window.comparisonManager.getPropertyIds();
  console.log('  Property IDs:', ids);
  console.log('  Count:', ids.length);
  
  if (ids.length === 0) {
    console.warn('⚠️ No properties in comparison. Add some first.');
    return;
  }
  
  // 3. Test fetching first property
  console.log('\n3️⃣ Testing property fetch:');
  const testId = ids[0];
  console.log('  Fetching property', testId, '...');
  
  try {
    const data = await callSupabaseRPC('get_property_by_id_func', { prop_id: testId });
    console.log('  ✅ Success!');
    console.log('  Data:', data);
  } catch (error) {
    console.error('  ❌ Failed:', error.message);
    return;
  }
  
  // 4. Test full comparison fetch
  console.log('\n4️⃣ Testing full comparison fetch:');
  try {
    const compData = await window.comparisonManager.fetchAllComparisonData();
    console.log('  ✅ Success!');
    console.log('  Properties:', compData.properties.length);
    console.log('  Location insights:', compData.locationInsights.size);
  } catch (error) {
    console.error('  ❌ Failed:', error.message);
    console.error('  Stack:', error.stack);
    return;
  }
  
  console.log('\n✅ All tests passed! Comparison should work.');
}

fullTest();
```

## Files to Check

1. **`frontend/index.html`** - Script loading order (lines 351-357)
2. **`frontend/app.js`** - callSupabaseRPC function (around line 61)
3. **`frontend/comparison-manager.js`** - ComparisonManager class
4. **`.env`** - Supabase credentials

## Script Loading Order (Should Be)

```html
<!-- Line 351 -->
<script src="app.js?v=6.2"></script>

<!-- Line 354 -->
<script src="comparison-manager.js?v=2.0"></script>

<!-- Line 357 -->
<script src="comparison-ui.js?v=2.0"></script>
```

## Next Steps

1. ✅ Clear browser cache and hard refresh
2. ✅ Check browser console for errors
3. ✅ Run dependency check in console
4. ✅ Test property fetch in console
5. ✅ Use test_comparison.html for detailed testing
6. 📧 Share console errors if still not working

## Contact

If still not working after these steps, please share:
1. Browser console errors (screenshot or copy/paste)
2. Output of the dependency check
3. Output of the property fetch test
4. Browser name and version
