# Streamlit Cloud Deployment Guide

**Date:** 2026-02-03
**Status:** Ready for deployment

This guide explains how to deploy your RAG chatbot to Streamlit Cloud.

---

## ⚠️ Critical: Database Configuration

### PostgreSQL & Redis Status

**Local Development:**
- PostgreSQL: Used for persistent session storage
- Redis: Not used (optional for distributed tasks)

**Streamlit Cloud:**
- ❌ No built-in PostgreSQL database
- ❌ No built-in Redis server
- ✅ App works perfectly with in-memory storage

### Required Configuration

**In your Streamlit Cloud secrets, set:**
```toml
# Disable PostgreSQL/Redis for Streamlit Cloud
USE_POSTGRES = "false"
USE_REDIS_QUEUE = "false"

# API Keys (required)
NEWSAPI_KEY = "your_newsapi_key_here"
GROQ_API_KEY = "your_groq_key_here"
```

---

## 🚀 Deployment Steps

### 1. Push Code to GitHub
```bash
git push origin main
```
✅ **Already done!** Your code is at: https://github.com/ar-aishwaryanand-glitch/rag-chatbot.git

### 2. Configure Streamlit Cloud Secrets

Go to: https://share.streamlit.io/ → Your App → Settings → Secrets

**Add these secrets:**
```toml
# Core Configuration
LLM_PROVIDER = "groq"
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_API_KEY = "your_groq_api_key_here"

EMBEDDING_PROVIDER = "huggingface"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# NewsAPI (optional but recommended)
NEWSAPI_KEY = "your_newsapi_key_here"

# Agent Settings
AGENT_ENABLED = "true"
AGENT_MODE = "hybrid"
AGENT_MAX_ITERATIONS = "10"
AGENT_TIMEOUT = "120"

# Memory Settings
MEMORY_ENABLED = "true"
MEMORY_WINDOW_SIZE = "10"
MEMORY_SUMMARY_FREQUENCY = "5"

# Tool Settings
WEB_SEARCH_ENABLED = "true"
WEB_SEARCH_PROVIDER = "duckduckgo"
CALCULATOR_ENABLED = "true"
CODE_EXECUTOR_ENABLED = "false"
FILE_OPS_ENABLED = "true"

# Safety Settings
CODE_EXECUTION_TIMEOUT = "5"
REFLECTION_ENABLED = "true"
HALLUCINATION_DETECTION = "false"

# Database - IMPORTANT: Disable for Streamlit Cloud
USE_POSTGRES = "false"
USE_REDIS_QUEUE = "false"
```

### 3. Deploy

Streamlit Cloud will automatically:
1. Detect your GitHub push
2. Install dependencies from `requirements.txt`
3. Start your app at `src/ui/streamlit_app_agent.py`
4. Build typically takes 2-3 minutes

### 4. Verify Deployment

After deployment, test these features:
- ✅ Basic RAG queries
- ✅ News search with filtering
- ✅ Web search
- ✅ Multi-tool agent operations
- ✅ Memory and conversation history (in-memory)

---

## 📦 What Gets Deployed

### Dependencies (from requirements.txt)
```
✅ langchain & langchain-groq (LLM)
✅ sentence-transformers (embeddings)
✅ chromadb (vector database)
✅ streamlit (UI)
✅ newsapi-python (news integration)
✅ feedparser (RSS feeds)
✅ playwright (web scraping - may have issues)
```

### Features Available on Streamlit Cloud

| Feature | Status | Notes |
|---------|--------|-------|
| RAG queries | ✅ Works | Uses in-memory ChromaDB |
| News search | ✅ Works | NewsAPI + relevance filtering |
| Web search | ✅ Works | DuckDuckGo search |
| Calculator | ✅ Works | Math operations |
| Code executor | ⚠️ Limited | Disabled by default (security) |
| File operations | ✅ Works | Ephemeral storage |
| Web scraping | ⚠️ Limited | Playwright may not work on Cloud |
| Memory | ✅ Works | In-memory (resets on restart) |
| Session storage | ⚠️ Ephemeral | Lost on app restart |

---

## ⚠️ Limitations on Streamlit Cloud

### 1. No Playwright (Web Scraping)

**Problem:** Playwright requires Chromium browser installation
**Impact:** `web_agent` tool won't work
**Solution:** Use `news_api` tool instead for news (already implemented!)

**Status Check:**
```python
# In your app
from src.agent.tools import WebAgentTool
web_agent = WebAgentTool()
if not web_agent.available:
    print("Web agent disabled - using news_api instead")
```

### 2. Ephemeral Storage

**Problem:** Files stored on disk are deleted on app restart
**Impact:**
- Uploaded documents disappear after restart
- Vector database resets on restart
- Conversation history lost on restart

**Solutions:**
- Use external vector DB (Pinecone, Weaviate)
- Use external PostgreSQL (see Option 2 below)
- Accept ephemeral nature for free tier

### 3. Memory Limits

**Limits:**
- 1GB RAM (free tier)
- 800MB disk space
- 10-minute execution timeout

**Solutions:**
- Keep vector databases small (<1000 documents)
- Use lightweight models
- Optimize memory usage

### 4. App Restarts

**When app restarts:**
- Idle for 7 days
- Code changes (automatic redeploy)
- Manual restart by user
- Streamlit Cloud maintenance

**What gets reset:**
- In-memory conversation history
- Uploaded documents
- Vector database contents
- Session data

---

## 🔧 Advanced Options

### Option 2: Use External PostgreSQL (If Needed)

If you need persistent storage, use a free external database:

#### Recommended Providers:
1. **Supabase** (Recommended)
   - Free tier: 500MB database
   - Setup: https://supabase.com/
   ```toml
   USE_POSTGRES = "true"
   DATABASE_URL = "postgresql://user:pass@db.supabase.co:5432/postgres"
   ```

2. **Neon** (Serverless PostgreSQL)
   - Free tier: 3GB storage
   - Setup: https://neon.tech/
   ```toml
   USE_POSTGRES = "true"
   DATABASE_URL = "postgresql://user:pass@ep-xxx.neon.tech/neondb"
   ```

3. **ElephantSQL**
   - Free tier: 20MB
   - Setup: https://www.elephantsql.com/
   ```toml
   USE_POSTGRES = "true"
   DATABASE_URL = "postgresql://user:pass@server.elephantsql.com/dbname"
   ```

#### Enable in Streamlit Secrets:
```toml
USE_POSTGRES = "true"
DATABASE_URL = "postgresql://user:password@host:port/database"
```

### Option 3: Use External Redis (If Needed)

For distributed task processing (not currently used):

1. **Redis Cloud** (Recommended)
   - Free tier: 30MB
   - Setup: https://redis.com/try-free/
   ```toml
   USE_REDIS_QUEUE = "true"
   REDIS_URL = "redis://default:password@redis-xxxxx.redis.cloud:12345"
   ```

2. **Upstash** (Serverless Redis)
   - Free tier: 10K commands/day
   - Setup: https://upstash.com/
   ```toml
   USE_REDIS_QUEUE = "true"
   REDIS_URL = "redis://default:password@xxxxx.upstash.io:6379"
   ```

---

## 🧪 Testing Before Deployment

### Local Test with Cloud Settings

1. Update `.streamlit/secrets.toml`:
   ```toml
   USE_POSTGRES = "false"
   USE_REDIS_QUEUE = "false"
   ```

2. Run locally:
   ```bash
   streamlit run src/ui/streamlit_app_agent.py
   ```

3. Test all features:
   - RAG queries
   - News search
   - Web search
   - Calculator
   - File operations

### Expected Behavior:
```
✓ App starts successfully
✓ No PostgreSQL connection errors
✓ No Redis connection errors
✓ All tools work except web_agent (Playwright)
✓ News queries use news_api tool
✓ Memory works (in-memory)
```

---

## 📊 Monitoring

### Check App Health

After deployment, monitor:

**In Streamlit Cloud Dashboard:**
- App status (running/stopped/error)
- Build logs (dependency installation)
- Runtime logs (errors, warnings)
- Resource usage (RAM, CPU)

**In Your App:**
- Check tool availability:
  ```python
  st.sidebar.write("Available Tools:")
  for tool in tool_registry.list_tools():
      st.sidebar.write(f"- {tool.name}: {'✓' if tool.available else '✗'}")
  ```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| App crashes on startup | PostgreSQL connection error | Set `USE_POSTGRES=false` |
| "Playwright not available" | Chromium not installed | Use `news_api` instead of `web_agent` |
| "Out of memory" | ChromaDB too large | Reduce document count |
| App restarts frequently | Idle timeout | Accept for free tier |

---

## 🎯 Recommended Configuration for Streamlit Cloud

**Minimal, Reliable Setup:**
```toml
# LLM
LLM_PROVIDER = "groq"
GROQ_API_KEY = "your_key"
GROQ_MODEL = "llama-3.3-70b-versatile"

# Embeddings
EMBEDDING_PROVIDER = "huggingface"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# NewsAPI
NEWSAPI_KEY = "your_key"

# Database - DISABLE
USE_POSTGRES = "false"
USE_REDIS_QUEUE = "false"

# Tools
WEB_SEARCH_ENABLED = "true"
CALCULATOR_ENABLED = "true"
CODE_EXECUTOR_ENABLED = "false"
FILE_OPS_ENABLED = "true"

# Agent
AGENT_ENABLED = "true"
MEMORY_ENABLED = "true"
```

This configuration:
- ✅ Works reliably on free tier
- ✅ No external services needed (except APIs)
- ✅ All major features work
- ✅ Fast and responsive
- ⚠️ No persistent storage (acceptable for most use cases)

---

## 📝 Summary

### ✅ Ready for Deployment

- Code pushed to GitHub
- PostgreSQL disabled (in-memory storage)
- Redis disabled (not needed)
- All dependencies in requirements.txt
- NewsAPI configured

### 🎯 Next Steps

1. **Add secrets to Streamlit Cloud** (required)
2. **Click "Deploy"** in Streamlit Cloud dashboard
3. **Wait 2-3 minutes** for build
4. **Test deployed app**

### ⚠️ Remember

- **DO NOT** enable PostgreSQL unless using external database
- **DO NOT** enable Redis unless using external service
- **Expect** app to reset on idle/restart (free tier behavior)
- **Use** `news_api` instead of `web_agent` for news

---

## 🔗 Useful Links

- **Your GitHub Repo:** https://github.com/ar-aishwaryanand-glitch/rag-chatbot
- **Streamlit Cloud:** https://share.streamlit.io/
- **Groq Console:** https://console.groq.com/
- **NewsAPI Dashboard:** https://newsapi.org/account

---

**Last Updated:** 2026-02-03
