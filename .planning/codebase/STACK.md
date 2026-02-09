# Technology Stack

**Analysis Date:** 2026-02-09

## Languages

**Primary:**
- Python 3.14.2 - Core application language for RAG agent, LLM integration, and backend logic
- Python 3.11/3.12 - Recommended fallback versions for compatibility (C extension build issues on 3.14)

## Runtime

**Environment:**
- Python 3.14 (with fallback to 3.11/3.12 for heavy packages)

**Package Manager:**
- pip - Standard Python package manager
- Virtual environments (venv) - Python built-in isolation

## Frameworks

**Core LLM & RAG:**
- LangChain Core (`langchain-core>=0.1.0`) - Core LLM abstractions and utilities
- LangChain Community (`langchain-community>=0.0.1`) - Community integrations
- LangChain Text Splitters (`langchain-text-splitters>=0.0.1`) - Document chunking utilities
- LangChain HuggingFace (`langchain-huggingface>=0.0.1`) - HuggingFace embeddings integration
- LangChain Groq (`langchain-groq>=0.1.0`) - Groq LLM provider integration
- LangChain Google GenAI (`langchain-google-genai>=0.1.0`) - Google Gemini embeddings
- LangChain Pinecone (`langchain-pinecone>=0.0.1`) - Pinecone vector store integration

**Agent Orchestration:**
- LangGraph (`langgraph>=0.0.20`) - State graph-based agent orchestration
- LangGraph Checkpoint (`langgraph-checkpoint>=1.0.2`) - State persistence and recovery
- LangGraph Checkpoint PostgreSQL (`langgraph-checkpoint-postgres>=1.0.0`) - Database-backed checkpoints

**Frontend:**
- Streamlit (`streamlit>=1.30.0`) - Web-based UI framework for chatbot interface

**Vector Storage:**
- FAISS CPU (`faiss-cpu>=1.7.0`) - Local, in-memory vector database (default)
- Pinecone Client (`pinecone-client>=3.0.0`) - Cloud vector database (optional, for production)

**Embeddings:**
- Sentence Transformers (`sentence-transformers>=2.2.0`) - Local embedding models (e.g., all-MiniLM-L6-v2)

**Testing:**
- pytest - Test runner (configured in `Makefile`)

**Build/Dev:**
- Python-dotenv (`python-dotenv>=1.0.0`) - Environment variable management

## Key Dependencies

**Critical - LLM Providers:**
- Groq (`groq>=0.4.0`) - Primary LLM provider for fast inference (default: llama-3.3-70b-versatile)
- Google GenAI (`google-genai>=1.0.0`) - Alternative LLM provider (fallback: gemini-2.0-flash-exp)

**Critical - Embeddings:**
- Sentence Transformers (`sentence-transformers>=2.2.0`) - ~2GB download, required for local embeddings
- HuggingFace Transformers - Implicit dependency from sentence-transformers

**Agent Tools:**
- DuckDuckGo Search (`duckduckgo-search>=3.8.0`) - Free web search via DuckDuckGo library (DDGS)
- Playwright (`playwright>=1.40.0`) - Browser automation for web agent tool
- Beautiful Soup 4 (`beautifulsoup4>=4.12.0`) - HTML parsing for web scraping
- Readability (`readability-lxml>=0.8.1`) - Article content extraction from web pages
- lxml (`lxml>=4.9.0`) - XML/HTML processing library
- RestrictedPython (`RestrictedPython>=6.0`) - Sandboxed code execution for code executor tool
- NumExpr (`numexpr>=2.8.0`) - Safe math expression evaluation for calculator tool

**News & Web Scraping:**
- NewsAPI (`newsapi-python>=0.2.7`) - NewsAPI client for comprehensive news coverage
- Feedparser (`feedparser>=6.0.10`) - RSS feed parser for Google News fallback
- Python-dateutil (`python-dateutil>=2.8.2`) - Advanced date parsing utilities

**Document Processing:**
- PyPDF (`pypdf>=3.17.0`) - PDF file parsing and extraction
- Python-DOCX (`python-docx>=1.0.0`) - DOCX file parsing and extraction

**Infrastructure:**
- psycopg2 (`psycopg2-binary>=2.9.0`) - PostgreSQL adapter for session storage
- psycopg3 (`psycopg[binary]>=3.1.0`) - PostgreSQL adapter for checkpoint storage
- Redis (`redis>=5.0.0`) - Redis client for message queue and distributed coordination
- PyYAML (`pyyaml>=6.0`) - YAML configuration parsing for policy engine

**Observability:**
- OpenTelemetry API (`opentelemetry-api>=1.20.0`) - Tracing and metrics API
- OpenTelemetry SDK (`opentelemetry-sdk>=1.20.0`) - Implementation and exporters
- OpenTelemetry OTLP Exporter (`opentelemetry-exporter-otlp>=1.20.0`) - OTLP gRPC export (Jaeger, Honeycomb)
- OpenTelemetry Jaeger Exporter (`opentelemetry-exporter-jaeger>=1.20.0`) - Jaeger-specific exporter

## Configuration

**Environment:**
- Configuration loaded from `.env` file via `python-dotenv`
- See `.env.example` for comprehensive list of configurable options
- Config class: `src/config.py` - Central configuration management with validation

**Build:**
- Makefile: `Makefile` - Common operations (run, test, setup, clean)
- No complex build system (pure Python project)

## Platform Requirements

**Development:**
- Python 3.11/3.12 recommended (3.14 has build issues with some C extensions)
- pip for package installation
- Virtual environment (venv)
- 4GB+ RAM for embedding models (sentence-transformers ~2GB)
- PostgreSQL 12+ (optional, for session/checkpoint storage)
- Redis 6+ (optional, for distributed task queue)

**Production:**
- Python 3.11/3.12 (stable, production-ready)
- PostgreSQL 12+ for persistent storage
- Pinecone cloud vector database (optional, recommended over local FAISS)
- Redis for distributed coordination (optional)
- 8GB+ RAM for production LLM workloads
- Compatible with cloud platforms: AWS, GCP, Azure (via environment config)

---

*Stack analysis: 2026-02-09*
