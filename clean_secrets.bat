@echo off
echo Cleaning secrets and resetting Git history...

echo.
echo Deleting files with hardcoded secrets...
if exist test_groq.py del test_groq.py
if exist .env del .env

echo.
echo Creating clean .env from template...
copy .env.example .env

echo.
echo Removing Git history to clean secrets...
rmdir /s /q .git

echo.
echo Reinitializing clean Git repository...
git init
git add .
git commit -m "Clean implementation: DB-Buddy AI Database Assistant

Features:
- AI-powered database troubleshooting and optimization
- Support for multiple cloud providers (AWS, Azure, GCP)
- Interactive chat interface with LOV selectors
- Context-aware recommendations for cloud databases
- Multiple deployment options (Flask, Streamlit)
- Secure API key handling via environment variables
- Streamlit secrets support for cloud deployment

Security:
- No hardcoded API keys
- Environment variable configuration
- Streamlit secrets integration"

echo.
echo Adding remote and pushing clean code...
git remote add origin https://github.com/tb-repo/DB-Buddy.git
git branch -M main
git push -f origin main

echo.
echo Clean code pushed to main branch!
echo.
echo IMPORTANT: Set environment variables in deployment platform:
echo - GROQ_API_KEY=your_groq_api_key
echo - HUGGINGFACE_API_KEY=your_huggingface_api_key
echo.
pause