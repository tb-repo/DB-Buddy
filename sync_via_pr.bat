@echo off
echo Setting up Git repository for DB-Buddy with Pull Request...

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

echo.
echo Fetching existing repository...
git fetch origin

echo.
echo Creating feature branch...
git checkout -b feature/initial-implementation

echo.
echo Pushing feature branch...
git push -u origin feature/initial-implementation

echo.
echo Repository synced to feature branch!
echo.
echo Next steps:
echo 1. Go to https://github.com/tb-repo/DB-Buddy
echo 2. Create a Pull Request from 'feature/initial-implementation' to 'main'
echo 3. Merge the PR to complete the sync
echo.
echo IMPORTANT: Set environment variables in deployment platform:
echo - GROQ_API_KEY=your_groq_api_key
echo - HUGGINGFACE_API_KEY=your_huggingface_api_key
echo.
pause