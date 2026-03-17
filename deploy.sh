#!/bin/bash

echo "🚀 Preparing for Netlify Deployment..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit for Netlify deployment"
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Check if .env is in .gitignore
if ! grep -q "^\.env$" .gitignore; then
    echo "⚠️  Adding .env to .gitignore..."
    echo ".env" >> .gitignore
fi

echo ""
echo "📋 Next Steps:"
echo "1. Create a repository on GitHub/GitLab/Bitbucket"
echo "2. Run: git remote add origin <your-repo-url>"
echo "3. Run: git push -u origin main"
echo "4. Go to https://app.netlify.com/"
echo "5. Click 'Add new site' → 'Import an existing project'"
echo "6. Select your repository"
echo "7. Add environment variables from .env file"
echo "8. Deploy!"
echo ""
echo "📖 See NETLIFY_DEPLOYMENT_GUIDE.md for detailed instructions"
