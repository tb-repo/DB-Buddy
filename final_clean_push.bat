@echo off
echo Final clean push to GitHub...

echo.
echo Deleting files with secrets...
if exist test_groq.py del test_groq.py
if exist .env del .env

echo.
echo Creating clean .env...
copy .env.example .env

echo.
echo Checking current branch...
git branch

echo.
echo Adding clean files...
git add .
git commit -m "Remove secrets and clean implementation"

echo.
echo Checking what branch we're on...
for /f %%i in ('git branch --show-current') do set CURRENT_BRANCH=%%i
echo Current branch: %CURRENT_BRANCH%

echo.
echo Pushing to current branch...
git push origin %CURRENT_BRANCH%

echo.
echo Done! Check GitHub for your clean code.
pause