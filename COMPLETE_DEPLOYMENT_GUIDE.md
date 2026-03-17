# Complete Deployment Guide

## The Problem
Netlify doesn't support Python serverless functions well on the free tier. 

## The Solution
Deploy frontend and backend separately:
- **Frontend**: Netlify (free, fast CDN)
- **Backend API**: Render (free, Python-friendly)

---

## Part 1: Deploy API on Render

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 2: Deploy on Render
1. Go to https://render.com/
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Select your repository
5. Render auto-detects `render.yaml` ✅
6. Click "Create Web Service"

### Step 3: Add Environment Variables
In Render Dashboard → Environment tab:

```
BACKEND_API_KEY=west-hyd-intel-secure-key-2026
GOOGLE_PLACES_API_KEY=AIzaSyDnREtiEfU6adEdXJvTbLtLcHe26kWvz-g
SUPABASE_URL=https://ihraowxbduhlichzszgk.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlocmFvd3hiZHVobGljaHpzemdrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk5MDU5OTEsImV4cCI6MjA2NTQ4MTk5MX0.9SGeXWpk4_OI2qMPyfCfVtUqar6q62-ZFifaA3lc3BE
DB_HOST=aws-0-ap-south-1.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.ihraowxbduhlichzszgk
DB_PASSWORD=Relai@World@123
```

### Step 4: Wait for Deployment
- Build takes 2-3 minutes
- Your API will be at: `https://west-hyderabad-api.onrender.com`
- Test it: `https://west-hyderabad-api.onrender.com/api/v1/insights`

---

## Part 2: Update Frontend for Production API

### Option A: Update config.js (Recommended)

Edit `frontend/config.js` and change the PRODUCTION_API_URL:

```javascript
const API_CONFIG = {
  PRODUCTION_API_URL: 'https://YOUR-RENDER-URL.onrender.com',  // ← Update this
  LOCAL_API_URL: 'http://127.0.0.1:8000'
};
```

### Option B: Update app.js directly

Find all instances of API URL detection in `frontend/app.js` and update them to use your Render URL.

---

## Part 3: Deploy Frontend on Netlify

Your frontend is already deployed! Just need to:

1. Update the API URL in `frontend/config.js`
2. Commit and push:
   ```bash
   git add frontend/config.js
   git commit -m "Update API URL to Render"
   git push origin main
   ```
3. Netlify will auto-deploy (takes 1 minute)

---

## Testing Your Deployment

### Test API (Render)
```bash
curl https://YOUR-RENDER-URL.onrender.com/
curl https://YOUR-RENDER-URL.onrender.com/api/v1/insights
```

### Test Frontend (Netlify)
1. Open: `https://grand-florentine-259a3a.netlify.app/`
2. Check browser console for API calls
3. Test map, search, and chatbot features

---

## Cost Breakdown

### Render (API)
- ✅ FREE: 750 hours/month (24/7 for 1 service)
- ⚠️ Spins down after 15 min inactivity (cold start ~30s)
- ✅ No bandwidth limits
- ✅ No request limits

### Netlify (Frontend)
- ✅ FREE: 100 GB bandwidth/month
- ✅ FREE: 300 build minutes/month
- ✅ No cold starts (always fast)

### Total Cost: $0/month 🎉

---

## Handling Cold Starts (Optional)

Render free tier spins down after 15 minutes of inactivity. First request takes ~30 seconds.

### Solution 1: Accept It
- Most users won't notice
- Subsequent requests are fast

### Solution 2: Keep-Alive Service
Use UptimeRobot (free) to ping your API every 5 minutes:
1. Go to https://uptimerobot.com/
2. Add monitor: `https://YOUR-RENDER-URL.onrender.com/`
3. Check interval: 5 minutes

---

## Troubleshooting

### API not responding
- Check Render logs: Dashboard → Logs tab
- Verify environment variables are set
- Check if service is running

### Frontend can't connect to API
- Check browser console for errors
- Verify API URL in `config.js` is correct
- Check CORS settings in `api.py`

### Build fails on Render
- Check build logs
- Verify `requirements.txt` has all dependencies
- Check Python version in `render.yaml`

---

## Alternative: All-in-One on Railway

If you prefer everything in one place:

1. Go to https://railway.app/
2. Deploy from GitHub
3. Railway handles both frontend and backend
4. $5 free credit/month
5. No cold starts

---

## Next Steps

1. ✅ Deploy API on Render
2. ✅ Get your Render URL
3. ✅ Update `frontend/config.js`
4. ✅ Push changes
5. ✅ Test everything
6. 🎉 You're live!

---

## Monitoring

### Week 1: Check Daily
- Render: Check if API is responding
- Netlify: Check bandwidth usage
- Test all features

### After Week 1: Check Weekly
- Monitor Render uptime
- Check Netlify bandwidth (should be <10 GB/month)
- Review error logs

---

## Upgrade Path (If Needed)

If you outgrow free tiers:

1. **Render Pro**: $7/month (no cold starts, better performance)
2. **Netlify Pro**: $19/month (more bandwidth, analytics)
3. **Railway**: Pay-as-you-go ($5 credit covers most small apps)

But honestly, free tier should work fine for your use case!
