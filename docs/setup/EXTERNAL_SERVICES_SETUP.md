# External Services Setup for Full Tech Stack

**Date:** 2026-02-03
**Purpose:** Deploy to Streamlit Cloud with PostgreSQL and Redis

---

## 🎯 Overview

This guide walks you through setting up external services to enable the full tech stack on Streamlit Cloud:

- ✅ PostgreSQL (via Supabase) - Persistent session storage
- ✅ Redis (via Upstash) - Distributed task queue
- ✅ Streamlit Cloud - Web hosting

---

## 1️⃣ PostgreSQL Setup (Supabase)

### Step 1: Create Supabase Account

1. Go to: https://supabase.com/
2. Click "Start your project"
3. Sign up with GitHub (recommended)

### Step 2: Create New Project

1. Click "New Project"
2. Fill in details:
   - **Name:** `rag-chatbot`
   - **Database Password:** (generate strong password)
   - **Region:** Choose closest to you
   - **Pricing:** Free tier
3. Click "Create new project"
4. Wait 2-3 minutes for provisioning

### Step 3: Get Connection String

1. Go to **Project Settings** (gear icon)
2. Navigate to **Database** section
3. Scroll to "Connection string"
4. Copy the **URI** format:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```
5. Replace `[YOUR-PASSWORD]` with your actual password

### Step 4: Initialize Database Schema

Run these SQL commands in Supabase SQL Editor:

```sql
-- Create sessions table for conversation history
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create messages table for conversation messages
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create checkpoints table for agent state
CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id ON checkpoints(thread_id);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Step 5: Test Connection

```bash
# Install psql (if not installed)
# brew install postgresql (macOS)
# apt-get install postgresql-client (Linux)

# Test connection
psql "postgresql://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres"

# Should connect successfully and show postgres prompt
```

---

## 2️⃣ Redis Setup (Upstash)

### Step 1: Create Upstash Account

1. Go to: https://upstash.com/
2. Click "Get Started"
3. Sign up with GitHub (recommended)

### Step 2: Create Redis Database

1. Click "Create database"
2. Fill in details:
   - **Name:** `rag-chatbot-queue`
   - **Type:** Regional (free)
   - **Region:** Choose closest to you
   - **TLS:** Enabled (recommended)
3. Click "Create"

### Step 3: Get Connection String

1. Click on your newly created database
2. Scroll to "REST API" section
3. Copy the **Redis URL**:
   ```
   redis://default:YOUR_TOKEN@xxxxx.upstash.io:6379
   ```

### Step 4: Test Connection

```bash
# Install redis-cli
# brew install redis (macOS)
# apt-get install redis-tools (Linux)

# Test connection
redis-cli -u "redis://default:YOUR_TOKEN@xxxxx.upstash.io:6379"

# Should connect and show redis prompt
# Try: PING
# Should return: PONG
```

---

## 3️⃣ Configure Local Environment

Update your `.env` file:

```bash
# ===== ENABLE FULL TECH STACK =====

# PostgreSQL (Supabase)
USE_POSTGRES=true
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres

# Redis (Upstash)
USE_REDIS_QUEUE=true
REDIS_URL=redis://default:YOUR_TOKEN@xxxxx.upstash.io:6379

# NewsAPI
NEWSAPI_KEY=your_newsapi_key_here

# Groq LLM
GROQ_API_KEY=your_groq_key_here
```

---

## 4️⃣ Configure Streamlit Cloud Secrets

Go to: https://share.streamlit.io/ → Your App → Settings → Secrets

Add these secrets:

```toml
# LLM Configuration
LLM_PROVIDER = "groq"
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_API_KEY = "your_groq_api_key_here"

EMBEDDING_PROVIDER = "huggingface"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# NewsAPI
NEWSAPI_KEY = "your_newsapi_key_here"

# PostgreSQL (Supabase) - ENABLE
USE_POSTGRES = "true"
DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres"

# Redis (Upstash) - ENABLE
USE_REDIS_QUEUE = "true"
REDIS_URL = "redis://default:YOUR_TOKEN@xxxxx.upstash.io:6379"

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
```

---

## 5️⃣ Test Locally Before Deploying

### Update .env

```bash
USE_POSTGRES=true
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres

USE_REDIS_QUEUE=true
REDIS_URL=redis://default:YOUR_TOKEN@xxxxx.upstash.io:6379
```

### Run Locally

```bash
streamlit run src/ui/streamlit_app_agent.py
```

### Test Features

**PostgreSQL (Session Storage):**
1. Start a conversation
2. Close the app
3. Restart the app
4. Conversation history should persist ✅

**Redis (Task Queue):**
1. Check Redis connection in logs
2. Should see: "✓ Redis connected"

**Check Supabase Dashboard:**
1. Go to Table Editor
2. Should see `sessions` and `messages` tables
3. Should see your conversation data

---

## 6️⃣ Deploy to Streamlit Cloud

### Prerequisites Checklist

- ✅ Supabase database created
- ✅ Database schema initialized
- ✅ Upstash Redis created
- ✅ Connection strings copied
- ✅ Tested locally successfully
- ✅ Secrets added to Streamlit Cloud

### Deploy

1. Push code to GitHub (if not already):
   ```bash
   git push origin main
   ```

2. Go to Streamlit Cloud dashboard
3. Click "Reboot" to restart with new secrets
4. Wait 2-3 minutes for build

### Verify Deployment

**Check logs for:**
```
✓ PostgreSQL connected to: db.xxxxx.supabase.co
✓ Redis connected to: xxxxx.upstash.io
✓ Session storage: PostgreSQL
✓ All tools initialized successfully
```

**Test in app:**
1. Start a conversation
2. Check Supabase dashboard - should see new session
3. Refresh page - conversation should persist ✅

---

## 🎯 What You Get With Full Tech Stack

### Without External Services (In-Memory)
- ❌ Sessions reset on app restart
- ❌ No conversation history persistence
- ❌ No distributed task processing
- ✅ Simple and free

### With External Services (PostgreSQL + Redis)
- ✅ Sessions persist across restarts
- ✅ Conversation history saved permanently
- ✅ Multi-user support with separate sessions
- ✅ Distributed task processing
- ✅ Scalable architecture
- ⚠️ Requires external service management

---

## 📊 Service Limits (Free Tier)

### Supabase (PostgreSQL)
- **Database size:** 500MB
- **Bandwidth:** 5GB/month
- **API requests:** Unlimited
- **Projects:** 2 projects
- **Auto-pause:** After 7 days inactivity

### Upstash (Redis)
- **Commands:** 10,000/day
- **Storage:** 256MB
- **Bandwidth:** 200MB/day
- **Databases:** Unlimited
- **Auto-delete:** Never (unless manual delete)

### Streamlit Cloud
- **RAM:** 1GB
- **Storage:** 800MB (ephemeral)
- **Apps:** 3 public apps
- **Viewers:** Unlimited

---

## ⚠️ Important Notes

### Security

1. **Never commit secrets to git**
   - ✅ API keys in .env (already in .gitignore)
   - ✅ Secrets in Streamlit Cloud dashboard
   - ❌ Don't hardcode in Python files

2. **Use strong passwords**
   - Supabase database password: 20+ characters
   - Upstash tokens are auto-generated (secure)

3. **Enable SSL/TLS**
   - Supabase: Enabled by default ✅
   - Upstash: Enabled by default ✅

### Monitoring

**Supabase Dashboard:**
- Monitor database size
- Check query performance
- View table contents
- Track API usage

**Upstash Dashboard:**
- Monitor command usage
- Check memory usage
- View recent commands
- Track latency

**Streamlit Cloud:**
- Monitor app health
- Check runtime logs
- View resource usage

### Troubleshooting

**PostgreSQL Connection Error:**
```
psycopg2.OperationalError: could not connect to server
```
**Solution:**
1. Check DATABASE_URL is correct
2. Check password has no special characters (escape if needed)
3. Check Supabase project is not paused
4. Try connecting with psql from terminal

**Redis Connection Error:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```
**Solution:**
1. Check REDIS_URL is correct
2. Check Upstash database is not deleted
3. Check region matches (low latency)
4. Try connecting with redis-cli from terminal

**Session Data Not Persisting:**
1. Check USE_POSTGRES=true in secrets
2. Check database schema is initialized
3. Check Supabase logs for errors
4. Verify sessions table exists

---

## 🔗 Service Dashboards

### Supabase
- **Dashboard:** https://supabase.com/dashboard
- **Documentation:** https://supabase.com/docs
- **Status:** https://status.supabase.com/

### Upstash
- **Dashboard:** https://console.upstash.com/
- **Documentation:** https://docs.upstash.com/
- **Status:** https://upstash.com/status

### Streamlit Cloud
- **Dashboard:** https://share.streamlit.io/
- **Documentation:** https://docs.streamlit.io/deploy/streamlit-community-cloud
- **Status:** https://streamlit.statuspage.io/

---

## 💰 Cost Estimation

### Free Tier (Recommended for Starting)
- Supabase: $0/month (500MB limit)
- Upstash: $0/month (10K commands/day)
- Streamlit Cloud: $0/month (3 apps)
- **Total:** $0/month ✅

### If You Exceed Free Tier
- Supabase Pro: $25/month (8GB, no pause)
- Upstash Pay-as-you-go: ~$5-10/month
- Streamlit Cloud Team: $20/month/user
- **Total:** ~$30-55/month

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] Supabase account created
- [ ] Database provisioned and schema initialized
- [ ] Connection string tested
- [ ] Upstash account created
- [ ] Redis database created
- [ ] Redis URL tested
- [ ] All secrets copied
- [ ] Tested locally with external services

### Deployment
- [ ] Updated Streamlit Cloud secrets
- [ ] Code pushed to GitHub
- [ ] App restarted in Streamlit Cloud
- [ ] Build completed successfully
- [ ] No connection errors in logs

### Post-Deployment
- [ ] Test conversation persistence
- [ ] Check Supabase tables populated
- [ ] Monitor resource usage
- [ ] Verify all tools working
- [ ] Document any issues

---

**Last Updated:** 2026-02-03
**Status:** Ready for production deployment with full tech stack
