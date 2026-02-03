# Backend Services Status

**Generated:** 2026-02-03
**System:** RAG Agent

---

## Current Configuration

### ✅ Active Services

| Service | Status | Details |
|---------|--------|---------|
| **FAISS Vector Store** | ✅ Active | 64.5 KB index, 33.4 KB metadata |
| **Policy Engine** | ✅ Active | 14 policy rules loaded |
| **File Persistence** | ✅ Active | 2 episodic memory sessions saved |

### ⚠️ Configured But Not Connected

| Service | Status | Issue |
|---------|--------|-------|
| **PostgreSQL** | ⚠️ Configured but disconnected | Module missing: `psycopg2` not installed |

### ⚪ Not Configured (Using Defaults)

| Service | Status | Using Instead |
|---------|--------|---------------|
| **Redis Queue** | ⚪ Disabled | Direct execution (no queue) |
| **Pinecone** | ⚪ Disabled | FAISS local vector store |
| **OpenTelemetry** | ⚪ Disabled | No observability tracing |

---

## How to Enable Each Service

### 1. PostgreSQL (Currently: Configured but not working)

**What it's used for:** Persistent session storage, checkpoint recovery, policy violation logs

**Current Issue:** Module not installed

**Fix:**
```bash
pip install psycopg2-binary
# Or
pip install psycopg[binary]
```

**Verify in .env:**
```bash
USE_POSTGRES=true
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rag_chatbot
```

**Initialize database:**
```bash
# Start PostgreSQL
brew services start postgresql@15  # macOS
# or
sudo systemctl start postgresql    # Linux

# Create database
createdb rag_chatbot

# Run migrations
python init_database.py
```

**Verify:**
```bash
python check_backend_status.py
```

---

### 2. Redis Queue (Currently: Disabled)

**What it's used for:** Async task processing, distributed agent coordination, background workers

**Enable:**
```bash
# 1. Install and start Redis
brew install redis            # macOS
brew services start redis

# Or with Docker
docker run -d -p 6379:6379 redis:alpine

# 2. Update .env
echo "USE_REDIS_QUEUE=true" >> .env

# 3. Start background worker
python queue_worker.py
```

**Verify:**
```bash
redis-cli ping  # Should return "PONG"
python check_backend_status.py
```

**Usage in code:**
```python
from src.queue import TaskQueue, TaskPriority

queue = TaskQueue()
task_id = queue.submit_task(
    query="What is RAG?",
    priority=TaskPriority.HIGH
)
result = queue.get_result(task_id, timeout=60)
```

---

### 3. Pinecone (Currently: Disabled, using FAISS)

**What it's used for:** Cloud vector database, production-grade scaling, multi-tenancy

**Enable:**
```bash
# 1. Get API key from https://app.pinecone.io

# 2. Update .env
echo "USE_PINECONE=true" >> .env
echo "PINECONE_API_KEY=your_key_here" >> .env
echo "PINECONE_INDEX_NAME=rag-agent" >> .env
echo "PINECONE_REGION=us-east-1" >> .env

# 3. Migrate existing FAISS data (optional)
python migrate_to_pinecone.py
```

**Verify:**
```bash
python check_backend_status.py
```

**When to use:**
- FAISS: Development, < 1M vectors, single server
- Pinecone: Production, > 1M vectors, distributed, auto-scaling

---

### 4. OpenTelemetry Observability (Currently: Disabled)

**What it's used for:** Distributed tracing, performance monitoring, bottleneck detection

**Enable with Jaeger (easiest):**
```bash
# 1. Start Jaeger
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  jaegertracing/all-in-one:latest

# 2. Update .env
echo "ENABLE_OBSERVABILITY=true" >> .env
echo "OTEL_EXPORTER_TYPE=otlp" >> .env
echo "OTEL_EXPORTER_ENDPOINT=http://localhost:4317" >> .env
echo "OTEL_SERVICE_NAME=rag-agent" >> .env

# 3. View traces at http://localhost:16686
```

**Verify:**
```bash
python check_backend_status.py
# Then ask a question in the UI and check Jaeger UI
```

**What you'll see:**
- RAG query end-to-end latency
- Document retrieval time
- LLM generation time
- Tool execution traces
- Error tracking

---

## Quick Commands Reference

### Check all backend status
```bash
python check_backend_status.py
```

### Check individual services

**PostgreSQL:**
```bash
psql -U postgres -d rag_chatbot -c "SELECT COUNT(*) FROM sessions;"
```

**Redis:**
```bash
redis-cli ping
redis-cli INFO
redis-cli KEYS "rag:queue:*"
```

**FAISS:**
```bash
ls -lh data/vector_store/
```

**Pinecone:**
```bash
# Install pinecone CLI (if available) or use Python
python -c "from pinecone import Pinecone; pc = Pinecone(api_key='your_key'); print(pc.list_indexes())"
```

---

## What's Actually Running Right Now

Based on your current `.env` configuration:

```
✅ ACTIVE:
   - FAISS local vector store (64.5 KB index)
   - Policy Engine (14 rules enforcing behavior)
   - Groq LLM (llama-3.3-70b-versatile)
   - HuggingFace embeddings (local)
   - Episodic memory (2 sessions persisted to disk)

⚠️ CONFIGURED BUT BROKEN:
   - PostgreSQL (configured but psycopg2 not installed)

⚪ NOT ENABLED:
   - Redis queue (using direct execution)
   - Pinecone (using FAISS instead)
   - OpenTelemetry (no observability)
   - Learning module persistence (not initialized yet)
   - Reflections (no entries yet)
```

---

## Performance Impact

| Service | Memory | Startup Time | When Needed |
|---------|--------|--------------|-------------|
| FAISS | ~100 MB | Instant | Always (default) |
| PostgreSQL | ~50 MB | +0.5s | Session persistence, checkpoints |
| Redis | ~30 MB | +0.2s | Background tasks, scaling |
| Pinecone | 0 MB (cloud) | +1-2s | Production, > 1M vectors |
| OpenTelemetry | ~20 MB | +0.3s | Debugging, monitoring |

**Current memory footprint:** ~150 MB (FAISS + LLM + embeddings)
**With all services:** ~250 MB

---

## Troubleshooting

### PostgreSQL says "USE_POSTGRES=true" but won't connect

**Issue:** Module not installed
**Fix:** `pip install psycopg2-binary` or `pip install psycopg[binary]`

### Redis connection refused

**Issue:** Redis not running
**Fix:** `brew services start redis` or `docker run -d -p 6379:6379 redis:alpine`

### Jaeger traces not appearing

**Issue:** Wrong endpoint or Jaeger not running
**Fix:**
```bash
docker ps | grep jaeger  # Check if running
docker logs jaeger       # Check for errors
```

### FAISS "Vector store not initialized"

**Issue:** No documents uploaded yet (or old bug before commit af1b006)
**Fix:** Upload documents in UI or pull latest code

---

## See Also

- [PERSISTENCE_BUGS_ANALYSIS.md](PERSISTENCE_BUGS_ANALYSIS.md) - Recent persistence fixes
- [POLICY_ENGINE_GUIDE.md](POLICY_ENGINE_GUIDE.md) - Policy configuration
- [REDIS_QUEUE_GUIDE.md](REDIS_QUEUE_GUIDE.md) - Queue setup
- [OBSERVABILITY_GUIDE.md](OBSERVABILITY_GUIDE.md) - Monitoring setup
- [POSTGRES_SETUP.md](POSTGRES_SETUP.md) - Database setup
- [PINECONE_MIGRATION_GUIDE.md](PINECONE_MIGRATION_GUIDE.md) - Cloud vector store migration

---

**Last Updated:** 2026-02-03
