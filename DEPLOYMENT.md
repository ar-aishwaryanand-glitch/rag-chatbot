# Deployment Guide

This guide explains how to deploy the RAG Agent Assistant on a new machine.

---

## Prerequisites

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| Python | 3.9+ | `python --version` |
| pip | Latest | `pip --version` |
| Git | Any | `git --version` (optional) |

---

## Quick Start

### Option 1: Automated Setup (Recommended)

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
setup.bat
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env

# 5. Edit .env with your API keys
# (see Environment Variables section below)

# 6. Run the app
make run
# OR
streamlit run src/ui/streamlit_app_agent.py
```

---

## Environment Variables

Create a `.env` file in the project root with these settings:

### Required

```bash
# OpenAI API Key (for embeddings and LLM)
OPENAI_API_KEY=sk-your-key-here
```

### Optional - Web Search

```bash
# Tavily API for web search (free tier available)
# Get key at: https://tavily.com
TAVILY_API_KEY=tvly-your-key-here

# News API for news search
# Get key at: https://newsapi.org
NEWSAPI_KEY=your-news-api-key
```

### Optional - Confluence Integration

```bash
# Confluence import feature
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_USERNAME=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token
```

### Optional - Database (PostgreSQL/Supabase)

```bash
# Default: SQLite (no config needed)
# For PostgreSQL:
DATABASE_URL=postgresql://user:password@host:5432/database

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

### Optional - Feature Flags

```bash
# Enable dangerous tools (code execution, file operations)
CODE_EXECUTOR_ENABLED=false
FILE_OPS_ENABLED=false

# Security settings
MAX_FILE_SIZE_MB=10
ALLOWED_FILE_EXTENSIONS=.txt,.md,.pdf,.py,.js,.json
```

---

## Directory Structure After Setup

```
rag work/
├── .env                 # Your API keys (create this)
├── .env.example         # Template (reference)
├── venv/                # Virtual environment (created by setup)
├── data/
│   ├── documents/       # Your uploaded documents
│   ├── vectorstore/     # Embeddings database
│   └── checkpoints/     # Conversation history
└── src/                 # Application code
```

---

## Running the Application

### Development Mode

```bash
# Using Makefile
make run

# Or directly
streamlit run src/ui/streamlit_app_agent.py
```

### Production Mode

```bash
# With custom port
streamlit run src/ui/streamlit_app_agent.py --server.port 8501 --server.address 0.0.0.0

# With Streamlit Cloud (see docs/STREAMLIT_CLOUD_DEPLOYMENT.md)
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `OPENAI_API_KEY not found` | Create `.env` file with your key |
| `Permission denied` (setup.sh) | Run `chmod +x setup.sh` |
| Port already in use | Use `--server.port 8502` |

### Check Installation

```bash
# Verify Python
python --version

# Verify dependencies
pip list | grep streamlit
pip list | grep langchain

# Test imports
python -c "from src.agent import AgentExecutor; print('OK')"
```

### Reset Data

```bash
# Clear vector store (re-index documents)
rm -rf data/vectorstore/

# Clear conversation history
rm -rf data/checkpoints/

# Clear all data
make clean
```

---

## Updating the Application

```bash
# If using Git
git pull origin main
pip install -r requirements.txt

# If using ZIP
# 1. Backup your .env and data/ folder
# 2. Replace all other files
# 3. Run pip install -r requirements.txt
```

---

## Support

- **Issues**: Check existing documentation in `docs/` folder
- **Configuration**: See `docs/CONFIGURATION.md`
- **Codebase**: See `CODEBASE_GUIDE.md`
