# Deployment Checklist - Security Fixes

## ✅ Pre-Deployment (Completed)

- [x] Remove hardcoded Supabase credentials from frontend
- [x] Configure CORS to restrict origins
- [x] Remove dead code from api.py
- [x] Eliminate Haversine formula duplication
- [x] Create utility functions for shared code
- [x] Add environment variables for configuration
- [x] Create Supabase config loader for frontend
- [x] Add new API endpoint for config delivery
- [x] Update .env with new variables
- [x] Verify .env is in .gitignore
- [x] Run security verification tests (all passed)

## 📋 Local Testing

### 1. Start Backend Server
```bash
# Activate virtual environment (if using)
# source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows

# Start the API server
uvicorn api:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### 2. Test in Browser
Open: `http://localhost:8000`

**Check Browser Console:**
- [ ] ✅ "Supabase config loaded from backend"
- [ ] ✅ "API Base URL: http://127.0.0.1:8000"
- [ ] ✅ "Environment: Local Development"
- [ ] ❌ No CORS errors
- [ ] ❌ No credential errors

**Test Features:**
- [ ] Search for a location (e.g., "Gachibowli")
- [ ] Click on a location pin
- [ ] View intelligence card
- [ ] Load amenities (hospitals, schools, etc.)
- [ ] View properties list
- [ ] Check future developments

### 3. Test API Endpoints
```bash
# Test health check
curl http://localhost:8000/api/health

# Test Supabase config endpoint
curl http://localhost:8000/api/config/supabase

# Expected: Should return URL and key
```

## 🚀 GitHub Deployment

### 1. Commit Changes
```bash
# Check what's changed
git status

# Add all changes
git add .

# Commit with descriptive message
git commit -m "Security fixes: Remove hardcoded credentials, restrict CORS, clean dead code"

# Push to GitHub
git push origin main
```

### 2. Verify on GitHub
- [ ] Check that `.env` is NOT in the repository
- [ ] Verify `frontend/app.js` has no hardcoded credentials
- [ ] Check `api.py` has CORS restrictions
- [ ] Confirm all new files are present:
  - `frontend/supabase-config.js`
  - `ENABLE_RLS_SECURITY.sql`
  - `SECURITY_FIXES_APPLIED.md`
  - `DEPLOYMENT_CHECKLIST.md`

## 🌐 Render Deployment

### 1. Environment Variables
Go to Render Dashboard → Your Service → Environment

**Add/Update these variables:**
```
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
FRONTEND_ORIGIN=https://your-app.onrender.com
ENVIRONMENT=production
BACKEND_API_KEY=your_secure_backend_key_here
```

**Important Notes:**
- Replace URLs with your actual Render URL
- If using custom domain, add it to FRONTEND_ORIGIN
- For multiple domains: `https://domain1.com,https://domain2.com`

### 2. Deploy
- [ ] Push to GitHub (Render auto-deploys)
- [ ] Or click "Manual Deploy" in Render dashboard
- [ ] Wait for deployment to complete
- [ ] Check deployment logs for errors

### 3. Test Production
Open your Render URL: `https://your-app.onrender.com`

**Check Browser Console:**
- [ ] ✅ "Supabase config loaded from backend"
- [ ] ✅ "API Base URL: https://your-app.onrender.com"
- [ ] ✅ "Environment: Production"
- [ ] ❌ No CORS errors
- [ ] ❌ No 403/401 errors

**Test All Features:**
- [ ] Location search works
- [ ] Map loads correctly
- [ ] Intelligence cards display
- [ ] Amenities load
- [ ] Properties list works
- [ ] Future developments modal
- [ ] Commute calculator

## 🗄️ Supabase RLS Setup

### 1. Open Supabase Dashboard
Go to: https://supabase.com/dashboard

### 2. Navigate to SQL Editor
Dashboard → Your Project → SQL Editor

### 3. Run RLS Script
- [ ] Copy contents of `ENABLE_RLS_SECURITY.sql`
- [ ] Paste into SQL Editor
- [ ] Click "Run"
- [ ] Verify output shows `rls_enabled = true` for all tables

### 4. Verify RLS is Working
```sql
-- Run this query to check RLS status
SELECT 
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('locations', 'properties', 'future_development_scrap', 'news_balanced_corpus_1')
ORDER BY tablename;
```

Expected output:
```
| tablename                    | rls_enabled |
|------------------------------|-------------|
| future_development_scrap     | true        |
| locations                    | true        |
| news_balanced_corpus_1       | true        |
| properties                   | true        |
```

### 5. Test Read Access
- [ ] Open your app
- [ ] Search for a location
- [ ] Verify data loads correctly
- [ ] Check browser console for no errors

## 🌍 Custom Domain (Optional)

### 1. Configure Domain in Render
- [ ] Go to Render Dashboard → Settings → Custom Domain
- [ ] Add your domain
- [ ] Update DNS records as instructed

### 2. Update Environment Variables
- [ ] Add custom domain to `FRONTEND_ORIGIN`
- [ ] Example: `FRONTEND_ORIGIN=https://yourdomain.com,https://relai-map-analysis.onrender.com`

### 3. Test Custom Domain
- [ ] Open your custom domain
- [ ] Test all features
- [ ] Verify CORS works
- [ ] Check SSL certificate is active

## 🔍 Post-Deployment Verification

### Security Checks
- [ ] No hardcoded credentials in GitHub repository
- [ ] `.env` file is gitignored
- [ ] CORS only allows specified domains
- [ ] RLS enabled on all Supabase tables
- [ ] API endpoints require proper authentication

### Functionality Checks
- [ ] All pages load without errors
- [ ] Location search works
- [ ] Map layers toggle correctly
- [ ] Intelligence cards display data
- [ ] Amenities load from Google Places API
- [ ] Properties list populates
- [ ] Future developments modal works
- [ ] Commute calculator functions

### Performance Checks
- [ ] Page loads in < 3 seconds
- [ ] Map tiles load smoothly
- [ ] API responses are fast
- [ ] No console errors or warnings

## 📊 Monitoring

### Set Up Monitoring (Recommended)
1. **UptimeRobot** - Monitor `/api/health` endpoint
2. **Sentry** - Track JavaScript errors
3. **Render Logs** - Monitor API errors
4. **Supabase Logs** - Track database queries

### What to Monitor
- [ ] API uptime (should be 99%+)
- [ ] Response times (< 500ms)
- [ ] Error rates (< 1%)
- [ ] CORS errors (should be 0)
- [ ] Authentication failures (should be 0)

## 🆘 Troubleshooting

### Issue: "Supabase config not loaded"
**Solution:**
1. Check `/api/config/supabase` endpoint is accessible
2. Verify SUPABASE_URL and SUPABASE_KEY in environment variables
3. Check CORS allows your domain

### Issue: CORS errors
**Solution:**
1. Verify FRONTEND_ORIGIN includes your domain
2. Check ENVIRONMENT variable is set correctly
3. Restart Render service after env changes

### Issue: RLS blocking queries
**Solution:**
1. Verify RLS policies are created (run ENABLE_RLS_SECURITY.sql)
2. Check you're using anon key (not service_role key) in frontend
3. Verify policies allow SELECT for anon role

### Issue: Features not working
**Solution:**
1. Check browser console for errors
2. Check Render logs for API errors
3. Verify all environment variables are set
4. Test API endpoints directly with curl

## ✅ Final Checklist

- [ ] All security fixes applied
- [ ] Local testing completed successfully
- [ ] Changes pushed to GitHub
- [ ] Render deployment successful
- [ ] Environment variables configured
- [ ] RLS enabled in Supabase
- [ ] Production testing completed
- [ ] Custom domain configured (if applicable)
- [ ] Monitoring set up
- [ ] Documentation updated

## 🎉 Success Criteria

Your deployment is successful when:
1. ✅ No hardcoded credentials in code
2. ✅ CORS properly restricted
3. ✅ All features work in production
4. ✅ No console errors
5. ✅ RLS enabled and working
6. ✅ Performance is acceptable
7. ✅ Monitoring is active

---

**Need Help?**
- Check `SECURITY_FIXES_APPLIED.md` for detailed explanations
- Review Render logs for API errors
- Check Supabase logs for database issues
- Test locally first before deploying to production
