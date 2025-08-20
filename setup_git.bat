@echo off
echo Setting up Git repository for DB-Buddy...

git init
git add .
git commit -m "Initial commit: DB-Buddy AI Database Assistant

Features:
- AI-powered database troubleshooting and optimization
- Support for multiple cloud providers (AWS, Azure, GCP)
- Interactive chat interface with LOV selectors
- Context-aware recommendations for cloud databases
- Multiple deployment options (Flask, Streamlit)
- Support for Groq, Hugging Face, and Ollama AI providers"

echo.
echo Adding remote repository...
git remote add origin https://github.com/tb-repo/DB-Buddy.git
git branch -M main

echo.
echo Pushing to GitHub...
git push -u origin main

echo.
echo Repository synced to https://github.com/tb-repo/DB-Buddy
echo.
echo IMPORTANT: Set environment variables in your deployment platform:
echo - GROQ_API_KEY=your_groq_api_key
echo - HUGGINGFACE_API_KEY=your_huggingface_api_key
echo.
pause