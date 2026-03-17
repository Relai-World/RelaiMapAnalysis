# PowerShell script to prepare for Render deployment

Write-Host "🚀 Setting up for Render + Netlify Deployment" -ForegroundColor Green
Write-Host ""

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "📦 Initializing git..." -ForegroundColor Yellow
    git init
    git add .
    git commit -m "Initial commit - ready for Render + Netlify"
} else {
    Write-Host "✅ Git repository exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "📋 Deployment Checklist:" -ForegroundColor Cyan
Write-Host ""
Write-Host "STEP 1: Deploy API on Render" -ForegroundColor Yellow
Write-Host "  1. Go to https://render.com/"
Write-Host "  2. Sign up with GitHub"
Write-Host "  3. Click 'New +' → 'Web Service'"
Write-Host "  4. Select your repository"
Write-Host "  5. Render will auto-detect render.yaml"
Write-Host "  6. Add environment variables from .env file"
Write-Host "  7. Click 'Create Web Service'"
Write-Host ""

Write-Host "STEP 2: Update Frontend" -ForegroundColor Yellow
Write-Host "  1. Copy your Render URL (e.g., https://west-hyderabad-api.onrender.com)"
Write-Host "  2. Edit frontend/config.js"
Write-Host "  3. Update PRODUCTION_API_URL with your Render URL"
Write-Host "  4. Commit and push changes"
Write-Host ""

Write-Host "STEP 3: Netlify Auto-Deploys" -ForegroundColor Yellow
Write-Host "  Your frontend on Netlify will auto-update!"
Write-Host ""

Write-Host "📖 See COMPLETE_DEPLOYMENT_GUIDE.md for detailed instructions" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Pro Tip: Render free tier spins down after 15 min inactivity." -ForegroundColor Cyan
Write-Host "   First request takes ~30s, then it's fast!" -ForegroundColor Cyan
