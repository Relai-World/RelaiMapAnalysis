# 🚀 Netlify Deployment - Quick Start Script

## Prerequisites
- Git installed
- Node.js installed (for Netlify CLI)
- GitHub account
- Render/Railway account (for backend)

---

## STEP 1: Initialize Git Repository

```bash
cd "c:\Users\gudde\OneDrive\Desktop\Final"
git init
git add .
git commit -m "Ready for Netlify deployment - Location updates complete"
```

---

## STEP 2: Create GitHub Repository

### Option A: Via GitHub Website
1. Go to https://github.com/new
2. Create new repository
3. Name: `hyderabad-real-estate-map` (or your choice)
4. Make it **Public** or **Private**
5. Click "Create repository"
6. Copy the repository URL

### Option B: Via GitHub CLI (if installed)
```bash
gh repo create hyderabad-real-estate-map --public --source=. --remote=origin --push
```

---

## STEP 3: Push to GitHub

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

**Replace YOUR_USERNAME and YOUR_REPO with actual values!**

---

## STEP 4: Install Netlify CLI

```bash
npm install -g netlify-cli
```

Verify installation:
```bash
netlify --version
```

---

## STEP 5: Login to Netlify

```bash
netlify login
```

This opens browser for authentication.

---

## STEP 6: Deploy to Netlify

### First Time Setup:
```bash
netlify init
```

Select:
- "Create & configure a new site"
- Choose your team (or personal account)
- Site name: (leave blank for auto-generated)

### Deploy:
```bash
netlify deploy --prod --dir=frontend
```

Netlify will:
1. Build your frontend
2. Deploy to global CDN
3. Give you a URL like: `https://your-site.netlify.app`

---

## STEP 7: Set Up Backend API on Render

### 7.1: Create Render Account
1. Go to https://render.com
2. Sign up with GitHub
3. Complete profile

### 7.2: Create Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:

**Basic Settings:**
- Name: `hyderabad-api`
- Region: Choose closest to your users
- Branch: `main`

**Build Settings:**
- Runtime: `Python 3`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn api:app --host 0.0.0.0 --port $PORT`

**Instance Type:**
- Select "Free" tier

### 7.3: Add Environment Variables

In Render dashboard, go to Environment tab and add:

```env
DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=post@123
DB_NAME=real_estate_intelligence
DB_PORT=5432
BHUBHARATI_USERNAME=7981247396
BHUBHARATI_PASSWORD=H@rjeet123
```

⚠️ **Important**: For production, update DB credentials to cloud database!

### 7.4: Deploy Backend
Click "Create Web Service"
- Build takes ~5 minutes
- You'll get URL: `https://hyderabad-api-xxxx.onrender.com`

---

## STEP 8: Update Netlify Configuration

Edit `netlify.toml` and replace the API URL:

**Change this line:**
```toml
to = "https://west-hyderabad-intelliweb.onrender.com/api/:splat"
```

**To your new Render URL:**
```toml
to = "https://YOUR-RENDER-API.onrender.com/api/:splat"
```

Commit and push:
```bash
git add netlify.toml
git commit -m "Update API endpoint to production"
git push origin main
```

---

## STEP 9: Test Your Deployment

### 9.1: Test Frontend
Open your Netlify URL in browser:
```
https://your-site.netlify.app
```

Check:
- ✅ Map loads
- ✅ Location markers visible
- ✅ Clicking locations shows details
- ✅ Images display correctly
- ✅ Search works

### 9.2: Test API
Test your Render API directly:
```
https://YOUR-RENDER-API.onrender.com/api/v1/insights
```

Should return JSON with location data.

### 9.3: Test Integration
On Netlify frontend, open browser DevTools (F12) → Network tab
- Click on a location
- Check API calls succeed (status 200)
- No CORS errors

---

## STEP 10: Optional - Custom Domain

### On Netlify:
1. Go to Site Settings → Domain Management
2. "Add custom domain"
3. Enter: `yourdomain.com`
4. Follow DNS instructions

### On Render:
1. Dashboard → Service → Settings
2. "Custom Domain"
3. Add same domain
4. Update DNS records

---

## 🔧 TROUBLESHOOTING

### Issue: Build fails on Netlify
**Solution**: Ensure `frontend/` directory exists
```bash
ls frontend
# Should show index.html, app.js, etc.
```

### Issue: API returns 500 error
**Solution**: Check Render logs
- Go to Render Dashboard → Your Service → Logs
- Look for database connection errors
- Verify environment variables

### Issue: CORS errors
**Solution**: Update `api.py` CORS settings
```python
allow_origins=[
    "https://your-site.netlify.app",
    "http://localhost:8000"
]
```

### Issue: Database connection timeout
**Solution**: Migrate to cloud database
- Use Neon.tech or Supabase (free tiers)
- Update Render environment variables
- See README_NETLIFY.md for detailed instructions

---

## 📊 DEPLOYMENT VERIFICATION CHECKLIST

After completing all steps, verify:

### Frontend (Netlify)
- [ ] Site accessible via Netlify URL
- [ ] Homepage loads without errors
- [ ] Map displays correctly
- [ ] All 346 location markers visible
- [ ] Clicking locations shows details
- [ ] Location images load
- [ ] Property listings work
- [ ] Amenities display correctly
- [ ] Search functionality works
- [ ] Mobile responsive

### Backend (Render)
- [ ] API accessible via Render URL
- [ ] `/api/v1/insights` returns data
- [ ] `/api/v1/properties?area=X` works
- [ ] Database connected
- [ ] No errors in Render logs
- [ ] Response time < 2 seconds

### Integration
- [ ] Frontend successfully calls backend API
- [ ] No CORS errors in console
- [ ] Data displays correctly
- [ ] All features working

---

## 💰 COST TRACKER

### Current Setup (Free Tier)
```
Netlify Frontend:     $0/month  ✅
Render Backend:       $0/month  ✅
Local Database:       $0/month  ✅
Total:                $0/month  ✅
```

### Production Upgrade Options
```
Render Backend Pro:   $7/month  (no sleep)
Neon Database Pro:    $0/month  (free tier sufficient)
Netlify Pro:          $0/month  (free tier sufficient)
Total:                $7/month  (optional)
```

---

## 🎯 ALTERNATIVE: Railway.app

If you prefer Railway over Render:

### Setup Railway:
1. Go to https://railway.app
2. Sign up with GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Add PostgreSQL plugin
6. Set environment variables
7. Deploy

Railway has better free tier than Render!

---

## 🆘 GETTING HELP

### Resources
- Netlify Docs: https://docs.netlify.com
- Render Docs: https://render.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com

### Communities
- Netlify Discord
- Render Community Forum
- Stack Overflow (tag: netlify, fastapi)

---

## ✅ POST-DEPLOYMENT TASKS

After successful deployment:

### 1. Monitor Performance
- Netlify Analytics (built-in)
- Google Analytics (add tracking code)
- Sentry for error tracking

### 2. Set Up Monitoring
- Uptime monitoring: https://uptimerobot.com
- Performance: https://web.dev/measure
- SEO: https://search.google.com/search-console

### 3. Backup Strategy
- Database: Daily backups
- Code: Regular git commits
- Assets: Cloud storage (Cloudinary/S3)

### 4. Security
- Enable HTTPS (automatic on Netlify)
- Secure API keys (use environment variables)
- Rate limiting on API endpoints

---

## 🎉 SUCCESS!

Once everything is deployed and tested:

✅ Share your Netlify URL
✅ Share your Render API URL
✅ Document the setup for your team
✅ Celebrate! 🎊

---

**Quick Commands Reference:**

```bash
# Deploy to Netlify
netlify deploy --prod --dir=frontend

# Check deployment status
netlify status

# Open site in browser
netlify open

# View logs
netlify logs

# Rollback to previous version
netlify rollback
```

---

**Good luck with your deployment!** 🚀

If you encounter any issues, refer to `README_NETLIFY.md` for detailed troubleshooting.
