@echo off
echo ========================================
echo UAE Legal ETL Pipeline - GitHub Setup
echo ========================================
echo.

echo This script will help you push this project to GitHub.
echo.
echo Prerequisites:
echo - Git must be installed
echo - You must have a GitHub account
echo.

pause

echo.
echo Step 1: Initializing Git repository...
git init
if errorlevel 1 (
    echo ERROR: Git initialization failed. Is Git installed?
    pause
    exit /b 1
)
echo ✓ Git repository initialized
echo.

echo Step 2: Adding all files...
git add .
if errorlevel 1 (
    echo ERROR: Failed to add files
    pause
    exit /b 1
)
echo ✓ Files added
echo.

echo Step 3: Creating initial commit...
git commit -m "Initial commit: UAE Legal Documents ETL Pipeline"
if errorlevel 1 (
    echo ERROR: Commit failed
    pause
    exit /b 1
)
echo ✓ Initial commit created
echo.

echo Step 4: Setting default branch to main...
git branch -M main
echo ✓ Branch set to main
echo.

echo ========================================
echo Next Steps:
echo ========================================
echo.
echo 1. Go to GitHub: https://github.com/new
echo 2. Create a new repository named: uae-legal-etl-pipeline
echo 3. DO NOT initialize with README, .gitignore, or license
echo 4. Copy your repository URL (it will look like):
echo    https://github.com/YOUR_USERNAME/uae-legal-etl-pipeline.git
echo.
echo 5. Come back here and press any key to continue...
echo.

pause

echo.
set /p REPO_URL="Enter your GitHub repository URL: "

echo.
echo Adding remote repository...
git remote add origin %REPO_URL%
if errorlevel 1 (
    echo ERROR: Failed to add remote. Check the URL.
    pause
    exit /b 1
)
echo ✓ Remote added
echo.

echo Pushing to GitHub...
git push -u origin main
if errorlevel 1 (
    echo.
    echo ERROR: Push failed. This might be because:
    echo - You need to authenticate with GitHub
    echo - The repository URL is incorrect
    echo - You don't have permission
    echo.
    echo Try running this command manually:
    echo git push -u origin main
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! 🎉
echo ========================================
echo.
echo Your project has been pushed to GitHub!
echo.
echo View it at: %REPO_URL%
echo.
echo Next steps:
echo - Add repository description on GitHub
echo - Add topics: python, etl, legal-tech, nlp
echo - Share with your team
echo.

pause
