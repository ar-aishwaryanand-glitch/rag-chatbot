# PostgreSQL Session Storage Setup

This guide shows how to configure persistent session storage using PostgreSQL for your RAG chatbot.

---

## 🎯 What You Get

With PostgreSQL enabled, your RAG chatbot will:
- ✅ **Persist conversations** across browser sessions
- ✅ **Restore previous sessions** from the sidebar
- ✅ **Store episodic memory** in a database
- ✅ **Track session statistics** (messages, tools used, success rate)
- ✅ **Search conversation history**
- ✅ **Never lose chat history** even after closing the browser

---

## 📋 Prerequisites

### 1. Install PostgreSQL

**Mac (Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download from [https://www.postgresql.org/download/windows/](https://www.postgresql.org/download/windows/)

**Docker (All Platforms):**
```bash
docker run --name rag-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=rag_chatbot \
  -p 5432:5432 \
  -d postgres:15
```

### 2. Create Database

```bash
# Create database
createdb rag_chatbot

# Or using psql
psql -U postgres
CREATE DATABASE rag_chatbot;
\q
```

### 3. Install Python Package

```bash
pip install psycopg2-binary
```

---

## ⚙️ Configuration

### Step 1: Update `.env` File

Copy `.env.example` to `.env` if you haven't already:
```bash
cp .env.example .env
```

### Step 2: Enable PostgreSQL

Edit `.env` and set:
```bash
USE_POSTGRES=true
```

### Step 3: Configure Connection

**Option A: Full Connection String (Recommended)**
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/rag_chatbot
```

**Option B: Individual Parameters**
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=rag_chatbot
```

### Example `.env` Configuration

```bash
# Enable PostgreSQL
USE_POSTGRES=true

# Local PostgreSQL (choose one method)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rag_chatbot

# OR use individual parameters
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=postgres
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_DB=rag_chatbot
```

---

## 🚀 Initialize Database

Run the initialization script to create tables:

```bash
python init_database.py
```

**Expected output:**
```
================================================================================
PostgreSQL Database Initialization
================================================================================

📝 Connection Information:
   Host: localhost
   Port: 5432
   Database: rag_chatbot
   User: postgres

🔌 Testing PostgreSQL connection...
✅ Connected to PostgreSQL
   Version: PostgreSQL 15.5

📊 Initializing database tables...
✅ Database tables created successfully

📋 Created tables:
   • sessions
   • messages
   • episodic_memory
   • session_stats

================================================================================
🎉 Database initialization complete!
================================================================================
```

---

## 🎮 Using Session Management

### Start the Agent UI

```bash
streamlit run run_agent_ui.py
```

### Session Features in UI

#### 1. **Session Selector** (Top of Sidebar)
- View all your past sessions
- Click to restore any previous conversation
- Sessions show title and message count

#### 2. **Create New Session**
- Select "➕ New Session" from dropdown
- Starts fresh with empty chat history

#### 3. **Rename Session**
- Expand "⚙️ Session Options" in sidebar
- Enter new title and click "💾 Save Title"

#### 4. **Delete Session**
- Expand "⚙️ Session Options"
- Click "🗑️ Delete Session" (twice to confirm)
- Removes session and all associated data

### Automatic Features

When PostgreSQL is enabled, the system automatically:
- Creates a new session when you start chatting
- Logs every message (user and assistant)
- Stores tool calls and sources
- Tracks episodic memory
- Updates session statistics

---

## 📊 Database Schema

### Tables

#### **sessions**
Stores conversation sessions
```sql
- session_id (VARCHAR, PRIMARY KEY)
- user_id (VARCHAR, nullable)
- title (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- metadata (JSONB)
- is_active (BOOLEAN)
```

#### **messages**
Stores conversation messages
```sql
- message_id (SERIAL, PRIMARY KEY)
- session_id (VARCHAR, FOREIGN KEY)
- role (VARCHAR: user/assistant/system)
- content (TEXT)
- timestamp (TIMESTAMP)
- metadata (JSONB)
- tool_calls (JSONB)
- sources (JSONB)
```

#### **episodic_memory**
Stores agent memories
```sql
- memory_id (SERIAL, PRIMARY KEY)
- session_id (VARCHAR, FOREIGN KEY)
- memory_type (VARCHAR)
- content (TEXT)
- importance (FLOAT)
- timestamp (TIMESTAMP)
- metadata (JSONB)
- embedding (JSONB)
```

#### **session_stats**
Stores session statistics
```sql
- session_id (VARCHAR, PRIMARY KEY, FOREIGN KEY)
- total_messages (INTEGER)
- total_tokens (INTEGER)
- tools_used (JSONB)
- success_rate (FLOAT)
- avg_response_time (FLOAT)
- last_activity (TIMESTAMP)
```

---

## 🌐 Cloud PostgreSQL Providers

### Heroku Postgres (Free Tier)
```bash
# From Heroku dashboard, copy DATABASE_URL
DATABASE_URL=postgres://user:pass@host:5432/db
```

### Supabase (Free Tier)
```bash
# From Supabase dashboard → Settings → Database
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
```

### Railway (Free Trial)
```bash
# From Railway dashboard, copy PostgreSQL URL
DATABASE_URL=postgresql://postgres:pass@host.railway.app:5432/railway
```

### Neon (Free Tier)
```bash
# From Neon dashboard, copy connection string
DATABASE_URL=postgres://user@host.neon.tech/db?sslmode=require
```

---

## 🔧 Troubleshooting

### Connection Refused
```
Error: connection refused
```

**Solution:**
- Check if PostgreSQL is running: `pg_isready`
- Start PostgreSQL: `brew services start postgresql@15` (Mac)
- Check port: PostgreSQL usually runs on port 5432

### Authentication Failed
```
Error: password authentication failed
```

**Solution:**
- Verify your password in `.env`
- Reset password: `psql -U postgres -c "ALTER USER postgres PASSWORD 'newpassword';"`

### Database Does Not Exist
```
Error: database "rag_chatbot" does not exist
```

**Solution:**
```bash
createdb rag_chatbot
# Or in psql: CREATE DATABASE rag_chatbot;
```

### psycopg2 Not Installed
```
Error: psycopg2 not installed
```

**Solution:**
```bash
pip install psycopg2-binary
```

### Permission Denied
```
Error: permission denied for schema public
```

**Solution:**
```sql
-- In psql
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
```

---

## 🔒 Security Best Practices

### 1. Use Environment Variables
Never commit `.env` to git:
```bash
# .env is already in .gitignore
echo ".env" >> .gitignore
```

### 2. Strong Passwords
Use strong passwords for production:
```bash
# Generate secure password
openssl rand -base64 32
```

### 3. SSL Connections (Production)
Add SSL to connection string:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

### 4. Restrict Access
- Use firewall rules to limit database access
- Create separate users with limited permissions
- Enable connection pooling for production

---

## 🧪 Testing the Setup

### 1. Test Connection
```bash
python init_database.py
```

### 2. Test in Python
```python
from src.database.session_manager import SessionManager

# Initialize manager
manager = SessionManager()

# Check if available
if manager.is_available():
    print("✅ PostgreSQL is working!")

    # Create test session
    session_id = manager.create_session(title="Test Session")
    print(f"Created session: {session_id}")

    # List sessions
    sessions = manager.list_sessions()
    print(f"Total sessions: {len(sessions)}")
else:
    print("❌ PostgreSQL not available")
```

### 3. Test in UI
1. Run `streamlit run run_agent_ui.py`
2. Look for "💾 Session Management" in sidebar
3. Start a conversation
4. Refresh the page - conversation should persist!

---

## 📈 Migration from File-Based Storage

If you have existing episodic memory files, they will continue to work. PostgreSQL runs alongside file-based storage.

To migrate old sessions to PostgreSQL:
1. Enable PostgreSQL in `.env`
2. Old file-based memories remain in `data/episodic_memory/`
3. New conversations are stored in PostgreSQL
4. Both systems coexist peacefully

---

## 💡 Tips & Tricks

### View Sessions in psql
```bash
psql -d rag_chatbot

-- List all sessions
SELECT session_id, title, created_at,
       (SELECT COUNT(*) FROM messages WHERE messages.session_id = sessions.session_id) as msg_count
FROM sessions
ORDER BY updated_at DESC
LIMIT 10;

-- View messages from a session
SELECT role, LEFT(content, 50), timestamp
FROM messages
WHERE session_id = 'your-session-id'
ORDER BY timestamp;
```

### Backup Database
```bash
pg_dump rag_chatbot > backup.sql
```

### Restore Database
```bash
psql rag_chatbot < backup.sql
```

### Clean Old Sessions
```sql
-- Delete sessions older than 30 days
DELETE FROM sessions WHERE updated_at < NOW() - INTERVAL '30 days';
```

---

## 🆘 Getting Help

If you encounter issues:

1. **Check logs**: Look for error messages in terminal
2. **Verify connection**: Run `python init_database.py`
3. **Test PostgreSQL**: Run `pg_isready` and `psql -l`
4. **Check `.env`**: Ensure `USE_POSTGRES=true` and connection details are correct
5. **Review documentation**: [PostgreSQL Docs](https://www.postgresql.org/docs/)

---

*Last updated: 2026-02-03*
