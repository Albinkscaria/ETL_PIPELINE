#!/bin/bash

echo "========================================"
echo "UAE Legal ETL Pipeline - GitHub Setup"
echo "========================================"
echo ""

echo "This script will help you push this project to GitHub."
echo ""
echo "Prerequisites:"
echo "- Git must be installed"
echo "- You must have a GitHub account"
echo ""

read -p "Press Enter to continue..."

echo ""
echo "Step 1: Initializing Git repository..."
git init
if [ $? -ne 0 ]; then
    echo "ERROR: Git initialization failed. Is Git installed?"
    exit 1
fi
echo "✓ Git repository initialized"
echo ""

echo "Step 2: Adding all files..."
git add .
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to add files"
    exit 1
fi
echo "✓ Files added"
echo ""

echo "Step 3: Creating initial commit..."
git commit -m "Initial commit: UAE Legal Documents ETL Pipeline"
if [ $? -ne 0 ]; then
    echo "ERROR: Commit failed"
    exit 1
fi
echo "✓ Initial commit created"
echo ""

echo "Step 4: Setting default branch to main..."
git branch -M main
echo "✓ Branch set to main"
echo ""

echo "========================================"
echo "Next Steps:"
echo "========================================"
echo ""
echo "1. Go to GitHub: https://github.com/new"
echo "2. Create a new repository named: uae-legal-etl-pipeline"
echo "3. DO NOT initialize with README, .gitignore, or license"
echo "4. Copy your repository URL (it will look like):"
echo "   https://github.com/YOUR_USERNAME/uae-legal-etl-pipeline.git"
echo ""
echo "5. Come back here and press Enter to continue..."
echo ""

read -p "Press Enter when ready..."

echo ""
read -p "Enter your GitHub repository URL: " REPO_URL

echo ""
echo "Adding remote repository..."
git remote add origin "$REPO_URL"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to add remote. Check the URL."
    exit 1
fi
echo "✓ Remote added"
echo ""

echo "Pushing to GitHub..."
git push -u origin main
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Push failed. This might be because:"
    echo "- You need to authenticate with GitHub"
    echo "- The repository URL is incorrect"
    echo "- You don't have permission"
    echo ""
    echo "Try running this command manually:"
    echo "git push -u origin main"
    echo ""
    exit 1
fi

echo ""
echo "========================================"
echo "SUCCESS! 🎉"
echo "========================================"
echo ""
echo "Your project has been pushed to GitHub!"
echo ""
echo "View it at: $REPO_URL"
echo ""
echo "Next steps:"
echo "- Add repository description on GitHub"
echo "- Add topics: python, etl, legal-tech, nlp"
echo "- Share with your team"
echo ""
