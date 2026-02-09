# Database & Persistence Documentation

## Overview

The system uses **PostgreSQL** (via Supabase) for persistent storage of:
1. **LangGraph Checkpoints**: Agent state persistence
2. **Conversation Sessions**: Multi-user session tracking
3. **Messages**: Complete conversation history
4. **Episodic Memory**: Long-term user preferences and patterns
5. **Statistics**: Usage metrics and analytics

## Architecture

```
Agent Execution
     ↓
CheckpointBackend (LangGraph state persistence)
     ↓
[PostgreSQL - checkpoints table]

SessionManager (High-level interface)
     ↓
PostgresBackend (Low-level operations)
     ↓
[PostgreSQL - sessions, messages, memories, stats tables]
```

## Database Schema

### Tables

#### 1. checkpoints (LangGraph)
```sql
CREATE TABLE checkpoints (
    thread_id TEXT,
    checkpoint_id TEXT,
    parent_checkpoint_id TEXT,
    checkpoint BYTEA,           -- Serialized agent state
    metadata JSONB,
    created_at TIMESTAMP,
    checkpoint_ns TEXT,
    PRIMARY KEY (thread_id, checkpoint_id)
);
```

**Purpose**: Store agent execution state for resume/recovery.

#### 2. sessions
```sql
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY,
    user_id TEXT,               -- Optional user identifier
    title TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

**Purpose**: Track individual conversation sessions.

#### 3. messages
```sql
CREATE TABLE messages (
    message_id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(session_id),
    role TEXT,                  -- 'user', 'assistant', 'system'
    content TEXT,
    timestamp TIMESTAMP,
    tool_calls JSONB,           -- Tools used in this message
    sources JSONB               -- Sources referenced
);
```

**Purpose**: Store complete conversation history.

#### 4. episodic_memories
```sql
CREATE TABLE episodic_memories (
    memory_id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(session_id),
    memory_type TEXT,           -- 'conversation', 'fact', 'preference', 'task'
    content TEXT,
    importance FLOAT,           -- 0.0 to 1.0
    timestamp TIMESTAMP,
    metadata JSONB
);
```

**Purpose**: Store long-term patterns and learnings.

#### 5. session_stats
```sql
CREATE TABLE session_stats (
    session_id UUID PRIMARY KEY REFERENCES sessions(session_id),
    total_messages INTEGER,
    total_tokens INTEGER,
    tools_used JSONB,           -- Tool usage counts
    success_rate FLOAT,
    last_activity TIMESTAMP
);
```

**Purpose**: Track session metrics and usage.

## Checkpoint Backend

**File**: [src/database/checkpoint_backend.py](../src/database/checkpoint_backend.py)

Manages LangGraph checkpoint storage for agent state persistence.

### CheckpointManager

```python
class CheckpointManager:
    connection_string: str
    enabled: bool
    checkpoint_saver: PostgresSaver  # LangGraph's PostgreSQL saver
    _saver_context: ContextManager   # For proper cleanup
```

### Key Features

#### 1. Automatic State Persistence

```python
# Agent executes with thread_id
agent.execute(
    query="What is machine learning?",
    thread_id="user_123"
)

# After execution:
# → Full agent state saved to checkpoints table
# → Includes conversation_messages, tools_used, final_answer, etc.
```

#### 2. State Recovery

```python
# Next query with SAME thread_id
agent.execute(
    query="Can you elaborate?",
    thread_id="user_123"  # SAME ID
)

# On execution start:
# → Checkpoint loaded from database
# → conversation_messages restored
# → Agent has full conversation context!
```

#### 3. Checkpoint Lifecycle

```
Query 1 (thread_id="abc"):
├─ Initialize state with conversation_messages=None
├─ Execute agent phases
├─ Update conversation_messages in state
└─ Save checkpoint with full state

Query 2 (thread_id="abc"):
├─ Load checkpoint for thread_id="abc"
├─ Restore conversation_messages from state
├─ Continue execution with context
└─ Update and save checkpoint
```

### Usage

```python
from src.database.checkpoint_backend import get_checkpoint_manager

# Get global checkpoint manager
checkpoint_mgr = get_checkpoint_manager()

# Check availability
if checkpoint_mgr.is_available():
    print("✅ Checkpoint storage ready")

# Get checkpointer for agent
checkpointer = checkpoint_mgr.get_checkpointer()

# List checkpoints for thread
checkpoints = checkpoint_mgr.list_checkpoints(
    thread_id="user_123",
    limit=10
)

for cp in checkpoints:
    print(f"Checkpoint: {cp['checkpoint_id']}")
    print(f"Created: {cp['created_at']}")

# Get specific checkpoint
checkpoint_data = checkpoint_mgr.get_checkpoint(
    thread_id="user_123",
    checkpoint_id="abc123..."
)

# Delete thread checkpoints
checkpoint_mgr.delete_thread_checkpoints("user_123")

# Close (cleanup)
checkpoint_mgr.close()
```

### Integration with Agent

```python
class AgentExecutorV3:
    def __init__(self, ...):
        self.checkpoint_manager = get_checkpoint_manager()

    def execute(self, query: str, thread_id: str, ...):
        # Prepare config with thread_id
        config = {}
        if thread_id and self.checkpoint_manager.is_available():
            config = {"configurable": {"thread_id": thread_id}}

        # LangGraph will automatically:
        # 1. Load checkpoint for thread_id (if exists)
        # 2. Execute agent with restored state
        # 3. Save updated checkpoint after execution

        result = self.graph.invoke(initial_state, config=config)
        return result
```

### Checkpoint Content

```python
{
    'thread_id': 'user_123',
    'checkpoint_id': 'abc123...',
    'parent_checkpoint_id': 'xyz789...',
    'checkpoint': b'...',  # Serialized state
    'metadata': {},
    'created_at': '2026-02-04T10:30:00',
    'checkpoint_ns': ''
}

# Deserialized state contains:
{
    'query': 'Can you elaborate?',
    'final_answer': 'Machine learning is...',
    'conversation_messages': [
        {'role': 'user', 'content': 'What is ML?', ...},
        {'role': 'assistant', 'content': 'ML is...', ...},
        # ... full history
    ],
    'tools_used': ['document_search'],
    'memory_context': '[Recent conversation]...',
    # ... all agent state fields
}
```

## Session Manager

**File**: [src/database/session_manager.py](../src/database/session_manager.py)

High-level interface for session management, messages, and memory.

### SessionManager

```python
class SessionManager:
    backend: PostgresBackend  # Low-level database operations
    enabled: bool             # Is PostgreSQL available?
```

### Session Operations

#### Create Session

```python
from src.database.session_manager import SessionManager

session_mgr = SessionManager()

# Create new session
session_id = session_mgr.create_session(
    user_id="alice@example.com",
    title="ML Discussion"
)
# Returns: "550e8400-e29b-41d4-a716-446655440000"
```

#### List Sessions

```python
# Get all sessions for user
sessions = session_mgr.list_sessions(
    user_id="alice@example.com",
    limit=20
)

# Returns:
[
    {
        'session_id': '...',
        'title': 'ML Discussion',
        'created_at': datetime(...),
        'updated_at': datetime(...),
        'message_count': 8,
        'is_active': True
    },
    # ...
]
```

#### Restore Session

```python
# Restore complete session
session_data = session_mgr.restore_session(session_id)

# Returns:
{
    'session': {
        'id': '...',
        'title': 'ML Discussion',
        'created_at': '2026-02-04T10:00:00',
        'updated_at': '2026-02-04T10:30:00'
    },
    'conversation': [
        {'role': 'user', 'content': 'What is ML?', 'timestamp': '...', 'sources': []},
        {'role': 'assistant', 'content': 'ML is...', 'timestamp': '...', 'sources': [...]},
        # ... full history
    ],
    'memories': [
        {'type': 'preference', 'content': 'User prefers technical depth', 'importance': 0.8},
        # ...
    ],
    'stats': {
        'total_messages': 8,
        'tools_used': {'document_search': 3, 'web_search': 1},
        'success_rate': 0.95
    }
}
```

#### Update and Delete

```python
# Update title
session_mgr.update_session_title(session_id, "New Title")

# Delete session (and all related data)
session_mgr.delete_session(session_id)
```

### Message Operations

#### Log Messages

```python
# Log user message
session_mgr.log_message(
    session_id=session_id,
    role="user",
    content="What is machine learning?"
)

# Log assistant message with sources
session_mgr.log_message(
    session_id=session_id,
    role="assistant",
    content="Machine learning is...",
    tool_calls=[{'tool': 'document_search', 'params': {...}}],
    sources=[
        {'source': 'ml_basics.pdf', 'page': 3},
        {'source': 'wiki_ml.txt', 'chunk': 5}
    ]
)
```

#### Get Conversation History

```python
# Get all messages
messages = session_mgr.get_conversation_history(session_id)

# Get last 10 messages
recent = session_mgr.get_conversation_history(session_id, limit=10)

# Returns:
[
    {
        'role': 'user',
        'content': 'What is ML?',
        'timestamp': '2026-02-04T10:00:00',
        'sources': []
    },
    {
        'role': 'assistant',
        'content': 'ML is...',
        'timestamp': '2026-02-04T10:00:15',
        'sources': [...]
    },
    # ...
]
```

### Memory Operations

#### Store Episodic Memories

```python
# Store a preference
session_mgr.store_memory(
    session_id=session_id,
    memory_type="preference",
    content="User prefers detailed technical explanations",
    importance=0.8,
    metadata={'category': 'communication_style'}
)

# Store a fact
session_mgr.store_memory(
    session_id=session_id,
    memory_type="fact",
    content="User is studying machine learning",
    importance=0.9,
    metadata={'topic': 'machine_learning'}
)
```

#### Retrieve Memories

```python
# Get all memories
all_memories = session_mgr.get_session_memories(session_id)

# Get specific type
preferences = session_mgr.get_session_memories(
    session_id,
    memory_type="preference"
)

# Returns:
[
    {
        'type': 'preference',
        'content': 'User prefers detailed technical explanations',
        'importance': 0.8,
        'timestamp': '2026-02-04T10:30:00'
    },
    # ...
]
```

### Statistics Operations

```python
# Update session stats
session_mgr.update_session_stats(
    session_id=session_id,
    total_messages=10,
    total_tokens=5000,
    tools_used={'document_search': 4, 'web_search': 2},
    success_rate=0.95
)

# Stats are included in restore_session()
```

## PostgreSQL Backend

**File**: [src/database/postgres_backend.py](../src/database/postgres_backend.py)

Low-level database operations using psycopg.

### PostgresBackend

```python
class PostgresBackend:
    connection_string: str
    # Methods for CRUD operations on all tables
```

### Connection Management

```python
from src.database.postgres_backend import PostgresBackend

# Initialize
backend = PostgresBackend(connection_string)

# Initialize schema
backend.initialize_database()
# → Creates all tables if not exist

# Test connection
if backend.test_connection():
    print("✅ Connected to PostgreSQL")

# Close connections
backend.close()
```

## Configuration

**Database Settings** (from `.env`):

```bash
# Enable PostgreSQL
USE_POSTGRES=true

# Enable checkpoint storage
USE_CHECKPOINTS=true

# Full connection string (Supabase format)
DATABASE_URL=postgresql://user:password@host:port/database

# Or individual components (if DATABASE_URL not set)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=rag_chatbot
```

### Supabase Setup

1. **Create Supabase Project**: https://supabase.com/dashboard
2. **Get Connection String**:
   - Project Settings → Database → Connection String
   - Use "Transaction" pooler mode for psycopg
3. **Add to .env**:
   ```bash
   DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-1-ap-south-1.pooler.supabase.com:5432/postgres
   ```

## Integration with Streamlit

**File**: [src/ui/streamlit_app_agent.py](../src/ui/streamlit_app_agent.py)

### Session Management in UI

```python
# Initialize session manager
if 'session_manager' not in st.session_state:
    st.session_state.session_manager = SessionManager()

# Create or restore session
if st.session_state.session_manager.is_available():
    # Sidebar: Session selector
    sessions = st.session_state.session_manager.list_sessions()

    selected_session = st.selectbox(
        "Load Session",
        options=[s['session_id'] for s in sessions],
        format_func=lambda sid: next(
            (s['title'] for s in sessions if s['session_id'] == sid),
            "New Session"
        )
    )

    if selected_session:
        # Restore session
        session_data = st.session_state.session_manager.restore_session(selected_session)

        # Load conversation
        st.session_state.messages = session_data['conversation']

# After agent response
if agent_response and session_manager.is_available():
    # Log user message
    session_manager.log_message(
        session_id=thread_id,
        role="user",
        content=user_query
    )

    # Log assistant message
    session_manager.log_message(
        session_id=thread_id,
        role="assistant",
        content=agent_response['answer'],
        tool_calls=agent_response.get('tools_used'),
        sources=agent_response.get('sources')
    )
```

## Usage Examples

### Basic Session Flow

```python
from src.database.session_manager import SessionManager

# 1. Initialize
session_mgr = SessionManager()

# 2. Create session
session_id = session_mgr.create_session(
    user_id="alice",
    title="ML Learning Session"
)

# 3. Log conversation
session_mgr.log_message(session_id, "user", "What is ML?")
session_mgr.log_message(session_id, "assistant", "ML is...")

# 4. Store learning
session_mgr.store_memory(
    session_id,
    "preference",
    "User is beginner in ML",
    importance=0.7
)

# 5. Update stats
session_mgr.update_session_stats(
    session_id,
    total_messages=2,
    tools_used={'document_search': 1}
)

# 6. Later: Restore session
restored = session_mgr.restore_session(session_id)
print(f"Session: {restored['session']['title']}")
print(f"Messages: {len(restored['conversation'])}")
```

### Multi-User Sessions

```python
# User Alice's sessions
alice_sessions = session_mgr.list_sessions(user_id="alice")

# User Bob's sessions
bob_sessions = session_mgr.list_sessions(user_id="bob")

# Sessions are isolated by user_id
```

### Session Search

```python
# Search by title
ml_sessions = session_mgr.search_sessions(
    query="machine learning",
    user_id="alice"
)

# Returns sessions with "machine learning" in title
```

## Performance Considerations

### Connection Pooling

```python
# Supabase uses connection pooling by default
# Use "Transaction" mode for psycopg:
# postgresql://...@host:5432/postgres?pgbouncer=true
```

### Indexing

```sql
-- Indexes are automatically created on:
-- - Primary keys
-- - Foreign keys
-- - thread_id (checkpoints)
-- - session_id (messages, memories)

-- For better performance, add:
CREATE INDEX idx_messages_session_timestamp
ON messages(session_id, timestamp DESC);

CREATE INDEX idx_checkpoints_thread_created
ON checkpoints(thread_id, created_at DESC);
```

### Batch Operations

```python
# For bulk inserts, use transactions
with backend.connection.cursor() as cursor:
    for message in messages:
        cursor.execute("INSERT INTO messages ...")
    backend.connection.commit()
```

## Troubleshooting

### Connection failures

**Symptom**: "Could not connect to PostgreSQL"

**Solutions**:
1. Check `USE_POSTGRES=true` in `.env`
2. Verify `DATABASE_URL` is correct
3. Test connection: `psql $DATABASE_URL`
4. Check firewall/network settings
5. Ensure Supabase project is active
6. Use correct pooler mode (Transaction)

### Checkpoints not persisting

**Symptom**: Agent loses context between queries

**Solutions**:
1. Check `USE_CHECKPOINTS=true` in `.env`
2. Verify `langgraph-checkpoint-postgres` installed
3. Ensure `conversation_messages` in agent state
4. Use same `thread_id` across queries
5. Check checkpoint tables exist: `\dt checkpoints`

### Slow queries

**Symptom**: Database operations take too long

**Solutions**:
1. Add indexes (see above)
2. Use connection pooling
3. Limit message history: `get_conversation_history(limit=20)`
4. Archive old sessions periodically
5. Use Supabase Pro for better performance

### Memory growing too large

**Symptom**: Database size increasing rapidly

**Solutions**:
1. Set retention policy: Delete sessions older than N days
2. Compress checkpoint data
3. Archive inactive sessions to cold storage
4. Implement memory pruning
5. Monitor with `SELECT pg_size_pretty(pg_database_size('postgres'))`

## Best Practices

### 1. Always Use thread_id for Continuity

```python
# Generate stable thread_id
thread_id = f"user_{user_id}_session_{session_id}"

# Use consistently
agent.execute(query1, thread_id=thread_id)
agent.execute(query2, thread_id=thread_id)  # SAME ID
```

### 2. Log Messages Immediately

```python
# Right after agent response
session_manager.log_message(...)

# Don't batch - ensures data isn't lost if app crashes
```

### 3. Store Important Memories

```python
# After significant interactions
if user_revealed_preference:
    session_manager.store_memory(
        session_id,
        "preference",
        preference_text,
        importance=0.8
    )
```

### 4. Update Stats Periodically

```python
# After each turn
session_manager.update_session_stats(
    session_id,
    total_messages=len(messages),
    tools_used=tool_counts
)
```

### 5. Clean Up Old Data

```python
# Weekly cron job
from datetime import datetime, timedelta

cutoff = datetime.now() - timedelta(days=90)

old_sessions = [
    s for s in session_manager.list_sessions()
    if s['updated_at'] < cutoff and not s['is_active']
]

for session in old_sessions:
    session_manager.delete_session(session['session_id'])
```

### 6. Handle Failures Gracefully

```python
# Always check availability
if session_manager.is_available():
    session_manager.log_message(...)
else:
    # Fall back to in-memory or file-based storage
    pass
```

### 7. Close Connections

```python
# On app shutdown
try:
    session_manager.close()
    checkpoint_manager.close()
except Exception as e:
    print(f"Error during cleanup: {e}")
```

## Monitoring

### Database Size

```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('postgres'));

-- Check table sizes
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::regclass) DESC;
```

### Active Sessions

```sql
-- Count active sessions
SELECT COUNT(*) FROM sessions WHERE is_active = TRUE;

-- Recent sessions
SELECT session_id, title, updated_at
FROM sessions
ORDER BY updated_at DESC
LIMIT 10;
```

### Checkpoint Stats

```sql
-- Count checkpoints per thread
SELECT thread_id, COUNT(*)
FROM checkpoints
GROUP BY thread_id
ORDER BY COUNT(*) DESC
LIMIT 10;

-- Recent checkpoints
SELECT thread_id, checkpoint_id, created_at
FROM checkpoints
ORDER BY created_at DESC
LIMIT 20;
```

## Related Documentation

- [Agent System](AGENT_SYSTEM.md) - Checkpoint integration
- [Memory System](MEMORY_SYSTEM.md) - Memory persistence
- [Configuration](../CONFIGURATION.md) - Database settings
