# DeepTutor Quick Start Guide (Windows + Claude Max)

This guide explains how to run DeepTutor on Windows using your Claude Max subscription for LLM calls and Ollama for embeddings.

## System Requirements

- Windows 10/11
- Python 3.10+
- Node.js 18+
- Claude Code CLI (authenticated with Max subscription)
- ~2GB disk space on D:\ drive

## Installation Summary

DeepTutor is installed at `D:\DeepTutor` with the following setup:

| Component | Location | Purpose |
|-----------|----------|---------|
| DeepTutor | `D:\DeepTutor` | Main application |
| Ollama Models | `D:\ollama_models` | Embedding model storage |
| Ollama Program | `C:\Users\...\Programs\Ollama` | Ollama executable |

## Starting the System

### Option 1: Manual Start (3 terminals)

**Terminal 1 - Ollama:**
```cmd
set OLLAMA_MODELS=D:\ollama_models
"C:\Users\cs06t\AppData\Local\Programs\Ollama\ollama.exe" serve
```

**Terminal 2 - Backend:**
```cmd
cd D:\DeepTutor
python src/api/run_server.py
```

**Terminal 3 - Frontend:**
```cmd
cd D:\DeepTutor\web
npm run dev -- -p 3782
```

### Option 2: Using PowerShell Script

Create `D:\start_deeptutor.ps1`:
```powershell
# Start Ollama
$env:OLLAMA_MODELS = "D:\ollama_models"
Start-Process -FilePath "C:\Users\cs06t\AppData\Local\Programs\Ollama\ollama.exe" -ArgumentList "serve" -WindowStyle Minimized

Start-Sleep -Seconds 3

# Start Backend
Start-Process -FilePath "python" -ArgumentList "src/api/run_server.py" -WorkingDirectory "D:\DeepTutor" -WindowStyle Minimized

Start-Sleep -Seconds 5

# Start Frontend
Start-Process -FilePath "npm" -ArgumentList "run dev -- -p 3782" -WorkingDirectory "D:\DeepTutor\web" -WindowStyle Minimized

Write-Host "DeepTutor starting..."
Write-Host "Frontend: http://localhost:3782"
Write-Host "Backend:  http://localhost:8001"
```

Run with: `powershell -ExecutionPolicy Bypass -File D:\start_deeptutor.ps1`

## Accessing DeepTutor

Open your browser and navigate to: **http://localhost:3782**

## Service Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3782 | http://localhost:3782 |
| Backend API | 8001 | http://localhost:8001 |
| Ollama | 11434 | http://localhost:11434 |

## Using DeepTutor

### 1. Create a Knowledge Base

1. Click **Knowledge** in the sidebar
2. Click **Create New Knowledge Base**
3. Upload your documents (PDF, Markdown, or Text files)
4. Wait for processing (this builds the vector index and knowledge graph)

### 2. Ask Questions (Smart Solver)

1. Click **Solve** in the sidebar
2. Select your Knowledge Base
3. Type your question
4. Get answers with citations from your documents

### 3. Generate Practice Questions

1. Click **Question** in the sidebar
2. Choose **Custom** to generate questions from topics
3. Or choose **Mimic** to upload an exam PDF and generate similar questions

### 4. Deep Research

1. Click **Research** in the sidebar
2. Enter a research topic
3. Select depth: Quick / Medium / Deep / Auto
4. Get a comprehensive research report with citations

### 5. Guided Learning

1. Click **Guide** in the sidebar
2. Select notebooks/knowledge bases
3. Get interactive visual explanations of concepts

## Configuration Files

### `.env` (Main configuration)

```bash
# LLM - Claude Code CLI mode
LLM_BINDING=claude_code
LLM_MODEL=claude-sonnet-4-20250514
CLAUDE_CODE_PATH=C:\Users\cs06t\AppData\Roaming\npm\claude.cmd

# Embeddings - Ollama
EMBEDDING_BINDING=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSION=768
EMBEDDING_HOST=http://localhost:11434
OLLAMA_MODELS=D:\ollama_models

# Server
BACKEND_PORT=8001
FRONTEND_PORT=3782
```

### `config/main.yaml` (Module settings)

Contains settings for each module (solve, research, question, guide, etc.)

### `config/agents.yaml` (LLM parameters)

Contains temperature and max_tokens for each module.

## Troubleshooting

### "Claude Code CLI not found"

Install Claude Code:
```bash
npm install -g @anthropic-ai/claude-code
claude login
```

### "Ollama connection refused"

Start Ollama with the correct models path:
```cmd
set OLLAMA_MODELS=D:\ollama_models
"C:\Users\cs06t\AppData\Local\Programs\Ollama\ollama.exe" serve
```

### "Embedding model not found"

Pull the model:
```cmd
set OLLAMA_MODELS=D:\ollama_models
ollama pull nomic-embed-text
```

### Unicode errors in console

Set Python encoding:
```cmd
set PYTHONIOENCODING=utf-8
python src/api/run_server.py
```

### Backend not responding

Check if port 8001 is in use:
```cmd
netstat -an | findstr 8001
```

## Stopping the System

1. Press `Ctrl+C` in each terminal window
2. Or use Task Manager to end `python.exe`, `node.exe`, and `ollama.exe` processes

## Updating DeepTutor

```bash
cd D:\DeepTutor
git pull origin main
pip install -r requirements.txt
cd web && npm install
```

## Disk Space Cleanup

You can safely delete:
- `D:\OllamaSetup.exe` (1.2GB installer, no longer needed)

## Architecture Overview

```
Browser (http://localhost:3782)
    |
    v
Next.js Frontend (React 19)
    |
    v
FastAPI Backend (http://localhost:8001)
    |
    +---> Claude Code CLI ---> Your Max Subscription
    |         (LLM)
    |
    +---> Ollama (http://localhost:11434)
              (Embeddings)
              |
              v
         D:\ollama_models\nomic-embed-text
```

## Support

- DeepTutor Issues: https://github.com/HKUDS/DeepTutor/issues
- Claude Code Issues: https://github.com/anthropics/claude-code/issues
