# Ollama Setup for DB-Buddy

## Quick Setup

### 1. Install Ollama
```bash
# Windows (PowerShell as Administrator)
winget install Ollama.Ollama

# Or download from: https://ollama.ai/download
```

### 2. Download AI Model
```bash
# Download lightweight model (2GB)
ollama pull llama3.2:3b

# Or larger model for better quality (4.7GB)
ollama pull llama3.2:7b
```

### 3. Verify Installation
```bash
# Check if Ollama is running
ollama list

# Test the model
ollama run llama3.2:3b "Hello, can you help with databases?"
```

### 4. Start DB-Buddy
```bash
# Ollama runs automatically in background
python app.py
```

## Features

### With Ollama (AI-Enhanced):
- 🤖 **Dynamic responses** based on your specific situation
- 🧠 **Context-aware advice** that adapts to your answers
- 💡 **Creative solutions** for unique database problems
- 🔄 **Natural conversation** flow

### Without Ollama (Rule-Based):
- 📋 **Structured recommendations** from predefined rules
- ⚡ **Fast responses** with no AI processing delay
- 🔒 **Reliable advice** based on best practices
- 💾 **Low resource usage**

## System Requirements

- **RAM**: 8GB+ recommended for 3B model
- **Storage**: 2-5GB for model files
- **CPU**: Modern processor (any recent CPU works)

## Troubleshooting

### Ollama Not Working?
1. Check if service is running: `ollama list`
2. Restart Ollama service
3. DB-Buddy automatically falls back to rule-based mode

### Model Download Issues?
```bash
# Try different model
ollama pull mistral:7b

# Check available models
ollama list
```

## Model Recommendations

- **llama3.2:3b** - Fast, good for basic advice (2GB)
- **llama3.2:7b** - Better quality responses (4.7GB)  
- **mistral:7b** - Alternative option (4.1GB)
- **codellama:7b** - Specialized for code/SQL (3.8GB)

DB-Buddy works with any Ollama model - just update the model name in `app.py` if needed.