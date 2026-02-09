# Configuration Guide

## Overview

All system configuration is managed through:
1. **Environment variables** (`.env` file)
2. **Config class** ([src/config.py](../src/config.py))

## Configuration File

### Location

```bash
# Project root
.env
```

### Format

```bash
# Comments start with #
SETTING_NAME=value

# No spaces around =
LLM_PROVIDER=groq  # ✅ Correct
LLM_PROVIDER = groq  # ❌ Wrong

# Multi-word values don't need quotes
DATABASE_URL=postgresql://user:pass@host:5432/db

# But quotes don't hurt
DATABASE_URL="postgresql://user:pass@host:5432/db"
```

## Complete Configuration Reference

### LLM Settings

```bash
# ===== LLM PROVIDER =====

# Which LLM to use: "groq" or "google"
LLM_PROVIDER=groq

# Groq Configuration (fast, free tier available)
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile

# Available Groq models:
# - llama-3.3-70b-versatile (recommended)
# - llama-3.1-70b-versatile
# - mixtral-8x7b-32768
# - gemma2-9b-it

# Google Gemini Configuration (alternative)
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL=gemini-2.0-flash-exp

# LLM Parameters
LLM_TEMPERATURE=0.7      # 0.0 (deterministic) to 1.0 (creative)
LLM_MAX_TOKENS=1024      # Max output length
```

**Choosing a Provider**:
- **Groq**: Fastest, free tier, good quality
- **Google**: More advanced, paid, multimodal support

### Embedding Settings

```bash
# ===== EMBEDDINGS =====

# Embedding provider: "huggingface" or "google"
EMBEDDING_PROVIDER=huggingface

# HuggingFace Models (FREE, runs locally)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Popular options:
# - all-MiniLM-L6-v2: Fast, 384-dim, 80MB (recommended)
# - all-mpnet-base-v2: Better quality, 768-dim, 420MB
# - multi-qa-mpnet-base-dot-v1: Optimized for Q&A

# Google Embeddings (PAID, API-based)
# EMBEDDING_PROVIDER=google
# GOOGLE_API_KEY=your_key
# EMBEDDING_MODEL=models/embedding-001
```

**Model Comparison**:

| Model | Dimensions | Size | Speed | Quality |
|-------|------------|------|-------|---------|
| all-MiniLM-L6-v2 | 384 | 80MB | Fast | Good |
| all-mpnet-base-v2 | 768 | 420MB | Medium | Better |
| Google embedding-001 | 768 | API | Fast | Excellent |

### Vector Store Settings

```bash
# ===== VECTOR STORE =====

# Chunking parameters
CHUNK_SIZE=800           # Characters per chunk
CHUNK_OVERLAP=100        # Overlap between chunks

# Retrieval
TOP_K_RESULTS=3          # Documents to retrieve per query

# Vector store backend: local FAISS or cloud Pinecone
USE_PINECONE=false

# Pinecone Configuration (if USE_PINECONE=true)
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=rag-agent
PINECONE_CLOUD=aws       # aws, gcp, azure
PINECONE_REGION=us-east-1
PINECONE_METRIC=cosine   # cosine, euclidean, dotproduct
PINECONE_NAMESPACE=      # Optional namespace
```

**FAISS vs Pinecone**:

| Feature | FAISS | Pinecone |
|---------|-------|----------|
| Cost | FREE | Paid |
| Speed | Fast | Fast |
| Scale | ~100k docs | Billions |
| Hosting | Local | Cloud |
| Setup | None | API key |

### Agent Settings

```bash
# ===== AGENT CONFIGURATION =====

# Enable agent mode
AGENT_ENABLED=true

# Agent execution mode
AGENT_MODE=hybrid        # react, plan-execute, hybrid

# Execution limits
AGENT_MAX_ITERATIONS=10  # Max tool retry attempts
AGENT_TIMEOUT=120        # Total execution timeout (seconds)

# Debugging
AGENT_VERBOSE=true       # Print execution details
```

**Agent Modes**:
- **react**: Single-step reasoning (fastest)
- **plan-execute**: Plan first, then execute (more thorough)
- **hybrid**: Adaptive (recommended)

### Memory Settings

```bash
# ===== MEMORY CONFIGURATION =====

# Enable conversation memory
MEMORY_ENABLED=true

# Memory window (number of recent messages to keep)
MEMORY_WINDOW_SIZE=10

# Summarization frequency (summarize every N turns)
MEMORY_SUMMARY_FREQUENCY=5

# Memory storage path (for episodic memory)
# Default: data/memory_store/
```

**Memory Window Size**:
- Too small (< 5): Agent forgets quickly
- Just right (10-15): Good balance
- Too large (> 20): Token overhead

### Tool Settings

```bash
# ===== TOOL CONFIGURATION =====

# Web Search
WEB_SEARCH_ENABLED=true
WEB_SEARCH_PROVIDER=duckduckgo  # duckduckgo or tavily
TAVILY_API_KEY=your_tavily_key  # Optional, for Tavily

# Calculator
CALCULATOR_ENABLED=true

# Code Executor (⚠️ DISABLED by default for safety)
CODE_EXECUTOR_ENABLED=false
CODE_EXECUTION_TIMEOUT=5        # Timeout in seconds

# File Operations
FILE_OPS_ENABLED=true

# News API
NEWSAPI_KEY=your_newsapi_key    # Get from newsapi.org
```

**Tool Safety**:
- ✅ Safe: `document_search`, `web_search`, `calculator`, `news_api`
- ⚠️ Caution: `file_operations` (sandboxed workspace only)
- 🚨 Dangerous: `code_executor` (disabled by default)

### Database Settings

```bash
# ===== DATABASE CONFIGURATION =====

# Enable PostgreSQL for sessions and checkpoints
USE_POSTGRES=true
USE_CHECKPOINTS=true     # Enable checkpoint storage

# Full connection string (preferred)
DATABASE_URL=postgresql://user:password@host:port/database

# Or individual components
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=rag_chatbot
```

**Supabase Connection String Format**:
```bash
# Transaction pooler (for psycopg)
DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-1-ap-south-1.pooler.supabase.com:5432/postgres
```

### Policy & Safety Settings

```bash
# ===== SAFETY CONFIGURATION =====

# Code execution timeout
CODE_EXECUTION_TIMEOUT=5

# Reflection (self-evaluation)
REFLECTION_ENABLED=true

# Hallucination detection
HALLUCINATION_DETECTION=false  # Experimental

# Policy engine (content filtering, behavior control)
USE_POLICY_ENGINE=true
```

### Observability Settings

```bash
# ===== OBSERVABILITY =====

# Enable OpenTelemetry tracing and metrics
ENABLE_OBSERVABILITY=false

# Service identification
OTEL_SERVICE_NAME=rag-agent
OTEL_ENVIRONMENT=development  # development, staging, production

# Exporter type: console, otlp, jaeger
OTEL_EXPORTER_TYPE=console

# OTLP endpoint (for otlp exporter)
OTEL_EXPORTER_ENDPOINT=http://localhost:4317
OTEL_EXPORTER_HEADERS=   # Optional: API keys, auth headers

# Jaeger endpoint (for jaeger exporter)
JAEGER_HOST=localhost
JAEGER_PORT=6831

# What to trace
TRACE_RAG_OPERATIONS=true
TRACE_AGENT_OPERATIONS=true
TRACE_TOOL_CALLS=true
TRACE_LLM_CALLS=true

# Metrics
COLLECT_METRICS=true
METRIC_EXPORT_INTERVAL=60  # Seconds between exports
```

**Observability Stack**:
- **Console**: Print to stdout (development)
- **OTLP**: Send to Grafana, DataDog, etc.
- **Jaeger**: Open-source tracing UI

### Advanced Settings

```bash
# ===== ADVANCED =====

# Redis Task Queue (for distributed agents)
USE_REDIS_QUEUE=false
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Streaming (for real-time responses)
ENABLE_STREAMING=true

# Auto-indexing
AUTO_INDEX_ENABLED=false
AUTO_INDEX_INTERVAL=3600  # Seconds
```

## Environment-Specific Configuration

### Development

```bash
# .env.development
LLM_PROVIDER=groq              # Free tier
EMBEDDING_PROVIDER=huggingface  # Local, free
USE_POSTGRES=false              # Use file-based memory
USE_PINECONE=false              # Local FAISS
AGENT_VERBOSE=true              # Debug output
ENABLE_OBSERVABILITY=false      # No overhead
CODE_EXECUTOR_ENABLED=true      # OK for local testing
```

### Staging

```bash
# .env.staging
LLM_PROVIDER=groq
EMBEDDING_PROVIDER=huggingface
USE_POSTGRES=true               # Test database persistence
USE_CHECKPOINTS=true
USE_PINECONE=false              # FAISS still OK
AGENT_VERBOSE=false
ENABLE_OBSERVABILITY=true       # Test monitoring
CODE_EXECUTOR_ENABLED=false     # Safer
```

### Production

```bash
# .env.production
LLM_PROVIDER=groq               # Or google for better quality
EMBEDDING_PROVIDER=huggingface  # Or google
USE_POSTGRES=true               # Full persistence
USE_CHECKPOINTS=true
USE_PINECONE=true               # Scale to millions of docs
AGENT_VERBOSE=false
ENABLE_OBSERVABILITY=true       # Full monitoring
CODE_EXECUTOR_ENABLED=false     # NEVER enable in production
REFLECTION_ENABLED=true         # Quality monitoring
USE_POLICY_ENGINE=true          # Content filtering
```

## Accessing Configuration in Code

### Using Config Class

```python
from src.config import Config

# Access settings
llm_provider = Config.LLM_PROVIDER
chunk_size = Config.CHUNK_SIZE
memory_enabled = Config.MEMORY_ENABLED

# Display names
print(Config.get_llm_display_name())
# Output: "Groq (llama-3.3-70b-versatile)"

print(Config.get_embedding_display_name())
# Output: "HuggingFace (sentence-transformers/all-MiniLM-L6-v2)"

print(Config.get_vector_store_display_name())
# Output: "FAISS (Local)" or "Pinecone (rag-agent)"

# Validation (called automatically on import)
Config.validate()
```

### Programmatic Updates

```python
import os

# Update environment variable
os.environ['AGENT_VERBOSE'] = 'true'

# Reload config (if needed)
from importlib import reload
import src.config
reload(src.config)
```

## Configuration Validation

### Automatic Validation

On import, `Config.validate()` checks:
- ✅ Required API keys present
- ✅ Valid provider names
- ⚠️ Warnings for missing optional keys

```python
# src/config.py
@classmethod
def validate(cls):
    if cls.LLM_PROVIDER == "groq":
        if not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in .env")

    if cls.EMBEDDING_PROVIDER == "google" and not cls.GOOGLE_API_KEY:
        print("⚠️  Warning: Google embeddings selected but no key")
        print("   Falling back to HuggingFace")
        cls.EMBEDDING_PROVIDER = "huggingface"
```

### Manual Validation

```python
# Check configuration
from src.config import Config

def check_config():
    issues = []

    # Check LLM
    if Config.LLM_PROVIDER == "groq":
        if not Config.GROQ_API_KEY:
            issues.append("Missing GROQ_API_KEY")

    # Check Database
    if Config.USE_POSTGRES:
        if not Config.DATABASE_URL:
            issues.append("Missing DATABASE_URL")

    # Check Pinecone
    if Config.USE_PINECONE:
        if not Config.PINECONE_API_KEY:
            issues.append("Missing PINECONE_API_KEY")

    if issues:
        print("❌ Configuration issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False

    print("✅ Configuration valid")
    return True

check_config()
```

## Configuration Best Practices

### 1. Never Commit .env

```bash
# .gitignore
.env
.env.*
!.env.example
```

### 2. Use .env.example Template

```bash
# .env.example (committed to git)
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://user:password@host:port/database
# ... all required settings with placeholders
```

### 3. Environment-Specific Files

```bash
# Development
.env.development

# Staging
.env.staging

# Production
.env.production

# Load specific environment:
python -m dotenv -f .env.production run streamlit run app.py
```

### 4. Secret Management

For production, use secret managers:

```python
# AWS Secrets Manager
import boto3

secrets = boto3.client('secretsmanager')
secret = secrets.get_secret_value(SecretId='rag-agent-keys')

os.environ['GROQ_API_KEY'] = secret['GROQ_API_KEY']
```

### 5. Validate on Startup

```python
# streamlit_app_agent.py
if __name__ == "__main__":
    from src.config import Config

    try:
        Config.validate()
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        exit(1)

    # Start app
    run_app()
```

## Common Configuration Patterns

### Minimal Setup (Free Tier)

```bash
# Just the essentials
GROQ_API_KEY=gsk_...
LLM_PROVIDER=groq
EMBEDDING_PROVIDER=huggingface
USE_POSTGRES=false
AGENT_ENABLED=true
MEMORY_ENABLED=true
```

### Full-Featured Setup

```bash
# All features enabled
GROQ_API_KEY=gsk_...
LLM_PROVIDER=groq
EMBEDDING_PROVIDER=huggingface
USE_POSTGRES=true
USE_CHECKPOINTS=true
DATABASE_URL=postgresql://...
AGENT_ENABLED=true
MEMORY_ENABLED=true
WEB_SEARCH_ENABLED=true
NEWSAPI_KEY=...
ENABLE_OBSERVABILITY=true
```

### Production-Ready Setup

```bash
# Production configuration
GROQ_API_KEY=gsk_...
LLM_PROVIDER=groq
GROQ_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0.3

EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=all-mpnet-base-v2

USE_PINECONE=true
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=rag-agent-prod

USE_POSTGRES=true
USE_CHECKPOINTS=true
DATABASE_URL=postgresql://...

AGENT_ENABLED=true
AGENT_VERBOSE=false
AGENT_TIMEOUT=60

MEMORY_ENABLED=true
MEMORY_WINDOW_SIZE=15

CODE_EXECUTOR_ENABLED=false
FILE_OPS_ENABLED=true

ENABLE_OBSERVABILITY=true
OTEL_EXPORTER_TYPE=otlp
OTEL_EXPORTER_ENDPOINT=https://...

USE_POLICY_ENGINE=true
REFLECTION_ENABLED=true
```

## Troubleshooting

### Configuration not loading

**Symptom**: Settings not being applied

**Solutions**:
1. Check `.env` file exists in project root
2. Verify no syntax errors in `.env`
3. Restart application (env loaded at startup)
4. Check file permissions: `ls -la .env`

### API key errors

**Symptom**: "API key not found" or authentication errors

**Solutions**:
1. Verify key is in `.env`: `cat .env | grep API_KEY`
2. Check for extra spaces: `GROQ_API_KEY=xxx` not `GROQ_API_KEY = xxx`
3. Regenerate key if compromised
4. Check key hasn't expired

### Database connection fails

**Symptom**: "Could not connect to PostgreSQL"

**Solutions**:
1. Test connection: `psql $DATABASE_URL`
2. Check URL format is correct
3. Verify network access (firewall, VPN)
4. Ensure Supabase project is active
5. Use correct pooler mode (Transaction)

### Settings not taking effect

**Symptom**: Changed setting but behavior unchanged

**Solutions**:
1. Restart application (config cached)
2. Check spelling of setting name
3. Verify correct data type (true vs "true")
4. Check if setting requires other settings enabled

## Performance Tuning

### For Speed

```bash
LLM_PROVIDER=groq              # Fastest LLM
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Fast embeddings
TOP_K_RESULTS=3                # Fewer docs to process
MEMORY_WINDOW_SIZE=5           # Smaller context
AGENT_TIMEOUT=30               # Fail fast
```

### For Quality

```bash
LLM_PROVIDER=google            # Better reasoning
LLM_TEMPERATURE=0.3            # More deterministic
EMBEDDING_MODEL=all-mpnet-base-v2  # Better embeddings
TOP_K_RESULTS=5                # More context
MEMORY_WINDOW_SIZE=15          # Richer history
REFLECTION_ENABLED=true        # Quality monitoring
```

### For Scale

```bash
USE_PINECONE=true              # Cloud vector DB
USE_POSTGRES=true              # Persistent sessions
USE_REDIS_QUEUE=true           # Distributed processing
ENABLE_OBSERVABILITY=true      # Monitor performance
```

## Related Documentation

- [Agent System](AGENT_SYSTEM.md) - Agent configuration details
- [Memory System](MEMORY_SYSTEM.md) - Memory settings
- [RAG Core](RAG_CORE.md) - Embedding and vector store config
- [Database Persistence](DATABASE_PERSISTENCE.md) - Database settings
- [Tools Reference](TOOLS_REFERENCE.md) - Tool configuration
- [Codebase Guide](../CODEBASE_GUIDE.md) - System overview
