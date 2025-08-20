@echo off
echo Cleaning sensitive data and syncing to GitHub...

echo.
echo Removing any existing .env with hardcoded keys...
if exist .env del .env

echo.
echo Creating clean .env from template...
copy .env.example .env

echo.
echo Initializing Git repository...
git init

echo.
echo Adding all files (secrets are ignored)...
git add .

echo.
echo Committing clean code...
git commit -m "Initial commit: DB-Buddy AI Database Assistant (Clean)

Features:
- AI-powered database troubleshooting and optimization
- Support for multiple cloud providers (AWS, Azure, GCP)
- Interactive chat interface with LOV selectors
- Context-aware recommendations for cloud databases
- Multiple deployment options (Flask, Streamlit)
- Secure API key handling via environment variables
- Streamlit secrets support for cloud deployment"

echo.
echo Adding remote repository...
git remote add origin https://github.com/tb-repo/DB-Buddy.git 2>nul || git remote set-url origin https://github.com/tb-repo/DB-Buddy.git

echo.
echo Fetching existing repository...
git fetch origin

echo.
echo Creating feature branch...
git checkout -b feature/clean-implementation

echo.
echo Pushing clean code to feature branch...
git push -u origin feature/clean-implementation

echo.
echo Clean code synced to feature branch!
echo.
echo Next steps:
echo 1. Go to https://github.com/tb-repo/DB-Buddy
echo 2. Create a Pull Request from 'feature/clean-implementation' to 'main'
echo 3. Merge the PR to complete the sync
echo.
echo For Streamlit deployment:
echo 1. Add GROQ_API_KEY to Streamlit secrets
echo 2. Deploy streamlit_app.py
echo.
pause