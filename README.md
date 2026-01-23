# West Hyderabad Intelligence

A comprehensive Real Estate Intelligence Dashboard for West Hyderabad.

## Hosting Architecture
- **Frontend**: Hosted on [GitHub Pages](https://pages.github.com/) (Static Site).
- **Backend**: Hosted on [Render](https://render.com/) (Python FastAPI Service).
- **Database**: PostgreSQL (Hosted on Render/Neon/Supabase).

## Features
- **Serverless Maps**: Uses PMTiles for high-performance vector layers (Schools, Metro, etc.).
- **Data Insights**: Real-time investment analytics served via API.
- **Reporting**: Automated PDF generation for location reports.

## Local Development (Separated Mode)

### 1. Backend (Port 8000)
```bash
pip install -r requirements.txt
uvicorn api:app --reload
```
*API will be available at `http://127.0.0.1:8000`.*

### 2. Frontend (Port 3000)
```bash
npx serve frontend
# OR
python -m http.server 3000 --directory frontend
```
*App will be available at `http://localhost:3000`.*

## Deployment Guide

### 1. Deploy Backend to Render
1. Create a **Web Service** on Render connected to this repo.
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

### 2. Deploy Frontend to GitHub Pages
1. Go to Repo Settings > Pages.
2. Select Source: `main` branch, folder `/frontend` (if possible) or root.
3. **Important**: Update `BACKEND_URL` in `app.js` if the auto-detection needs adjustment.
