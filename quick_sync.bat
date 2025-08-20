@echo off
echo Quick sync to GitHub (handling existing remote)...

echo.
echo Updating remote URL...
git remote set-url origin https://github.com/tb-repo/DB-Buddy.git

echo.
echo Adding clean files...
git add .

echo.
echo Committing clean code...
git commit -m "Clean implementation: Removed hardcoded API keys, added Streamlit secrets support"

echo.
echo Fetching from GitHub...
git fetch origin

echo.
echo Creating/switching to feature branch...
git checkout -b feature/clean-implementation 2>nul || git checkout feature/clean-implementation

echo.
echo Pushing to GitHub...
git push -u origin feature/clean-implementation

echo.
echo Done! Create PR at: https://github.com/tb-repo/DB-Buddy
pause