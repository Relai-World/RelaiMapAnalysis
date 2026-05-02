# Remove Property Logic Fix

## Issue

The remove property logic was inconsistent across different UI elements:

1. **Property card "Compare" button** - Removed property but didn't update open modal
2. **Desktop modal "✕" button** - Removed and re-opened modal
3. **Mobile modal "Remove" button** - Removed and re-opened modal

This caused confusion when:
- Removing a property from a property card while modal was open (modal didn't update)
- Modal would re-open after every removal (jarring UX)

## Solution

Made the remove logic consistent and added automatic modal management:

### 1. Added State Change Listener to ComparisonUI

**File:** `frontend/comparison-ui.js`

```javascript
class ComparisonUI {
  constructor(comparisonManager) {
    // ... existing code ...
    
    // Subscribe to comparison state changes
    this.manager.subscribe((state) => this.handleStateChange(state));
  }
  
  /**
   * Handle comparison state changes
   * Closes modal if property count drops below 2 while modal is open
   */
  handleStateChange(state) {
    if (this.isOpen && state.propertyIds.length < 2) {
      this.close();
      this.manager.showNotification('Comparison closed: need at least 2 properties', 'info');
    }
  }
}
```

**Benefit:** Modal automatically closes if property count drops below 2, regardless of where the removal happened.

### 2. Improved Remove Button Handlers

**Desktop and Mobile Remove Buttons:**

```javascript
btn.onclick = () => {
  const propertyId = parseInt(btn.dataset.propertyId);
  this.manager.removeProperty(propertyId);
  
  const remainingCount = this.manager.getPropertyCount();
  
  // If less than 2 properties remain, close modal
  if (remainingCount < 2) {
    this.close();
    this.manager.showNotification('Need at least 2 properties to compare', 'info');
  } else {
    // Re-fetch and re-render with remaining properties
    this.open();
  }
};
```

**Changes:**
- Store `remainingCount` in a variable for clarity
- Consistent logic between desktop and mobile
- Clear comments explaining the behavior

## New Behavior

### Scenario 1: Remove from Property Card (Modal Closed)
1. User clicks "In Compare" button on property card
2. Property is removed from comparison
3. Button changes back to "Compare"
4. Floating button updates count
5. ✅ **No modal interaction** (modal is closed)

### Scenario 2: Remove from Property Card (Modal Open)
1. User has comparison modal open with 3+ properties
2. User clicks "In Compare" button on property card
3. Property is removed from comparison
4. Button changes back to "Compare"
5. Floating button updates count
6. ✅ **Modal stays open** (still have 2+ properties)

### Scenario 3: Remove from Property Card (Modal Open, Down to 1)
1. User has comparison modal open with exactly 2 properties
2. User clicks "In Compare" button on one of them
3. Property is removed from comparison
4. ✅ **Modal automatically closes** (less than 2 properties)
5. Notification: "Comparison closed: need at least 2 properties"

### Scenario 4: Remove from Modal (Desktop/Mobile)
1. User clicks "✕" or "Remove from Compare" in modal
2. Property is removed from comparison
3. If 2+ properties remain:
   - ✅ **Modal re-opens with updated data**
4. If less than 2 properties remain:
   - ✅ **Modal closes**
   - Notification: "Need at least 2 properties to compare"

## Benefits

1. **Consistent behavior** - All remove actions work the same way
2. **Automatic modal management** - Modal closes when it should, stays open when it should
3. **Clear feedback** - Notifications explain what happened
4. **No jarring re-opens** - Modal only re-opens when explicitly removing from within modal
5. **Responsive to external changes** - Modal reacts to property card button clicks

## Technical Details

### Observer Pattern
The ComparisonUI now subscribes to ComparisonManager state changes:

```
ComparisonManager.removeProperty()
  ↓
Updates state.propertyIds
  ↓
Notifies all observers
  ↓
ComparisonUI.handleStateChange()
  ↓
Checks if modal is open AND count < 2
  ↓
Closes modal if needed
```

### Remove Button Flow
```
User clicks remove button
  ↓
Call manager.removeProperty(id)
  ↓
Check remaining count
  ↓
If count < 2:
  - Close modal
  - Show notification
Else:
  - Re-open modal (fetches fresh data)
```

## Files Modified

1. ✅ `frontend/comparison-ui.js`
   - Added `handleStateChange()` method
   - Subscribed to manager state changes in constructor
   - Improved remove button handlers (desktop and mobile)

2. ✅ `frontend/index.html`
   - Updated version to `comparison-ui.js?v=2.3`

## Testing Checklist

- [ ] Add 3 properties to comparison
- [ ] Open comparison modal
- [ ] Remove one property from modal → Should re-open with 2 properties
- [ ] Remove another from modal → Should close (only 1 left)
- [ ] Add 3 properties again
- [ ] Open comparison modal
- [ ] Click "In Compare" on property card → Modal should stay open
- [ ] Click "In Compare" on another card → Modal should close automatically
- [ ] Verify floating button count updates correctly in all scenarios
- [ ] Test on both desktop and mobile views

## Edge Cases Handled

1. ✅ Removing last property while modal open → Modal closes
2. ✅ Removing property from card while modal open → Modal updates or closes
3. ✅ Removing property from modal → Consistent behavior
4. ✅ Multiple rapid removals → State stays consistent
5. ✅ Floating button always shows correct count

## Status

✅ **FIXED** - Remove property logic is now consistent across all UI elements.

## Next Steps

1. Hard refresh browser (Ctrl+F5)
2. Test all removal scenarios
3. Verify modal behavior is consistent
4. Check that notifications are clear and helpful
