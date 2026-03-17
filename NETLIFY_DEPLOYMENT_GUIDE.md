# Netlify Deployment Guide

## Prerequisites
- Netlify account (free tier works)
- Git repository (GitHub, GitLab, or Bitbucket)

## Step 1: Push to Git Repository

```bash
git init
git add .
git commit -m "Initial commit for Netlify deployment"
git remote add origin <your-repo-url>
git push -u origin main
```

## Step 2: Connect to Netlify

1. Go to https://app.netlify.com/
2. Click "Add new site" → "Import an existing project"
3. Choose your Git provider and select your repository
4. Netlify will auto-detect the `netlify.toml` configuration

## Step 3: Configure Environment Variables

In Netlify Dashboard → Site settings → Environment variables, add:

```
BACKEND_API_KEY=west-hyd-intel-secure-key-2026
GOOGLE_PLACES_API_KEY=AIzaSyDnREtiEfU6adEdXJvTbLtLcHe26kWvz-g
SUPABASE_URL=https://ihraowxbduhlichzszgk.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlocmFvd3hiZHVobGljaHpzemdrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk5MDU5OTEsImV4cCI6MjA2NTQ4MTk5MX0.9SGeXWpk4_OI2qMPyfCfVtUqar6q62-ZFifaA3lc3BE
DB_HOST=aws-0-ap-south-1.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.ihraowxbduhlichzszgk
DB_PASSWORD=Relai%40World%40123
```

## Step 4: Deploy

Click "Deploy site" - Netlify will:
- Install Python dependencies from `requirements.txt`
- Deploy frontend files from `frontend/` folder
- Create serverless functions from `netlify/functions/`

## Step 5: Test Your Deployment

Once deployed, your site will be at: `https://your-site-name.netlify.app`

Test these endpoints:
- Frontend: `https://your-site-name.netlify.app/`
- API Health: `https://your-site-name.netlify.app/api/`
- Insights: `https://your-site-name.netlify.app/api/v1/insights`

## Monitoring Usage

1. Go to Netlify Dashboard → Usage
2. Set up email alerts for:
   - Bandwidth (warn at 80GB)
   - Build minutes (warn at 250 minutes)
   - Function invocations (warn at 100k)

## Custom Domain (Optional)

1. Go to Domain settings
2. Add your custom domain
3. Netlify provides free SSL certificates

## Troubleshooting

### API not working
- Check Environment Variables are set correctly
- Check Function logs in Netlify Dashboard → Functions

### Build fails
- Check build logs in Netlify Dashboard → Deploys
- Verify `requirements.txt` has all dependencies

### High bandwidth usage
- Optimize images in `frontend/images/`
- Consider using a CDN for map tiles
- Enable Netlify's asset optimization

## Cost Optimization Tips

1. **Reduce bandwidth**: Compress images, use WebP format
2. **Cache static assets**: Already configured in `netlify.toml`
3. **Monitor function calls**: Check which endpoints are called most
4. **Use Supabase Edge Functions**: For heavy database operations

## Alternative: Deploy API Separately

If Netlify Functions are too expensive, consider:
- **Railway**: Free tier, easy Python deployment
- **Render**: Free tier with 750 hours/month
- **Fly.io**: Free tier with 3 shared VMs

Then update `frontend/app.js` to point to your separate API URL.
