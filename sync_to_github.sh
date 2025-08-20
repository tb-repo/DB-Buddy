#!/bin/bash

echo "Setting up Git repository for DB-Buddy..."

# Initialize git if not already done
if [ ! -d ".git" ]; then
    git init
fi

# Add all files
git add .

# Commit changes
git commit -m "Initial commit: DB-Buddy AI Database Assistant

Features:
- AI-powered database troubleshooting and optimization
- Support for multiple cloud providers (AWS, Azure, GCP)
- Interactive chat interface with LOV selectors
- Context-aware recommendations for cloud databases
- Multiple deployment options (Flask, Streamlit)
- Support for Groq, Hugging Face, and Ollama AI providers"

# Add remote repository
git remote add origin https://github.com/tb-repo/DB-Buddy.git 2>/dev/null || git remote set-url origin https://github.com/tb-repo/DB-Buddy.git

# Set main branch
git branch -M main

# Push to GitHub
git push -u origin main

echo ""
echo "Repository synced to https://github.com/tb-repo/DB-Buddy"
echo ""
echo "IMPORTANT: Set environment variables in your deployment platform:"
echo "- GROQ_API_KEY=your_groq_api_key"
echo "- HUGGINGFACE_API_KEY=your_huggingface_api_key"
echo ""