# Local Development Setup

## Quick Start

### 1. Set Environment to Development
In `.env`, make sure you have:
```env
ENVIRONMENT=development
```

This automatically enables CORS for common development ports (5500, 8000, 3000).

### 2. Start Backend Server
```bash
uvicorn api:app --reload
```

Server will run on: `http://127.0.0.1:8000`

### 3. Open Frontend

**Option A: Using Live Server (VS Code Extension)**
- Right-click `frontend/index.html`
- Select "Open with Live Server"
- Opens on: `http://127.0.0.1:5500` or `http://localhost:5500`

**Option B: Direct File Access**
- Open `frontend/index.html` directly in browser
- URL will be: `file:///path/to/frontend/index.html`
- ⚠️ Note: Some features may not work due to CORS restrictions with file:// protocol

**Option C: Using Python HTTP Server**
```bash
cd frontend
python -m http.server 8080
```
- Opens on: `http://localhost:8080`

### 4. Verify Setup

**Check Browser Console:**
- ✅ "Supabase config loaded from backend"
- ✅ "API Base URL: http://127.0.0.1:8000"
- ✅ "Environment: Local Development"
- ❌ No CORS errors

## Common Issues & Solutions

### Issue: CORS Error
```
Access to fetch at 'http://127.0.0.1:8000/api/config/supabase' from origin 'http://127.0.0.1:5500' 
has been blocked by CORS policy
```

**Solution:**
1. Check `.env` has `ENVIRONMENT=development`
2. Restart the backend server: `uvicorn api:app --reload`
3. Clear browser cache and reload
4. If using a different port, add it to `FRONTEND_ORIGIN` in `.env`

### Issue: Supabase Config Not Loading
```
❌ Failed to load Supabase config: TypeError: Failed to fetch
```

**Solution:**
1. Verify backend is running: `curl http://127.0.0.1:8000/api/health`
2. Check CORS is working: Look for `access-control-allow-origin` header
3. Ensure `supabase-config.js` is loaded before `app.js` in `index.html`

### Issue: Map Tiles Not Loading
```
Uncaught (in promise) TypeError: Failed to fetch (pmtiles.js)
```

**Solution:**
1. Verify `frontend/maptiles/` directory exists
2. Check PMTiles files are present (highways.pmtiles, metro.pmtiles, etc.)
3. Ensure backend is serving static files correctly

## Development Ports

The following ports are automatically allowed in development mode:

| Port | Common Use |
|------|------------|
| 5500 | VS Code Live Server |
| 8000 | Backend API / Python HTTP Server |
| 3000 | React/Node.js dev servers |

To add more ports, edit `api.py`:
```python
if os.getenv("ENVIRONMENT", "production") == "development":
    allowed_origins.extend([
        "http://localhost:YOUR_PORT",
        "http://127.0.0.1:YOUR_PORT"
    ])
```

## Environment Variables

### Required for Local Development
```env
# Set to development for local testing
ENVIRONMENT=development

# Supabase credentials
SUPABASE_URL=https://ihraowxbduhlichzszgk.supabase.co
SUPABASE_KEY=your_anon_key_here

# Google API keys
GOOGLE_PLACES_API_KEY=your_key_here
GOOGLE_MAPS_API_KEY=your_key_here

# CORS - Include your local ports
FRONTEND_ORIGIN=http://localhost:8000,http://127.0.0.1:5500
```

### Optional
```env
# Backend API key (for authenticated endpoints)
BACKEND_API_KEY=your_secure_key_here
```

## Testing Workflow

### 1. Test Backend API
```bash
# Health check
curl http://127.0.0.1:8000/api/health

# Supabase config
curl http://127.0.0.1:8000/api/config/supabase

# Test with CORS header
curl http://127.0.0.1:8000/api/config/supabase -H "Origin: http://127.0.0.1:5500"
```

### 2. Test Frontend
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for initialization messages
4. Test features:
   - Search for a location
   - Click location pins
   - Load amenities
   - View properties

### 3. Test CORS
1. Open Network tab in DevTools
2. Reload page
3. Check requests to `/api/config/supabase`
4. Verify response headers include:
   - `access-control-allow-origin: http://127.0.0.1:5500`
   - `access-control-allow-credentials: true`

## Hot Reload

### Backend (Automatic)
Using `--reload` flag, the server automatically restarts when you edit:
- `api.py`
- Any imported Python modules

### Frontend (Manual)
- Edit HTML/CSS/JS files
- Refresh browser (F5)
- Or use Live Server auto-reload

## Debugging Tips

### Enable Verbose Logging
In `api.py`, add at the top:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Backend Logs
Watch the terminal where `uvicorn` is running for:
- Request logs
- Error messages
- CORS decisions

### Check Frontend Console
Look for:
- API request/response logs
- JavaScript errors
- Network failures

### Test API Endpoints Directly
Use curl or Postman to test endpoints without frontend:
```bash
# Test amenities endpoint
curl "http://127.0.0.1:8000/api/v1/amenities/hospitals?lat=17.44&lng=78.38&limit=5"

# Test intelligence scores
curl "http://127.0.0.1:8000/api/v1/intelligence-scores/1"
```

## Production vs Development

### Development Mode
- CORS allows multiple localhost ports
- Detailed error messages
- Hot reload enabled
- No caching

### Production Mode
- CORS restricted to specific domains
- Generic error messages
- Optimized for performance
- Caching enabled

To switch to production mode:
```env
ENVIRONMENT=production
FRONTEND_ORIGIN=https://your-production-domain.com
```

## File Structure

```
project/
├── api.py                          # Backend API
├── .env                            # Environment variables (gitignored)
├── frontend/
│   ├── index.html                  # Main HTML
│   ├── app.js                      # Main JavaScript
│   ├── config.js                   # API URL configuration
│   ├── supabase-config.js          # Loads Supabase config from backend
│   ├── style.css                   # Styles
│   └── maptiles/                   # Map data files
├── ENABLE_RLS_SECURITY.sql         # Database security setup
├── SECURITY_FIXES_APPLIED.md       # Security documentation
├── DEPLOYMENT_CHECKLIST.md         # Deployment guide
└── LOCAL_DEVELOPMENT_SETUP.md      # This file
```

## Next Steps

1. ✅ Start backend server
2. ✅ Open frontend in browser
3. ✅ Verify no CORS errors
4. ✅ Test all features locally
5. 🚀 Deploy to production (see DEPLOYMENT_CHECKLIST.md)

## Need Help?

- **CORS Issues**: Check `ENVIRONMENT=development` in `.env`
- **API Errors**: Check backend terminal logs
- **Frontend Errors**: Check browser console
- **Security Setup**: See `SECURITY_FIXES_APPLIED.md`
- **Deployment**: See `DEPLOYMENT_CHECKLIST.md`
