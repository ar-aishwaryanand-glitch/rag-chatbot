# Technology Stack

**Analysis Date:** 2026-02-09

## Languages

**Primary:**
- Python 3.14.2 - Core application language for entire codebase

**Secondary:**
- None detected

## Runtime

**Environment:**
- Python 3.14.2 (compatible with 3.11+)
- Virtual environment: `venv/` (present in project)

**Package Manager:**
- pip
- Lockfile: Not present (uses `requirements.txt` only)

## Frameworks

**Core:**
- LangChain 0.1.0+ - Agent orchestration, LLM chains, RAG pipeline
- LangGraph 0.0.20+ - Agent state graphs and workflow management
- Streamlit 1.30.0+ - Web UI framework for the agent interface

**Testing:**
- pytest 5.0+ - Test runner with markers for unit/integration/slow tests
- pytest-cov - Coverage reporting (configured in `pytest.ini`)

**Build/Dev:**
- Ruff - Fast Python linter and code formatter (configured in `ruff.toml`)
- Docker - Containerization (multi-stage build with Playwright support)
- Makefile - Task automation for common operations

## Key Dependencies

**Critical:**
- groq 0.4.0+ - Groq API client for LLM inference (primary LLM provider)
- langchain-groq 0.1.0+ - LangChain integration for Groq
- langchain-huggingface 0.0.1+ - HuggingFace embeddings integration
- sentence-transformers 2.2.0+ - Local embedding models (all-MiniLM-L6-v2)

**Vector Storage:**
- faiss-cpu 1.7.0+ - Local vector store (default)
- pinecone-client 3.0.0+ - Cloud vector database (optional)
- langchain-pinecone 0.0.1+ - Pinecone integration

**Agent Framework:**
- langgraph 0.0.20+ - Agent state management and workflows
- langgraph-checkpoint 1.0.2+ - Agent checkpointing system
- langgraph-checkpoint-postgres 1.0.0+ - PostgreSQL checkpoint backend

**Agent Tools:**
- duckduckgo-search 3.8.0+ - Free web search tool
- playwright 1.40.0+ - Browser automation for web agent
- beautifulsoup4 4.12.0+ - HTML parsing
- newsapi-python 0.2.7+ - NewsAPI client
- feedparser 6.0.10+ - RSS feed parsing
- numexpr 2.8.0+ - Safe math evaluation for calculator
- RestrictedPython 6.0+ - Sandboxed code execution

**Document Processing:**
- pypdf 3.17.0+ - PDF file parsing
- python-docx 1.0.0+ - DOCX file parsing
- readability-lxml 0.8.1+ - Article content extraction
- lxml 4.9.0+ - XML/HTML processing

**Infrastructure:**
- psycopg2-binary 2.9.0+ - PostgreSQL adapter (psycopg2 for sessions)
- psycopg[binary] 3.1.0+ - PostgreSQL adapter (psycopg3 for checkpoints)
- redis 5.0.0+ - Redis client for message queue (optional)
- python-dotenv 1.0.0+ - Environment variable management
- pyyaml 6.0+ - YAML config parsing for policy engine

**Observability:**
- opentelemetry-api 1.20.0+ - OpenTelemetry API
- opentelemetry-sdk 1.20.0+ - OpenTelemetry SDK
- opentelemetry-exporter-otlp 1.20.0+ - OTLP exporter
- opentelemetry-exporter-jaeger 1.20.0+ - Jaeger exporter (optional)

## Configuration

**Environment:**
- Configuration via `.env` file (example: `.env.example`)
- Centralized config in `src/config.py` using `Config` class
- Required vars: `GROQ_API_KEY` (primary LLM)
- Optional vars: `PINECONE_API_KEY`, `DATABASE_URL`, `REDIS_URL`, `NEWSAPI_KEY`, `TAVILY_API_KEY`, `CONFLUENCE_*`

**Build:**
- `Dockerfile` - Multi-stage build with Python 3.11-slim base
- `docker-compose.yml` - Not detected
- `pytest.ini` - Test configuration with markers
- `ruff.toml` - Linting/formatting rules
- `.dockerignore` - Docker build exclusions

**Deployment:**
- `railway.json` - Railway.app deployment config
- `render.yaml` - Render.com deployment config
- `Makefile` - Development commands (run, test, setup, clean)

## Platform Requirements

**Development:**
- Python 3.11+ (tested with 3.14.2)
- Virtual environment recommended
- System dependencies for Playwright (libnss3, libatk, etc.)
- Optional: PostgreSQL 9.6+ for persistent sessions
- Optional: Redis 5.0+ for distributed task queue

**Production:**
- Docker container (exposed port 8503)
- Railway.app or Render.com compatible
- Groq API key required
- Optional: Pinecone for cloud vector storage
- Optional: PostgreSQL for session persistence
- Optional: Redis for distributed agents

---

*Stack analysis: 2026-02-09*
