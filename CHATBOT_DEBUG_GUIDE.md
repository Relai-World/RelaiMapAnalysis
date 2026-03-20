# Chatbot Debugging Guide for Render Deployment

## Issue: Chatbot not appearing on deployed site

The chatbot should appear when you click on location pins on the map. Here's how to debug:

## Step 1: Check Browser Console

1. Open your deployed site: `https://your-app.onrender.com`
2. Open browser developer tools (F12)
3. Go to Console tab
4. Look for any JavaScript errors

**Expected console messages when clicking a location:**
```
🚀 showFutureDevChatbot called for: [Location Name]
```

## Step 2: Test File Loading

Check if all files are loading properly:

1. In Network tab, refresh the page
2. Look for these files:
   - `app.js?v=4.1` - Should load successfully (200 status)
   - `style.css?v=5.5` - Should load successfully (200 status)
   - `config.js` - Should load successfully (200 status)

## Step 3: Manual Test

Open browser console and run:

```javascript
// Test if functions exist
console.log('showFutureDevChatbot exists:', typeof showFutureDevChatbot !== 'undefined');

// Test manual trigger
if (typeof showFutureDevChatbot !== 'undefined') {
  showFutureDevChatbot({
    location: "Test Location",
    location_id: 1
  });
}
```

## Step 4: Check Map Click Events

1. Click on any location pin on the map
2. Check console for:
   - "Location clicked:" message
   - Any error messages

## Step 5: API Connection Test

Test if API is working:

```javascript
fetch('https://hyderabad-intelligence.onrender.com/locations')
  .then(r => r.json())
  .then(data => console.log('API working, locations:', data.length))
  .catch(err => console.error('API error:', err));
```

## Common Issues & Solutions

### Issue 1: Files not loading (404 errors)
**Solution:** Check if files exist in your deployed repository

### Issue 2: JavaScript errors
**Solution:** Check console for specific error messages

### Issue 3: API URL mismatch
**Solution:** Verify `config.js` has correct production URL

### Issue 4: CSS not loading
**Solution:** Check if `style.css` loads and contains chatbot styles

### Issue 5: Map not loading locations
**Solution:** Check if location data is loading from API

## Quick Fix Test

If chatbot functions exist but aren't triggering, try this in console:

```javascript
// Force create robot icon
const robotIcon = document.createElement('div');
robotIcon.id = 'chatbot-robot-icon';
robotIcon.className = 'chatbot-robot-icon robot-visible';
robotIcon.style.cssText = `
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #a68a3d, #d4af37);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 1000;
`;
robotIcon.innerHTML = '<span style="font-size: 24px;">🤖</span>';
document.body.appendChild(robotIcon);
```

## Next Steps

1. Run the debug HTML file I created: `debug_chatbot_deployment.html`
2. Check your browser console for errors
3. Verify all files are loading correctly
4. Test API connection

Let me know what you find in the console and I'll help fix the specific issue!