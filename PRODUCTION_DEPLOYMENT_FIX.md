# Production Deployment Fix - API Connection Issues

## Problem
After deployment, the comparison modal shows:
- ❌ "Unable to fetch" for all amenities
- ❌ "Unable to generate review" for property reviews

## Root Cause
The frontend JavaScript files had hardcoded `http://localhost:8000` URLs instead of using the dynamic `window.API_BASE_URL` configuration.

## ✅ Fixed Files
1. **frontend/comparison-ui.js** - Line 654 (amenities endpoint)
2. **frontend/comparison-ui.js** - Line 720 (property review endpoint)

Changed from:
```javascript
fetch('http://localhost:8000/api/nearby-amenities', ...)
fetch('http://localhost:8000/api/property-review', ...)
```

To:
```javascript
fetch(`${window.API_BASE_URL}/api/nearby-amenities`, ...)
fetch(`${window.API_BASE_URL}/api/property-review`, ...)
```

## 🚀 Deployment Steps

### 1. Push Changes to GitHub
```bash
git add frontend/comparison-ui.js
git commit -m "Fix: Use dynamic API_BASE_URL for production deployment"
git push origin rishikaCode
```

### 2. Configure Render Environment Variables

On your Render backend service (https://relaimapanalysis.onrender.com), set these environment variables:

#### Required Environment Variables:
```bash
# Set environment to production
ENVIRONMENT=production

# Frontend origins (comma-separated)
FRONTEND_ORIGIN=https://analytics.relai.world,https://relai-world.github.io

# API Keys
GOOGLE_PLACES_API_KEY=your_google_places_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
BACKEND_API_KEY=relai-map-analysis-secure-key-2026

# Supabase
SUPABASE_URL=https://ihraowxbduhlichzszgk.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

### 3. Verify Frontend Config

Make sure **frontend/config.js** has the correct production URL:
```javascript
const API_CONFIG = {
  PRODUCTION_API_URL: 'https://relaimapanalysis.onrender.com',
  LOCAL_API_URL: 'http://127.0.0.1:8000'
};
```

### 4. Deploy Frontend

If using GitHub Pages:
```bash
# Push to main branch (or your deployment branch)
git checkout main
git merge rishikaCode
git push origin main
```

### 5. Test Production

1. Open: https://analytics.relai.world
2. Select 2 properties
3. Click "Compare Properties"
4. Verify:
   - ✅ Amenities counts load (Hospitals, Schools, Malls, Restaurants, Metro)
   - ✅ Property reviews generate successfully

## 🔍 Debugging

### Check CORS in Browser Console
If you still see errors, open browser DevTools (F12) and check:

1. **Network Tab**: Look for failed requests to the API
2. **Console Tab**: Look for CORS errors like:
   ```
   Access to fetch at 'https://relaimapanalysis.onrender.com/api/nearby-amenities' 
   from origin 'https://analytics.relai.world' has been blocked by CORS policy
   ```

### Verify Backend CORS Configuration
Check Render logs for:
```
🌐 CORS allowed origins: ['https://analytics.relai.world', 'https://relai-world.github.io']
```

### Common Issues

1. **Wrong ENVIRONMENT setting**: Make sure `ENVIRONMENT=production` on Render
2. **Missing FRONTEND_ORIGIN**: Add your production domain to Render env vars
3. **Cache issues**: Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
4. **Old deployment**: Make sure latest code is deployed on both frontend and backend

## 📝 CORS Configuration Explained

The backend (api.py) reads allowed origins from:
1. `FRONTEND_ORIGIN` environment variable (comma-separated list)
2. Hardcoded production domains: `analytics.relai.world` and `relai-world.github.io`
3. Development ports (only when `ENVIRONMENT=development`)

## ✅ Checklist

- [ ] Fixed hardcoded localhost URLs in comparison-ui.js
- [ ] Pushed changes to GitHub
- [ ] Set `ENVIRONMENT=production` on Render
- [ ] Set `FRONTEND_ORIGIN` on Render with production domains
- [ ] Verified all API keys are set on Render
- [ ] Deployed frontend to GitHub Pages
- [ ] Tested amenities loading in production
- [ ] Tested property reviews in production
- [ ] Checked browser console for errors
- [ ] Verified CORS headers in Network tab

## 🎯 Expected Result

After these fixes:
- ✅ Amenities counts load from Google Places API
- ✅ Property reviews generate using Perplexity AI
- ✅ All API calls work in production
- ✅ CORS allows requests from your production domain
