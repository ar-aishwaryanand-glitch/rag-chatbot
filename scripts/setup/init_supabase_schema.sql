-- Supabase Database Schema Initialization
-- Run this SQL in your Supabase SQL Editor
-- Dashboard → SQL Editor → New Query → Paste and Run

-- ============================================
-- 1. Sessions Table
-- ============================================
-- Stores conversation sessions for each user
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

COMMENT ON TABLE sessions IS 'Stores conversation sessions';
COMMENT ON COLUMN sessions.session_id IS 'Unique identifier for each session';
COMMENT ON COLUMN sessions.metadata IS 'Additional session data (user info, settings, etc.)';

-- ============================================
-- 2. Messages Table
-- ============================================
-- Stores individual messages within each session
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

COMMENT ON TABLE messages IS 'Stores conversation messages';
COMMENT ON COLUMN messages.role IS 'Message sender: user, assistant, or system';
COMMENT ON COLUMN messages.content IS 'Message text content';
COMMENT ON COLUMN messages.metadata IS 'Additional message data (tool calls, sources, etc.)';

-- ============================================
-- 3. Checkpoints Table (LangGraph)
-- ============================================
-- Stores agent execution state for resumable workflows
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

COMMENT ON TABLE checkpoints IS 'LangGraph checkpoints for agent state persistence';
COMMENT ON COLUMN checkpoints.thread_id IS 'Execution thread identifier';
COMMENT ON COLUMN checkpoints.checkpoint_id IS 'Unique checkpoint identifier';
COMMENT ON COLUMN checkpoints.checkpoint IS 'Serialized agent state';

-- ============================================
-- 4. Indexes for Performance
-- ============================================

-- Index for fast message lookup by session
CREATE INDEX IF NOT EXISTS idx_messages_session_id
ON messages(session_id);

-- Index for chronological message ordering
CREATE INDEX IF NOT EXISTS idx_messages_timestamp
ON messages(timestamp DESC);

-- Index for checkpoint lookup by thread
CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id
ON checkpoints(thread_id);

-- Index for session lookup
CREATE INDEX IF NOT EXISTS idx_sessions_created_at
ON sessions(created_at DESC);

-- ============================================
-- 5. Triggers for Auto-Update
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update sessions.updated_at
DROP TRIGGER IF EXISTS update_sessions_updated_at ON sessions;
CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 6. Verify Setup
-- ============================================

-- Check if tables were created successfully
DO $$
DECLARE
    session_count INTEGER;
    message_count INTEGER;
    checkpoint_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO session_count FROM information_schema.tables
    WHERE table_name = 'sessions';

    SELECT COUNT(*) INTO message_count FROM information_schema.tables
    WHERE table_name = 'messages';

    SELECT COUNT(*) INTO checkpoint_count FROM information_schema.tables
    WHERE table_name = 'checkpoints';

    RAISE NOTICE '✓ Tables created:';
    RAISE NOTICE '  - sessions: %', CASE WHEN session_count > 0 THEN 'YES' ELSE 'NO' END;
    RAISE NOTICE '  - messages: %', CASE WHEN message_count > 0 THEN 'YES' ELSE 'NO' END;
    RAISE NOTICE '  - checkpoints: %', CASE WHEN checkpoint_count > 0 THEN 'YES' ELSE 'NO' END;
    RAISE NOTICE '✓ Database schema initialized successfully!';
END $$;

-- Show table structure
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
    AND table_name IN ('sessions', 'messages', 'checkpoints')
ORDER BY table_name, ordinal_position;
