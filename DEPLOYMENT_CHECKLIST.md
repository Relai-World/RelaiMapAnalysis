# Netlify Deployment Checklist ✅

## Before Deployment

- [ ] Verify `.env` is in `.gitignore` (already done ✅)
- [ ] Test API locally: `uvicorn api:app --reload`
- [ ] Test frontend locally: Open `frontend/index.html` in browser
- [ ] Verify all environment variables are documented
- [ ] Check that no sensitive data is hardcoded in files

## Git Setup

- [ ] Initialize git: `git init`
- [ ] Create repository on GitHub/GitLab/Bitbucket
- [ ] Add remote: `git remote add origin <your-repo-url>`
- [ ] Commit files: `git add . && git commit -m "Initial commit"`
- [ ] Push to remote: `git push -u origin main`

## Netlify Configuration

- [ ] Go to https://app.netlify.com/
- [ ] Click "Add new site" → "Import an existing project"
- [ ] Connect your Git provider
- [ ] Select your repository
- [ ] Netlify auto-detects `netlify.toml` ✅

## Environment Variables Setup

Add these in Netlify Dashboard → Site settings → Environment variables:

- [ ] `BACKEND_API_KEY`
- [ ] `GOOGLE_PLACES_API_KEY`
- [ ] `SUPABASE_URL`
- [ ] `SUPABASE_KEY`
- [ ] `DB_HOST`
- [ ] `DB_PORT`
- [ ] `DB_NAME`
- [ ] `DB_USER`
- [ ] `DB_PASSWORD`

## Deploy & Test

- [ ] Click "Deploy site"
- [ ] Wait for build to complete (2-5 minutes)
- [ ] Test homepage: `https://your-site.netlify.app/`
- [ ] Test API health: `https://your-site.netlify.app/api/`
- [ ] Test insights endpoint: `https://your-site.netlify.app/api/v1/insights`
- [ ] Test search: `https://your-site.netlify.app/api/v1/search?q=gachibowli`
- [ ] Test map functionality
- [ ] Test chatbot

## Monitoring Setup

- [ ] Set bandwidth alert at 80GB
- [ ] Set build minutes alert at 250 minutes
- [ ] Set function invocations alert at 100k requests
- [ ] Enable email notifications

## Optional Enhancements

- [ ] Add custom domain
- [ ] Enable Netlify Analytics
- [ ] Set up deploy previews for branches
- [ ] Configure build hooks for auto-deploy

## Troubleshooting

If something doesn't work:

1. Check Function logs: Netlify Dashboard → Functions → View logs
2. Check Build logs: Netlify Dashboard → Deploys → Build log
3. Verify environment variables are set correctly
4. Check browser console for frontend errors
5. Test API endpoints individually

## Cost Monitoring

Week 1: Check usage daily
- Bandwidth used: ___ GB / 100 GB
- Build minutes: ___ / 300 minutes
- Function calls: ___ / 125k

If approaching limits, consider:
- Optimizing images
- Caching strategies
- Moving API to separate service (Railway/Render)
