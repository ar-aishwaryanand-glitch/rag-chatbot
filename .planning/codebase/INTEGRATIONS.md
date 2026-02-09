# External Integrations

**Analysis Date:** 2026-02-09

## APIs & External Services

**LLM Providers:**
- Groq (Primary LLM)
  - What it's used for: Fast inference with open-source models (default: llama-3.3-70b-versatile)
  - SDK/Client: `langchain-groq` (`langchain-groq>=0.1.0`)
  - Auth: `GROQ_API_KEY` env var
  - Config: `src/config.py` lines 15-22 (GROQ_API_KEY, GROQ_MODEL, LLM_PROVIDER)
  - Implementation: `src/rag_chain.py` lines 182-195 (ChatGroq initialization)

- Google Gemini (Fallback LLM)
  - What it's used for: Alternative LLM provider when Groq unavailable
  - SDK/Client: `langchain-google-genai` (`langchain-google-genai>=0.1.0`)
  - Auth: `GOOGLE_API_KEY` env var
  - Config: `src/config.py` lines 24-25 (GEMINI_MODEL, GOOGLE_API_KEY)
  - Implementation: `src/rag_chain.py` lines 204-207 (ChatGoogleGenerativeAI initialization)

**Web Search APIs:**
- DuckDuckGo (Free, No Auth)
  - What it's used for: Web search results and current information retrieval
  - SDK/Client: `duckduckgo-search>=3.8.0` (DDGS library)
  - Auth: None (free service)
  - Implementation: `src/agent/tools/web_search_tool.py` lines 154-161 (DDGS() client usage)
  - Rate limiting: 10 searches/minute (built-in throttling)
  - Features: Relevance filtering, deduplication, artifact cleaning

- Tavily (Optional, Paid)
  - What it's used for: Premium web search integration
  - Auth: `TAVILY_API_KEY` env var
  - Config: `src/config.py` line 85 (WEB_SEARCH_PROVIDER setting)
  - Status: Optional, fallback support

- NewsAPI (Optional, Paid)
  - What it's used for: Latest news articles and news search
  - SDK/Client: `newsapi-python>=0.2.7`
  - Auth: `NEWSAPI_KEY` env var
  - Free tier: 100 requests/day
  - Implementation: `src/agent/tools/news_api_tool.py` lines 21-24, 69-78
  - Fallback: Google News RSS feeds via `feedparser>=6.0.10`

**Confluence Integration (Optional):**
- Atlassian Confluence
  - What it's used for: Document import from Confluence spaces
  - SDK/Client: HTTP API via `requests` (no official SDK)
  - Auth: Basic Auth (email + API token) or Bearer token
  - Config: `src/config.py` lines 126-130 (CONFLUENCE_ENABLED, CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN, CONFLUENCE_SPACE_KEY)
  - Implementation: `src/confluence_loader.py` lines 29-100+
  - API endpoints:
    - Space content: `/rest/api/content?spaceKey={SPACE_KEY}`
    - Page search: `/rest/api/content/search` (CQL queries)
    - Page content: `/rest/api/content/{pageId}` (with body expansion)
  - Authentication: Detects Confluence Server vs Cloud, uses appropriate auth method

## Data Storage

**Databases:**

Vector Databases:
- FAISS (Local, Default)
  - What it's used for: In-memory vector storage for document embeddings
  - Client: `faiss-cpu>=1.7.0`
  - Storage: Local filesystem at `data/vector_store/`
  - Implementation: `src/vector_store.py` (VectorStoreManager)
  - When to use: Development, single-instance deployments
  - Limitation: Not scalable across multiple servers

- Pinecone (Cloud, Optional for Production)
  - What it's used for: Scalable, cloud-based vector database
  - Provider: Pinecone (https://app.pinecone.io)
  - SDK/Client: `pinecone-client>=3.0.0`, `langchain-pinecone>=0.0.1`
  - Auth: `PINECONE_API_KEY` env var
  - Config: `src/config.py` lines 51-60
    - `USE_PINECONE`: Enable/disable (default: false)
    - `PINECONE_INDEX_NAME`: Index name (default: "rag-agent")
    - `PINECONE_NAMESPACE`: Namespace for isolation (optional)
    - `PINECONE_METRIC`: Distance metric - cosine, euclidean, dotproduct (default: cosine)
    - `PINECONE_CLOUD`: Cloud provider - aws, gcp, azure (default: aws)
    - `PINECONE_REGION`: Serverless region (default: us-east-1)
  - Implementation: `src/vector_store_pinecone.py` (PineconeVectorStore)
  - When to use: Production, multi-instance deployments, high availability

**Relational Database - PostgreSQL:**
- Connection: PostgreSQL 12+ database
- Purpose: Session storage, agent memory, checkpoint storage
- Adapter: psycopg2 (session storage) + psycopg3 (checkpoint storage)
- Config: `src/config.py` lines 104-112
  - `USE_POSTGRES`: Enable/disable (default: false)
  - `DATABASE_URL`: Full connection string (preferred)
  - Alternative: Individual components (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB)
  - Default connection: localhost:5432, user=postgres, db=rag_chatbot
- Implementation:
  - `src/database/postgres_backend.py` - Session and message storage (psycopg2)
  - `src/database/checkpoint_backend.py` - LangGraph checkpoint storage (psycopg3)
  - `src/database/session_manager.py` - Session lifecycle management
  - `src/database/models.py` - Data models (Session, Message, EpisodicMemory)

**Supabase (Cloud PostgreSQL):**
- What it's used for: Managed PostgreSQL alternative
- Connection: Via `DATABASE_URL` or Supabase credentials
- Config: `src/config.py` (commented examples)
  - `SUPABASE_URL`: Supabase project URL
  - `SUPABASE_KEY`: Anon key for authentication
- Implementation: Compatible with psycopg2/psycopg3 backends

**File Storage:**
- Local filesystem only - No external file storage service
- Paths:
  - Documents: `data/documents/`
  - Vector store: `data/vector_store/`
  - Memory store: `data/memory_store/`
  - Workspace: `data/workspace/`

**Caching:**
- Redis (Optional, for distributed caching and task queue)
  - What it's used for: Distributed message queue, caching, and agent coordination
  - Provider: Redis server 6+
  - SDK/Client: `redis>=5.0.0`
  - Auth: `REDIS_URL` env var (format: redis://[user:password@]host:port/db)
  - Config: `src/config.py` lines 117-123
    - `USE_REDIS_QUEUE`: Enable/disable (default: false)
    - `REDIS_URL`: Connection string
    - `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`: Individual components
  - Implementation: `src/task_queue/task_queue.py` (TaskQueue with Redis backend)
  - Features: Priority queues, task status tracking, pub/sub notifications, dead letter queue

## Authentication & Identity

**Auth Providers:**
- None - Custom authentication via API keys in environment variables
- All authentication is key-based:
  - LLM provider keys (Groq, Google)
  - External service keys (Tavily, NewsAPI, Confluence)
  - Database credentials (PostgreSQL connection strings)

**API Key Management:**
- Via `.env` file (development)
- Via environment variables (production)
- No OAuth2 or OIDC integration currently

## Monitoring & Observability

**Distributed Tracing:**
- OpenTelemetry Framework
  - SDK: `opentelemetry-api>=1.20.0`, `opentelemetry-sdk>=1.20.0`
  - Config: `src/config.py` lines 134-156
  - Implementation: `src/observability.py` (ObservabilityManager singleton)

**Exporters:**
- Console Exporter (Development)
  - Exports to stdout for debugging
  - Config: `OTEL_EXPORTER_TYPE=console`

- OTLP Exporter (Production)
  - Exports to OTLP gRPC endpoint
  - SDK: `opentelemetry-exporter-otlp>=1.20.0`
  - Config:
    - `OTEL_EXPORTER_TYPE=otlp`
    - `OTEL_EXPORTER_ENDPOINT`: gRPC endpoint (default: http://localhost:4317)
    - `OTEL_EXPORTER_HEADERS`: Optional auth headers
  - Compatible with: Jaeger, Honeycomb, Datadog, New Relic

- Jaeger Exporter (Optional)
  - Direct Jaeger integration
  - SDK: `opentelemetry-exporter-jaeger>=1.20.0`
  - Config:
    - `OTEL_EXPORTER_TYPE=jaeger`
    - `JAEGER_HOST`, `JAEGER_PORT` (default: localhost:6831)

**Instrumentation:**
- Tracing coverage: `src/config.py` lines 148-152
  - `TRACE_RAG_OPERATIONS`: RAG retrieval and generation
  - `TRACE_AGENT_OPERATIONS`: Agent execution steps
  - `TRACE_TOOL_CALLS`: Tool invocations
  - `TRACE_LLM_CALLS`: LLM API calls

- Metrics collection: `src/config.py` lines 154-156
  - `COLLECT_METRICS`: Enable/disable metrics
  - `METRIC_EXPORT_INTERVAL`: Export frequency (default: 60 seconds)

**Error Tracking:**
- None - Errors logged to console/stdout only
- Recommendation: Configure OTLP exporter for production error tracking

**Logs:**
- Approach: Console logging via Python print statements
- Observability module: `src/observability.py` provides structured logging with OpenTelemetry

## CI/CD & Deployment

**Hosting:**
- Not specified in codebase - Flexible deployment
- Compatible with:
  - Streamlit Cloud (native support)
  - Docker containers
  - Traditional VMs/servers
  - Serverless platforms (with modifications)

**CI Pipeline:**
- Not configured - Manual testing via pytest and Makefile

**Test Framework:**
- pytest (executed via `make test` or `make test-quick`)
- Test location: `tests/` directory structure

## Environment Configuration

**Required env vars for startup:**
- `GROQ_API_KEY` - Required for LLM (unless using Google)
- `GOOGLE_API_KEY` - Required if using Google Gemini
- `.env` file must be created from `.env.example`

**Recommended for full functionality:**
- `USE_POSTGRES=true` + `DATABASE_URL` - Session persistence
- `USE_PINECONE=true` + `PINECONE_API_KEY` - Production vector DB
- `ENABLE_OBSERVABILITY=true` + `OTEL_EXPORTER_*` - Monitoring
- `CONFLUENCE_ENABLED=true` + Confluence credentials - Document import

**Optional for enhanced features:**
- `TAVILY_API_KEY` - Premium web search
- `NEWSAPI_KEY` - News API integration
- `USE_REDIS_QUEUE=true` + `REDIS_URL` - Distributed task queue
- `USE_POLICY_ENGINE=true` - Agent behavior control

**Secrets location:**
- `.env` file (gitignored, must be created manually)
- File format: `KEY=value` pairs
- Loading: Handled by `src/config.py` via `python-dotenv`

## Webhooks & Callbacks

**Incoming:**
- None currently configured
- Streamlit provides built-in callback handling for widget interactions

**Outgoing:**
- Confluence: One-way read-only integration (fetch documents only)
- NewsAPI: One-way read-only integration (fetch articles only)
- External LLM/Vector DB: One-way calls (no callbacks)

## Integration Patterns

**Document Ingestion Pipeline:**
1. Document upload via Streamlit UI (`src/ui/streamlit_app_agent.py`)
2. Or Confluence fetch via `src/confluence_loader.py`
3. Chunking: `src/embeddings.py` (RecursiveCharacterTextSplitter)
4. Embedding: HuggingFace or Google embeddings
5. Storage: FAISS (local) or Pinecone (cloud)

**Agent Tool Execution:**
1. Web search: DuckDuckGo or Tavily
2. News search: NewsAPI or Google News RSS
3. Web browsing: Playwright + Beautiful Soup
4. Code execution: RestrictedPython sandbox
5. All results logged via OpenTelemetry

**Session Persistence:**
1. Agent state checkpointed to PostgreSQL via LangGraph
2. Messages stored in PostgreSQL backend
3. Episodic memory stored in PostgreSQL
4. Optional Redis queue for distributed agents

---

*Integration audit: 2026-02-09*
