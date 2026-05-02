# Troubleshooting: "Failed to Load Comparison" Error

## Quick Diagnosis

Open your browser's Developer Console (F12) and run these commands one by one:

### Step 1: Check if managers exist
```javascript
console.log('ComparisonManager:', window.comparisonManager);
console.log('ComparisonUI:', window.comparisonUI);
```

**Expected:** Both should show objects, not `undefined`

---

### Step 2: Check property IDs in comparison
```javascript
console.log('Property IDs:', window.comparisonManager.getPropertyIds());
console.log('Property count:', window.comparisonManager.getPropertyCount());
```

**Expected:** Should show array of property IDs and count >= 2

---

### Step 3: Check if Supabase RPC function exists
```javascript
console.log('callSupabaseRPC:', typeof callSupabaseRPC);
```

**Expected:** Should show `"function"`, not `"undefined"`

---

### Step 4: Test fetching a single property
```javascript
// Replace 12345 with an actual property ID from your comparison
const testId = window.comparisonManager.getPropertyIds()[0];
console.log('Testing property ID:', testId);

callSupabaseRPC('get_property_by_id_func', { prop_id: testId })
  .then(data => {
    console.log('✅ Success! Property data:', data);
  })
  .catch(error => {
    console.error('❌ Error:', error);
  });
```

**Expected:** Should show property data, not an error

---

### Step 5: Test fetching location insights
```javascript
callSupabaseRPC('get_all_insights')
  .then(data => {
    console.log('✅ Success! Location insights count:', data.length);
    console.log('Sample:', data[0]);
  })
  .catch(error => {
    console.error('❌ Error:', error);
  });
```

**Expected:** Should show array of location insights

---

### Step 6: Test full comparison fetch
```javascript
window.comparisonManager.fetchAllComparisonData()
  .then(data => {
    console.log('✅ Success!');
    console.log('Properties:', data.properties.length);
    console.log('Location insights:', data.locationInsights.size);
  })
  .catch(error => {
    console.error('❌ Error:', error);
    console.error('Message:', error.message);
    console.error('Stack:', error.stack);
  });
```

**Expected:** Should show comparison data

---

## Common Issues & Solutions

### Issue 1: `callSupabaseRPC is not defined`

**Cause:** `app.js` not loaded or loaded after `comparison-manager.js`

**Solution:** Check `index.html` script loading order:
```html
<!-- Should be in this order -->
<script src="app.js"></script>
<script src="comparison-manager.js"></script>
<script src="comparison-ui.js"></script>
```

---

### Issue 2: `Cannot read property 'getPropertyIds' of undefined`

**Cause:** `comparisonManager` not initialized

**Solution:** Check if `comparison-manager.js` is loaded:
```javascript
// In browser console
console.log(window.comparisonManager);
```

If undefined, check for JavaScript errors in console that might be preventing initialization.

---

### Issue 3: `Property fetch returns empty array`

**Cause:** Property ID doesn't exist in database

**Solution:** Verify property IDs are valid:
```javascript
// Check what IDs are in comparison
console.log(window.comparisonManager.getPropertyIds());

// Test if property exists in database
callSupabaseRPC('get_property_by_id_func', { prop_id: YOUR_ID })
  .then(data => console.log('Property exists:', data))
  .catch(err => console.error('Property not found:', err));
```

---

### Issue 4: `Network error` or `Failed to fetch`

**Cause:** Supabase connection issue

**Solution:** 
1. Check `.env` file has correct Supabase credentials
2. Check network tab in DevTools for failed requests
3. Verify Supabase project is active
4. Check CORS settings in Supabase

---

### Issue 5: `get_all_insights` returns error

**Cause:** RPC function doesn't exist or has wrong permissions

**Solution:**
1. Check if function exists in Supabase:
   ```sql
   SELECT * FROM pg_proc WHERE proname = 'get_all_insights';
   ```

2. Check function permissions:
   ```sql
   GRANT EXECUTE ON FUNCTION get_all_insights() TO anon, authenticated;
   ```

3. If function doesn't exist, run the SQL from `supabase_functions.sql`

---

### Issue 6: Properties in comparison but still shows error

**Cause:** One or more properties failed to fetch

**Solution:** Check which property is failing:
```javascript
const ids = window.comparisonManager.getPropertyIds();

for (const id of ids) {
  try {
    const data = await callSupabaseRPC('get_property_by_id_func', { prop_id: id });
    console.log(`✅ Property ${id}:`, data);
  } catch (error) {
    console.error(`❌ Property ${id} failed:`, error);
  }
}
```

---

## Automated Debug Script

Load and run the debug script:

```html
<!-- Add to index.html temporarily -->
<script src="debug_comparison_issue.js"></script>
```

Then in console:
```javascript
debugComparisonIssue();
```

This will run all tests automatically and show you exactly where the issue is.

---

## Check Script Loading Order

In `index.html`, verify scripts are loaded in this order:

```html
<!-- 1. Supabase client -->
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>

<!-- 2. Main app (includes callSupabaseRPC) -->
<script src="app.js"></script>

<!-- 3. Comparison manager (uses callSupabaseRPC) -->
<script src="comparison-manager.js"></script>

<!-- 4. Comparison UI (uses comparisonManager) -->
<script src="comparison-ui.js"></script>
```

---

## Enable Verbose Logging

Temporarily add more logging to see exactly where it fails:

```javascript
// In browser console, before opening comparison
window.comparisonManager.fetchAllComparisonData = async function() {
  console.log('🔄 Starting fetchAllComparisonData...');
  console.log('Property IDs:', this.state.propertyIds);
  
  try {
    console.log('📡 Fetching properties...');
    const propertyPromises = this.state.propertyIds.map(id => {
      console.log(`  Fetching property ${id}...`);
      return this.fetchPropertyDetails(id).catch(err => {
        console.error(`  ❌ Failed to fetch property ${id}:`, err);
        return null;
      });
    });
    
    const properties = await Promise.all(propertyPromises);
    console.log('✅ All properties fetched:', properties);
    
    const validProperties = properties.filter(p => p !== null);
    console.log('✅ Valid properties:', validProperties.length);
    
    // ... rest of the function
  } catch (error) {
    console.error('❌ fetchAllComparisonData failed:', error);
    throw error;
  }
};
```

---

## Most Likely Causes (in order)

1. **Property ID doesn't exist** - Check if the property IDs in comparison are valid
2. **Supabase RPC function error** - Check if `get_property_by_id_func` works
3. **Script loading order** - Check if `app.js` loads before `comparison-manager.js`
4. **Network/CORS issue** - Check browser network tab for failed requests
5. **Missing Supabase credentials** - Check `.env` file

---

## Quick Fix: Clear and Re-add Properties

Sometimes the comparison state gets corrupted. Try:

```javascript
// Clear all properties
window.comparisonManager.clearAll();

// Add fresh properties (replace with your actual IDs)
window.comparisonManager.addProperty(12345);
window.comparisonManager.addProperty(67890);

// Try opening comparison again
window.comparisonUI.open();
```

---

## Still Not Working?

Share the output of this command:

```javascript
// Run this and share the output
console.log('=== COMPARISON DEBUG INFO ===');
console.log('Property IDs:', window.comparisonManager?.getPropertyIds());
console.log('Property count:', window.comparisonManager?.getPropertyCount());
console.log('callSupabaseRPC exists:', typeof callSupabaseRPC !== 'undefined');
console.log('Supabase client exists:', typeof window.supabase !== 'undefined');

// Test a simple RPC call
callSupabaseRPC('get_all_insights')
  .then(data => console.log('✅ RPC works, insights count:', data.length))
  .catch(err => console.error('❌ RPC failed:', err.message));
```

Then I can help you debug further based on the output.
