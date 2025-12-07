# GitHub Setup Guide

## Step-by-Step Instructions to Push This Project to GitHub

### Prerequisites
- Git installed on your system
- GitHub account created
- GitHub repository created (can be done in step 2)

---

## Option 1: Using GitHub Desktop (Easiest)

### Step 1: Install GitHub Desktop
1. Download from: https://desktop.github.com/
2. Install and sign in with your GitHub account

### Step 2: Create Repository
1. Open GitHub Desktop
2. Click "File" → "Add Local Repository"
3. Browse to this project folder
4. Click "Create Repository" if prompted
5. Click "Publish Repository"
6. Choose repository name: `uae-legal-etl-pipeline`
7. Add description: "Automated extraction of citations and definitions from UAE legal documents"
8. Uncheck "Keep this code private" (or keep checked if you want it private)
9. Click "Publish Repository"

### Step 3: Done!
Your project is now on GitHub!

---

## Option 2: Using Command Line (Git)

### Step 1: Initialize Git Repository
Open terminal/command prompt in this project folder and run:

```bash
# Initialize git repository
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit: UAE Legal Documents ETL Pipeline"
```

### Step 2: Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `uae-legal-etl-pipeline`
3. Description: "Automated extraction of citations and definitions from UAE legal documents"
4. Choose Public or Private
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

### Step 3: Connect and Push
GitHub will show you commands. Use these:

```bash
# Add remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/uae-legal-etl-pipeline.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

### Step 4: Verify
Go to your GitHub repository URL to see your project!

---

## Option 3: Using VS Code (If you have VS Code)

### Step 1: Open Source Control
1. Open this project folder in VS Code
2. Click the Source Control icon (left sidebar)
3. Click "Initialize Repository"

### Step 2: Commit Changes
1. Stage all files (click + next to "Changes")
2. Enter commit message: "Initial commit: UAE Legal Documents ETL Pipeline"
3. Click the checkmark to commit

### Step 3: Publish to GitHub
1. Click "Publish to GitHub" button
2. Choose repository name: `uae-legal-etl-pipeline`
3. Choose Public or Private
4. Click "Publish"

### Step 4: Done!
VS Code will push everything to GitHub automatically.

---

## Important Notes

### Files That Will Be Pushed
✅ All Python source code
✅ Documentation (README, INSTALLATION, etc.)
✅ Configuration files (config.json, requirements.txt)
✅ Docker files
✅ Tests folder
✅ Empty Data/ and reference/ folders (for structure)

### Files That Will NOT Be Pushed (in .gitignore)
❌ .env file (contains API keys - NEVER push this!)
❌ venv/ folder (virtual environment)
❌ __pycache__/ folders
❌ extracted_data.json (output file)
❌ *.log files
❌ PDF files in Data/ folder (too large)

### Security Checklist
Before pushing, ensure:
- [ ] .env file is in .gitignore
- [ ] No API keys in code
- [ ] No sensitive data in config files
- [ ] No personal information in PDFs

---

## After Pushing to GitHub

### 1. Add Repository Description
On GitHub repository page:
- Click "About" (gear icon)
- Add description: "Automated extraction of citations and definitions from UAE legal documents"
- Add topics: `python`, `etl`, `legal-tech`, `nlp`, `document-processing`, `uae`, `pdf-extraction`
- Add website (if you have one)

### 2. Enable GitHub Pages (Optional)
To host documentation:
1. Go to Settings → Pages
2. Source: Deploy from branch
3. Branch: main, folder: / (root)
4. Save

### 3. Add Badges to README (Optional)
Add these to the top of README.md:

```markdown
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production-brightgreen.svg)
```

### 4. Create Releases
When you have stable versions:
1. Go to "Releases" → "Create a new release"
2. Tag: v1.0.0
3. Title: "Initial Release"
4. Description: List features and changes
5. Publish release

---

## Updating Your Repository Later

When you make changes:

```bash
# Stage changes
git add .

# Commit with message
git commit -m "Description of changes"

# Push to GitHub
git push
```

Or use GitHub Desktop/VS Code to commit and push visually.

---

## Troubleshooting

### "Permission denied" error
- Make sure you're logged into GitHub
- Use HTTPS URL, not SSH (unless you have SSH keys set up)
- Try: `git remote set-url origin https://github.com/YOUR_USERNAME/uae-legal-etl-pipeline.git`

### "Repository not found" error
- Check the repository URL is correct
- Make sure the repository exists on GitHub
- Verify you have access to the repository

### Large file error
- PDFs are too large for GitHub
- They're already in .gitignore
- If you need to share PDFs, use Git LFS or external storage

### Need to remove sensitive data
If you accidentally committed sensitive data:
```bash
# Remove file from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/sensitive/file" \
  --prune-empty --tag-name-filter cat -- --all

# Force push
git push origin --force --all
```

---

## Repository URL Format

Your repository will be at:
```
https://github.com/YOUR_USERNAME/uae-legal-etl-pipeline
```

Clone URL for others:
```
https://github.com/YOUR_USERNAME/uae-legal-etl-pipeline.git
```

---

## Next Steps After Publishing

1. ✅ Share the repository URL
2. ✅ Add collaborators (Settings → Collaborators)
3. ✅ Set up branch protection (Settings → Branches)
4. ✅ Enable issues for bug tracking
5. ✅ Add a CONTRIBUTING.md file
6. ✅ Add a CODE_OF_CONDUCT.md file
7. ✅ Set up GitHub Actions for CI/CD (optional)

---

**Need Help?**
- GitHub Docs: https://docs.github.com
- Git Basics: https://git-scm.com/book/en/v2/Getting-Started-Git-Basics
- GitHub Desktop Help: https://docs.github.com/en/desktop
