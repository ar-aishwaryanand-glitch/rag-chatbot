# External Integrations

**Analysis Date:** 2026-02-09

## APIs & External Services

**LLM Providers:**
- Groq - Primary LLM provider for agent inference
  - SDK/Client: `groq>=0.4.0`, `langchain-groq>=0.1.0`
  - Auth: `GROQ_API_KEY`
  - Model: `llama-3.3-70b-versatile` (default)
  - Config: `src/config.py` lines 15-22, `src/rag_chain.py` lines 182-203

- Google Gemini - Alternative LLM provider (fallback)
  - SDK/Client: `langchain-google-genai>=0.1.0`
  - Auth: `GOOGLE_API_KEY`
  - Model: `gemini-2.0-flash-exp` (default)
  - Config: `src/config.py` lines 24-25, `src/rag_chain.py` lines 205-213

**Embedding Providers:**
- HuggingFace - Primary embedding provider (local)
  - SDK/Client: `langchain-huggingface>=0.0.1`, `sentence-transformers>=2.2.0`
  - Model: `sentence-transformers/all-MiniLM-L6-v2` (default)
  - Implementation: `src/embeddings.py` lines 19-37

- Google Embeddings - Alternative provider
  - SDK/Client: `langchain-google-genai`
  - Auth: `GOOGLE_API_KEY`
  - Model: `models/embedding-001`
  - Implementation: `src/embeddings.py` lines 39-44

**Web Search:**
- DuckDuckGo - Free web search (no API key required)
  - SDK/Client: `duckduckgo-search>=3.8.0`
  - Implementation: `src/agent/tools/web_search_tool.py`
  - Rate limit: 10 searches/minute (configurable)

- Tavily - Enhanced web search (optional)
  - Auth: `TAVILY_API_KEY`
  - Config: `src/config.py` line 85

- NewsAPI - News article search
  - SDK/Client: `newsapi-python>=0.2.7`
  - Auth: `NEWSAPI_KEY`
  - Free tier: 100 requests/day
  - Implementation: `src/agent/tools/news_api_tool.py` lines 21-23

- Google News RSS - Fallback news source
  - SDK/Client: `feedparser>=6.0.10`
  - No auth required
  - Implementation: `src/agent/tools/news_api_tool.py` lines 27-30

**Confluence:**
- Atlassian Confluence - Document import integration
  - SDK/Client: `requests` with HTTP Basic Auth
  - Auth: `CONFLUENCE_USERNAME`, `CONFLUENCE_API_TOKEN`
  - Config: `CONFLUENCE_URL`, `CONFLUENCE_SPACE_KEY`, `CONFLUENCE_ENABLED`
  - Implementation: `src/confluence_loader.py`

## Data Storage

**Databases:**
- PostgreSQL - Persistent session and checkpoint storage (optional)
  - Connection: `DATABASE_URL` or individual `POSTGRES_*` vars
  - Client: `psycopg2-binary>=2.9.0` (sessions), `psycopg[binary]>=3.1.0` (checkpoints)
  - Schema: `scripts/setup/init_supabase_schema.sql`
  - Session manager: `src/database/session_manager.py`
  - Checkpoint backend: `src/database/checkpoint_backend.py` lines 19-21
  - Models: `src/database/models.py`
  - Usage: Enabled via `USE_POSTGRES=true` and `USE_CHECKPOINTS=true`

- Supabase - Managed PostgreSQL (optional)
  - Connection: `SUPABASE_URL`, `SUPABASE_KEY`
  - Compatible with PostgreSQL backend

**Vector Storage:**
- FAISS - Local vector database (default)
  - Client: `faiss-cpu>=1.7.0`, `langchain-community`
  - Storage: `data/vector_store/` directory
  - Implementation: `src/vector_store.py` lines 8-9
  - No external service required

- Pinecone - Cloud vector database (optional)
  - SDK/Client: `pinecone-client>=3.0.0`, `langchain-pinecone>=0.0.1`
  - Auth: `PINECONE_API_KEY`
  - Config: `PINECONE_INDEX_NAME`, `PINECONE_NAMESPACE`, `PINECONE_CLOUD`, `PINECONE_REGION`, `PINECONE_METRIC`
  - Implementation: `src/vector_store_pinecone.py` line 40
  - Usage: Enabled via `USE_PINECONE=true`

**File Storage:**
- Local filesystem only
  - Documents: `data/documents/`
  - Vector store: `data/vector_store/`
  - Memory: `data/memory_store/`
  - Workspace: `data/workspace/`
  - Episodic memory: `data/episodic_memory/`

**Caching:**
- Redis - Distributed task queue and coordination (optional)
  - Client: `redis>=5.0.0`
  - Connection: `REDIS_URL` or individual `REDIS_*` vars
  - Implementation: `src/task_queue/task_queue.py` line 18
  - Usage: Enabled via `USE_REDIS_QUEUE=true`

## Authentication & Identity

**Auth Provider:**
- None - No built-in authentication system
  - Implementation: Application-level auth not implemented
  - API keys managed via environment variables
  - Streamlit secrets: `.streamlit/secrets.toml` (for deployment)

## Monitoring & Observability

**Error Tracking:**
- None - No dedicated error tracking service

**Logs:**
- Console logging via Python `print()` statements
- Observability framework: `src/observability.py`

**Tracing:**
- OpenTelemetry - Distributed tracing (optional)
  - SDK: `opentelemetry-api>=1.20.0`, `opentelemetry-sdk>=1.20.0`
  - Exporters: Console (dev), OTLP (prod), Jaeger (optional)
  - Config: `ENABLE_OBSERVABILITY`, `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_TYPE`, `OTEL_EXPORTER_ENDPOINT`
  - Implementation: `src/observability.py` lines 17-29
  - Traces: RAG operations, agent operations, tool calls, LLM calls
  - Usage: Enabled via `ENABLE_OBSERVABILITY=true`

**Metrics:**
- OpenTelemetry Metrics - Performance metrics (optional)
  - Exporters: Console (dev), OTLP (prod)
  - Config: `COLLECT_METRICS=true`, `METRIC_EXPORT_INTERVAL` (seconds)
  - Metrics tracked: retrieval latency, generation latency, query duration, errors

## CI/CD & Deployment

**Hosting:**
- Railway.app - Primary deployment target
  - Config: `railway.json`
  - Port: Dynamic via `$PORT` env var
  - Health check: `/_stcore/health`

- Render.com - Alternative deployment target
  - Config: `render.yaml`
  - Docker-based deployment
  - Free tier compatible

- Docker - Containerized deployment
  - Image: `python:3.11-slim`
  - Port: 8503 (exposed)
  - Health check: `/_stcore/health` endpoint

**CI Pipeline:**
- None - No GitHub Actions or CI workflows configured

## Environment Configuration

**Required env vars:**
- `GROQ_API_KEY` - Groq LLM API key (critical)

**Optional env vars (features):**
- `PINECONE_API_KEY` - Cloud vector storage
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis message queue
- `TAVILY_API_KEY` - Enhanced web search
- `NEWSAPI_KEY` - News API access
- `CONFLUENCE_URL`, `CONFLUENCE_USERNAME`, `CONFLUENCE_API_TOKEN`, `CONFLUENCE_SPACE_KEY` - Confluence integration
- `GOOGLE_API_KEY` - Google Gemini and embeddings

**Optional env vars (observability):**
- `OTEL_EXPORTER_ENDPOINT` - OpenTelemetry collector endpoint
- `OTEL_EXPORTER_HEADERS` - OTLP exporter headers (e.g., API keys)

**Feature flags:**
- `USE_PINECONE` - Enable cloud vector storage (default: false)
- `USE_POSTGRES` - Enable PostgreSQL backend (default: false)
- `USE_CHECKPOINTS` - Enable agent checkpointing (default: true)
- `USE_REDIS_QUEUE` - Enable distributed task queue (default: false)
- `USE_POLICY_ENGINE` - Enable agent governance (default: true)
- `ENABLE_OBSERVABILITY` - Enable OpenTelemetry (default: false)
- `CODE_EXECUTOR_ENABLED` - Enable code execution tool (default: false, security risk)
- `FILE_OPS_ENABLED` - Enable file operations tool (default: true)
- `WEB_SEARCH_ENABLED` - Enable web search tool (default: true)

**Secrets location:**
- Development: `.env` file in project root
- Production (Railway/Render): Platform-specific env var management
- Streamlit Cloud: `.streamlit/secrets.toml`

## Webhooks & Callbacks

**Incoming:**
- None - No webhook endpoints configured

**Outgoing:**
- None - No outbound webhooks configured

---

*Integration audit: 2026-02-09*
