# West Hyderabad Real Estate Intelligence - Deployment

## Quick Start (5 Minutes)

### 1. Run Deployment Script
```powershell
.\deploy.ps1
```

### 2. Create GitHub Repository
- Go to https://github.com/new
- Create a new repository (public or private)
- Copy the repository URL

### 3. Push Code
```bash
git remote add origin <your-repo-url>
git push -u origin main
```

### 4. Deploy on Netlify
- Go to https://app.netlify.com/
- Click "Add new site" → "Import an existing project"
- Select GitHub and your repository
- Netlify will auto-detect settings from `netlify.toml`

### 5. Add Environment Variables
In Netlify Dashboard → Site settings → Environment variables, copy all variables from your `.env` file:
- BACKEND_API_KEY
- GOOGLE_PLACES_API_KEY
- SUPABASE_URL
- SUPABASE_KEY
- DB_HOST
- DB_PORT
- DB_NAME
- DB_USER
- DB_PASSWORD

### 6. Deploy!
Click "Deploy site" and wait 2-5 minutes.

## What's Deployed?

- **Frontend**: Your HTML/CSS/JS from `frontend/` folder
- **API**: FastAPI backend as Netlify serverless functions
- **Database**: Supabase (already hosted)

## Your Site URLs

After deployment:
- **Frontend**: `https://your-site-name.netlify.app/`
- **API**: `https://your-site-name.netlify.app/api/`

## Free Tier Limits

- 100 GB bandwidth/month
- 300 build minutes/month
- 125k function requests/month

Set up usage alerts to avoid surprise charges!

## Need Help?

- See `NETLIFY_DEPLOYMENT_GUIDE.md` for detailed instructions
- See `DEPLOYMENT_CHECKLIST.md` for step-by-step checklist
- Check Netlify docs: https://docs.netlify.com/

## Alternative Deployment Options

If Netlify Functions are too expensive:

1. **Frontend on Netlify** (free) + **API on Railway** (free tier)
2. **Frontend on Netlify** (free) + **API on Render** (free tier)
3. **Everything on Vercel** (similar to Netlify)

## Project Structure

```
.
├── frontend/              # Static files (HTML, CSS, JS)
├── netlify/
│   └── functions/
│       └── api.py        # Serverless function wrapper
├── api.py                # Main FastAPI application
├── netlify.toml          # Netlify configuration
├── requirements.txt      # Python dependencies
├── runtime.txt           # Python version
└── .env                  # Environment variables (NOT committed)
```

## Support

Questions? Check the deployment guides or Netlify's support docs.
