"""
PostgreSQL backend for session and memory storage.

This module provides database operations for:
- Creating and managing sessions
- Storing and retrieving messages
- Managing episodic memory
- Session restoration
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2 import pool
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

from .models import Session, Message, EpisodicMemory, SessionStats


class PostgresBackend:
    """PostgreSQL backend for session and memory storage."""

    def __init__(self, connection_string: str = None):
        """
        Initialize PostgreSQL backend.

        Args:
            connection_string: PostgreSQL connection string
                Format: postgresql://user:password@host:port/database
        """
        if not POSTGRES_AVAILABLE:
            raise ImportError("psycopg2 not installed. Run: pip install psycopg2-binary")

        self.connection_string = connection_string or self._get_connection_string()
        self.connection_pool = None
        self._initialize_pool()

    def _get_connection_string(self) -> str:
        """Get connection string from environment variables."""
        # Try full connection string first
        conn_str = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')

        if conn_str:
            return conn_str

        # Build from individual components
        user = os.getenv('POSTGRES_USER', 'postgres')
        password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        database = os.getenv('POSTGRES_DB', 'rag_chatbot')

        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    def _initialize_pool(self):
        """Initialize connection pool."""
        try:
            self.connection_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=self.connection_string
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        conn = self.connection_pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.connection_pool.putconn(conn)

    def initialize_database(self):
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255),
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}',
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) REFERENCES sessions(session_id) ON DELETE CASCADE,
                    role VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}',
                    tool_calls JSONB,
                    sources JSONB
                )
            """)

            # Episodic memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    memory_id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) REFERENCES sessions(session_id) ON DELETE CASCADE,
                    memory_type VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    importance FLOAT DEFAULT 0.5,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}',
                    embedding JSONB
                )
            """)

            # Session stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_stats (
                    session_id VARCHAR(255) PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,
                    total_messages INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    tools_used JSONB DEFAULT '{}',
                    success_rate FLOAT DEFAULT 0.0,
                    avg_response_time FLOAT DEFAULT 0.0,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session_id
                ON messages(session_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp
                ON messages(timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_session_id
                ON episodic_memory(session_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_updated_at
                ON sessions(updated_at DESC)
            """)

            cursor.close()

    # Session operations

    def create_session(self, session: Session) -> bool:
        """Create a new session."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sessions (session_id, user_id, title, created_at, updated_at, metadata, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    session.session_id,
                    session.user_id,
                    session.title,
                    session.created_at,
                    session.updated_at,
                    json.dumps(session.metadata),
                    session.is_active
                ))
                cursor.close()
                return True
        except Exception as e:
            print(f"Error creating session: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    SELECT * FROM sessions WHERE session_id = %s
                """, (session_id,))
                row = cursor.fetchone()
                cursor.close()

                if row:
                    return Session(
                        session_id=row['session_id'],
                        user_id=row['user_id'],
                        title=row['title'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        metadata=row['metadata'],
                        is_active=row['is_active']
                    )
                return None
        except Exception as e:
            print(f"Error getting session: {e}")
            return None

    def list_sessions(self, user_id: Optional[str] = None, limit: int = 50) -> List[Session]:
        """List all sessions, optionally filtered by user."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                if user_id:
                    cursor.execute("""
                        SELECT * FROM sessions
                        WHERE user_id = %s
                        ORDER BY updated_at DESC
                        LIMIT %s
                    """, (user_id, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM sessions
                        ORDER BY updated_at DESC
                        LIMIT %s
                    """, (limit,))

                rows = cursor.fetchall()
                cursor.close()

                return [
                    Session(
                        session_id=row['session_id'],
                        user_id=row['user_id'],
                        title=row['title'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        metadata=row['metadata'],
                        is_active=row['is_active']
                    )
                    for row in rows
                ]
        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []

    def update_session(self, session_id: str, **kwargs):
        """Update session fields."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Build dynamic update query
                fields = []
                values = []
                for key, value in kwargs.items():
                    if key in ['title', 'metadata', 'is_active']:
                        fields.append(f"{key} = %s")
                        values.append(json.dumps(value) if key == 'metadata' else value)

                if fields:
                    fields.append("updated_at = %s")
                    values.append(datetime.now())
                    values.append(session_id)

                    query = f"UPDATE sessions SET {', '.join(fields)} WHERE session_id = %s"
                    cursor.execute(query, values)
                    cursor.close()
                    return True
                return False
        except Exception as e:
            print(f"Error updating session: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all related data."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
                cursor.close()
                return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False

    # Message operations

    def add_message(self, message: Message) -> Optional[int]:
        """Add a message to a session."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO messages (session_id, role, content, timestamp, metadata, tool_calls, sources)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING message_id
                """, (
                    message.session_id,
                    message.role,
                    message.content,
                    message.timestamp,
                    json.dumps(message.metadata),
                    json.dumps(message.tool_calls) if message.tool_calls else None,
                    json.dumps(message.sources) if message.sources else None
                ))
                message_id = cursor.fetchone()[0]
                cursor.close()

                # Update session timestamp
                self.update_session(message.session_id, updated_at=datetime.now())

                return message_id
        except Exception as e:
            print(f"Error adding message: {e}")
            return None

    def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Message]:
        """Get all messages from a session."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                if limit:
                    cursor.execute("""
                        SELECT * FROM messages
                        WHERE session_id = %s
                        ORDER BY timestamp DESC
                        LIMIT %s
                    """, (session_id, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM messages
                        WHERE session_id = %s
                        ORDER BY timestamp ASC
                    """, (session_id,))

                rows = cursor.fetchall()
                cursor.close()

                return [
                    Message(
                        message_id=row['message_id'],
                        session_id=row['session_id'],
                        role=row['role'],
                        content=row['content'],
                        timestamp=row['timestamp'],
                        metadata=row['metadata'],
                        tool_calls=row['tool_calls'],
                        sources=row['sources']
                    )
                    for row in rows
                ]
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []

    # Episodic memory operations

    def add_memory(self, memory: EpisodicMemory) -> Optional[int]:
        """Add an episodic memory entry."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO episodic_memory (session_id, memory_type, content, importance, timestamp, metadata, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING memory_id
                """, (
                    memory.session_id,
                    memory.memory_type,
                    memory.content,
                    memory.importance,
                    memory.timestamp,
                    json.dumps(memory.metadata),
                    json.dumps(memory.embedding) if memory.embedding else None
                ))
                memory_id = cursor.fetchone()[0]
                cursor.close()
                return memory_id
        except Exception as e:
            print(f"Error adding memory: {e}")
            return None

    def get_memories(self, session_id: str, memory_type: Optional[str] = None) -> List[EpisodicMemory]:
        """Get episodic memories for a session."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                if memory_type:
                    cursor.execute("""
                        SELECT * FROM episodic_memory
                        WHERE session_id = %s AND memory_type = %s
                        ORDER BY importance DESC, timestamp DESC
                    """, (session_id, memory_type))
                else:
                    cursor.execute("""
                        SELECT * FROM episodic_memory
                        WHERE session_id = %s
                        ORDER BY importance DESC, timestamp DESC
                    """, (session_id,))

                rows = cursor.fetchall()
                cursor.close()

                return [
                    EpisodicMemory(
                        memory_id=row['memory_id'],
                        session_id=row['session_id'],
                        memory_type=row['memory_type'],
                        content=row['content'],
                        importance=row['importance'],
                        timestamp=row['timestamp'],
                        metadata=row['metadata'],
                        embedding=row['embedding']
                    )
                    for row in rows
                ]
        except Exception as e:
            print(f"Error getting memories: {e}")
            return []

    # Session stats operations

    def update_stats(self, stats: SessionStats) -> bool:
        """Update session statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO session_stats (session_id, total_messages, total_tokens, tools_used, success_rate, avg_response_time, last_activity)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET
                        total_messages = EXCLUDED.total_messages,
                        total_tokens = EXCLUDED.total_tokens,
                        tools_used = EXCLUDED.tools_used,
                        success_rate = EXCLUDED.success_rate,
                        avg_response_time = EXCLUDED.avg_response_time,
                        last_activity = EXCLUDED.last_activity
                """, (
                    stats.session_id,
                    stats.total_messages,
                    stats.total_tokens,
                    json.dumps(stats.tools_used),
                    stats.success_rate,
                    stats.avg_response_time,
                    stats.last_activity
                ))
                cursor.close()
                return True
        except Exception as e:
            print(f"Error updating stats: {e}")
            return False

    def get_stats(self, session_id: str) -> Optional[SessionStats]:
        """Get session statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    SELECT * FROM session_stats WHERE session_id = %s
                """, (session_id,))
                row = cursor.fetchone()
                cursor.close()

                if row:
                    return SessionStats(
                        session_id=row['session_id'],
                        total_messages=row['total_messages'],
                        total_tokens=row['total_tokens'],
                        tools_used=row['tools_used'],
                        success_rate=row['success_rate'],
                        avg_response_time=row['avg_response_time'],
                        last_activity=row['last_activity']
                    )
                return None
        except Exception as e:
            print(f"Error getting stats: {e}")
            return None

    def close(self):
        """Close the connection pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
