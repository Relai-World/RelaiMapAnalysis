# Deploy API on Render (Free)

Render is better for Python backends and has a generous free tier.

## Step 1: Create Render Account
- Go to https://render.com/
- Sign up with GitHub (easiest)

## Step 2: Deploy API

1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Render will auto-detect `render.yaml`
4. Or manually configure:
   - **Name**: west-hyderabad-api
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free

## Step 3: Add Environment Variables

In Render Dashboard → Environment, add:

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

## Step 4: Deploy

Click "Create Web Service" - Render will build and deploy your API.

Your API will be at: `https://west-hyderabad-api.onrender.com`

## Step 5: Update Frontend

You need to update your frontend to point to the Render API URL.

### Option A: Use Environment Variable in Netlify

Add this environment variable in Netlify:
```
VITE_API_URL=https://west-hyderabad-api.onrender.com
```

### Option B: Update app.js directly

Change the API URL detection in `frontend/app.js` to use your Render URL.

## Free Tier Limits (Render)

- 750 hours/month (enough for 1 service running 24/7)
- Spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds (cold start)
- No bandwidth limits
- No request limits

## Keeping API Awake (Optional)

Free tier spins down after inactivity. To keep it awake:

1. Use a service like UptimeRobot (free) to ping your API every 5 minutes
2. Or accept the cold starts (first request is slow, then fast)

## Alternative: Railway

If Render doesn't work, try Railway:
- Go to https://railway.app/
- Similar setup, also has generous free tier
- $5 free credit per month
- No cold starts

## Cost Comparison

| Service | Free Tier | Best For |
|---------|-----------|----------|
| Render | 750 hrs/month | Python APIs, no cold start concerns |
| Railway | $5 credit/month | Always-on services |
| Fly.io | 3 VMs free | Global deployment |
| Netlify Functions | 125k requests | Simple serverless |

For your use case: **Render is the best choice** for the API.
