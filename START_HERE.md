# 🚀 START HERE - Deployment Guide

## What Happened?

Your frontend is deployed on Netlify ✅
But the API (backend) needs to be deployed separately.

## Why?

Netlify doesn't support Python serverless functions well on free tier.
Solution: Deploy API on Render (free, Python-friendly).

---

## 🎯 3-Step Deployment

### Step 1: Deploy API on Render (5 min)

1. Go to **https://render.com/**
2. Click **"Sign up with GitHub"**
3. Click **"New +"** → **"Web Service"**
4. Select your repository
5. Render auto-detects `render.yaml` ✅
6. Click **"Create Web Service"**
7. Go to **"Environment"** tab
8. Add all variables from your `.env` file:
   - BACKEND_API_KEY
   - GOOGLE_PLACES_API_KEY
   - SUPABASE_URL
   - SUPABASE_KEY
   - DB_HOST
   - DB_PORT
   - DB_NAME
   - DB_USER
   - DB_PASSWORD
9. Wait 2-3 minutes for deployment

### Step 2: Update Frontend (2 min)

1. Copy your Render URL (e.g., `https://west-hyderabad-api.onrender.com`)
2. Open `frontend/config.js`
3. Update this line:
   ```javascript
   PRODUCTION_API_URL: 'https://YOUR-RENDER-URL.onrender.com'
   ```
4. Save the file

### Step 3: Push Changes (1 min)

```bash
git add frontend/config.js
git commit -m "Connect to Render API"
git push origin main
```

Netlify will auto-deploy your updated frontend!

---

## ✅ Testing

### Test API (Render)
Open in browser:
- `https://YOUR-RENDER-URL.onrender.com/`
- `https://YOUR-RENDER-URL.onrender.com/api/v1/insights`

### Test Frontend (Netlify)
Open: `https://grand-florentine-259a3a.netlify.app/`
- Check browser console (F12) for API calls
- Test map functionality
- Test search
- Test chatbot

---

## 📚 Need More Help?

- **Quick Overview**: `DEPLOYMENT_SUMMARY.md`
- **Detailed Guide**: `COMPLETE_DEPLOYMENT_GUIDE.md`
- **Render Specific**: `RENDER_DEPLOYMENT_GUIDE.md`
- **Troubleshooting**: See any of the above guides

---

## 💰 Cost

**Total: $0/month** 🎉

- Netlify: 100 GB bandwidth/month (free)
- Render: 750 hours/month (free)
- Supabase: 500 MB database (free)

---

## ⚠️ Important Notes

1. **Cold Starts**: Render free tier spins down after 15 min inactivity
   - First request takes ~30 seconds
   - Subsequent requests are fast
   - This is normal and acceptable

2. **Environment Variables**: Must be added in Render dashboard
   - Don't commit `.env` to GitHub
   - Add them manually in Render

3. **CORS**: Already configured in `api.py` ✅

---

## 🎉 You're Almost There!

Just deploy the API on Render and update the frontend config.
Total time: ~8 minutes.

Let's go! 🚀
