# LangGraph Checkpoint Storage Guide

This guide explains how to use PostgreSQL-backed checkpoint storage for crash recovery and state persistence in LangGraph workflows.

---

## 🎯 What Are Checkpoints?

**Checkpoints** automatically save the agent's state at each step of execution. This enables:

- ✅ **Crash Recovery** - Resume workflows after errors or interruptions
- ✅ **State Inspection** - Debug by viewing execution history
- ✅ **Time Travel** - Rewind to any point in the workflow
- ✅ **Branch Execution** - Try different paths from the same checkpoint
- ✅ **Audit Trail** - Complete record of agent decisions

---

## 📋 Prerequisites

1. **PostgreSQL Setup** - See [POSTGRES_SETUP.md](POSTGRES_SETUP.md) for installation
2. **Python Packages** - Checkpoint dependencies installed
3. **Database Initialized** - Run `python init_database.py`

---

## ⚙️ Configuration

### Enable Checkpointing

Edit `.env`:
```bash
# Enable PostgreSQL backend
USE_POSTGRES=true

# Enable checkpoint storage (default: true)
USE_CHECKPOINTS=true

# Connection string
DATABASE_URL=postgresql://user:password@localhost:5432/rag_chatbot
```

### Install Dependencies

```bash
pip install langgraph-checkpoint-postgres psycopg[binary]
```

---

## 🚀 Usage

### Automatic Checkpointing

When enabled, checkpoints are created automatically at each step:

```python
from src.agent.agent_executor_v3 import AgentExecutorV3

# Initialize agent with checkpointing enabled
agent = AgentExecutorV3(
    llm=llm,
    tool_registry=tool_registry,
    config=config,
    enable_checkpoints=True  # Default: True
)

# Execute with thread_id for checkpoint storage
result = agent.execute(
    query="What is machine learning?",
    thread_id="session-123"  # Unique identifier for this conversation thread
)
```

**What Happens:**
1. Agent starts execution
2. After each node (understand → route → execute → synthesize), state is checkpointed
3. If the process crashes, you can resume from the last checkpoint
4. All checkpoints are stored in PostgreSQL

### Resume from Checkpoint

If execution is interrupted:

```python
# Resume from the last checkpoint
result = agent.resume_from_checkpoint(
    thread_id="session-123"
)

# Or resume with a new query
result = agent.resume_from_checkpoint(
    thread_id="session-123",
    query="Tell me more about supervised learning"
)
```

### View Checkpoint History

```python
from src.database import get_checkpoint_manager

checkpoint_mgr = get_checkpoint_manager()

# List all checkpoints for a thread
checkpoints = checkpoint_mgr.list_checkpoints(
    thread_id="session-123",
    limit=10
)

for cp in checkpoints:
    print(f"Checkpoint ID: {cp['checkpoint_id']}")
    print(f"Created: {cp['created_at']}")
    print(f"Parent: {cp['parent_checkpoint_id']}")
```

### Get Specific Checkpoint

```python
# Get the latest checkpoint
checkpoint = checkpoint_mgr.get_checkpoint(
    thread_id="session-123"
)

# Get a specific checkpoint
checkpoint = checkpoint_mgr.get_checkpoint(
    thread_id="session-123",
    checkpoint_id="abc123"
)

print(checkpoint['state'])  # View the saved state
```

---

## 📊 Database Schema

Checkpoints are stored in two tables:

### checkpoints Table
```sql
CREATE TABLE checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    checkpoint JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (thread_id, checkpoint_id)
);
```

### checkpoint_writes Table
```sql
CREATE TABLE checkpoint_writes (
    thread_id TEXT NOT NULL,
    checkpoint_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    channel TEXT NOT NULL,
    value JSONB,
    PRIMARY KEY (thread_id, checkpoint_id, task_id, idx)
);
```

---

## 🎮 Advanced Usage

### Custom Thread IDs

Use meaningful thread IDs for better organization:

```python
# Per user session
thread_id = f"user_{user_id}_session_{session_id}"

# Per conversation
thread_id = f"conv_{conversation_id}"

# Per task
thread_id = f"task_{task_id}_{timestamp}"

result = agent.execute(query="...", thread_id=thread_id)
```

### Cleanup Old Checkpoints

```python
# Delete all checkpoints for a thread
checkpoint_mgr.delete_thread_checkpoints(thread_id="old-session")
```

### Get Full Execution History

```python
# Get complete history with all states
history = checkpoint_mgr.get_thread_history(thread_id="session-123")

for entry in history:
    print(f"Checkpoint: {entry['checkpoint_id']}")
    print(f"Time: {entry['created_at']}")
    print(f"State: {entry['state']}")
```

---

## 🔍 Debugging with Checkpoints

### Inspect Intermediate States

```python
# Get all checkpoints for debugging
checkpoints = checkpoint_mgr.list_checkpoints("session-123")

for cp in checkpoints:
    state = checkpoint_mgr.get_checkpoint(
        thread_id="session-123",
        checkpoint_id=cp['checkpoint_id']
    )

    print(f"\nStep: {cp['checkpoint_id']}")
    print(f"Phase: {state.get('current_phase')}")
    print(f"Tool: {state.get('selected_tool')}")
    print(f"Answer: {state.get('final_answer')[:100]}")
```

### Time Travel Debugging

```python
# Go back to a specific point
checkpoint = checkpoint_mgr.get_checkpoint(
    thread_id="session-123",
    checkpoint_id="step-3"
)

# Modify state and re-execute
modified_state = checkpoint['state'].copy()
modified_state['selected_tool'] = 'different_tool'

# Resume with modified state
config = {"configurable": {"thread_id": "session-123-debug"}}
result = agent.graph.invoke(modified_state, config=config)
```

---

## 🔧 Troubleshooting

### Checkpointing Not Working

```python
# Check if checkpointing is available
if agent.checkpoint_manager and agent.checkpoint_manager.is_available():
    print("✅ Checkpointing enabled")
else:
    print("❌ Checkpointing disabled")
    # Check logs for errors
```

**Common Issues:**
1. `USE_POSTGRES=false` in .env
2. `USE_CHECKPOINTS=false` in .env
3. PostgreSQL not running
4. Database not initialized
5. Missing dependencies

### View Checkpoint Tables

```sql
-- Check if tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE 'checkpoint%';

-- Count checkpoints
SELECT thread_id, COUNT(*) as checkpoint_count
FROM checkpoints
GROUP BY thread_id
ORDER BY checkpoint_count DESC;

-- Recent checkpoints
SELECT thread_id, checkpoint_id, created_at
FROM checkpoints
ORDER BY created_at DESC
LIMIT 10;
```

### Clear All Checkpoints

```sql
-- Delete all checkpoint data
TRUNCATE TABLE checkpoint_writes;
TRUNCATE TABLE checkpoints;
```

---

## 💡 Best Practices

### 1. Use Meaningful Thread IDs

```python
# ✅ Good
thread_id = f"user_123_session_456"

# ❌ Bad
thread_id = str(random.randint(1, 1000000))
```

### 2. Clean Up Old Checkpoints

```python
# Regular cleanup
from datetime import datetime, timedelta

# Delete checkpoints older than 7 days
cutoff_date = datetime.now() - timedelta(days=7)
# Implement cleanup logic
```

### 3. Handle Errors Gracefully

```python
try:
    result = agent.execute(query="...", thread_id=thread_id)
except Exception as e:
    print(f"Execution failed: {e}")
    print("Will resume from last checkpoint on retry")

    # Retry from checkpoint
    result = agent.resume_from_checkpoint(thread_id=thread_id)
```

### 4. Monitor Checkpoint Size

```sql
-- Check checkpoint storage size
SELECT
    thread_id,
    COUNT(*) as checkpoints,
    pg_size_pretty(SUM(pg_column_size(checkpoint))) as total_size
FROM checkpoints
GROUP BY thread_id
ORDER BY SUM(pg_column_size(checkpoint)) DESC
LIMIT 10;
```

---

## 📈 Performance Considerations

### Checkpoint Overhead

Each checkpoint adds:
- **~1-2ms** per save operation
- **~100-500 bytes** per checkpoint
- **Network latency** to PostgreSQL

### Optimization Tips

1. **Use Local PostgreSQL** for development
2. **Use Connection Pooling** (automatically handled)
3. **Clean Up Old Checkpoints** regularly
4. **Use Indexes** (automatically created)

### Disable for High-Throughput

If not needed:
```python
# Disable checkpointing for better performance
agent = AgentExecutorV3(
    llm=llm,
    tool_registry=tool_registry,
    config=config,
    enable_checkpoints=False  # Disable for high-throughput scenarios
)
```

---

## 🌐 Cloud Deployment

### Heroku Postgres

```bash
# Heroku automatically provides DATABASE_URL
# Just enable checkpointing
heroku config:set USE_POSTGRES=true
heroku config:set USE_CHECKPOINTS=true
```

### Supabase

```bash
# Get connection string from Supabase dashboard
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
USE_POSTGRES=true
USE_CHECKPOINTS=true
```

### Railway

```bash
# Railway provides PostgreSQL connection string
DATABASE_URL=${{Postgres.DATABASE_URL}}
USE_POSTGRES=true
USE_CHECKPOINTS=true
```

---

## 🆘 Getting Help

**Checkpoint not saving?**
1. Check `USE_POSTGRES=true` and `USE_CHECKPOINTS=true`
2. Verify PostgreSQL connection
3. Run `python init_database.py`
4. Check logs for errors

**Can't resume?**
1. Verify thread_id matches
2. Check if checkpoint exists
3. Ensure database tables exist

**Performance issues?**
1. Use local PostgreSQL for dev
2. Enable connection pooling
3. Clean up old checkpoints
4. Consider disabling for batch jobs

---

*Last updated: 2026-02-03*
