# PowerShell deployment script for Windows

Write-Host "🚀 Preparing for Netlify Deployment..." -ForegroundColor Green

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "📦 Initializing git repository..." -ForegroundColor Yellow
    git init
    git add .
    git commit -m "Initial commit for Netlify deployment"
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
} else {
    Write-Host "✅ Git repository already exists" -ForegroundColor Green
}

# Check if .env is in .gitignore
$gitignoreContent = Get-Content .gitignore -Raw
if ($gitignoreContent -notmatch "^\.env$") {
    Write-Host "⚠️  Adding .env to .gitignore..." -ForegroundColor Yellow
    Add-Content .gitignore "`n.env"
}

Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Create a repository on GitHub/GitLab/Bitbucket"
Write-Host "2. Run: git remote add origin <your-repo-url>"
Write-Host "3. Run: git push -u origin main"
Write-Host "4. Go to https://app.netlify.com/"
Write-Host "5. Click 'Add new site' → 'Import an existing project'"
Write-Host "6. Select your repository"
Write-Host "7. Add environment variables from .env file"
Write-Host "8. Deploy!"
Write-Host ""
Write-Host "📖 See NETLIFY_DEPLOYMENT_GUIDE.md for detailed instructions" -ForegroundColor Yellow
