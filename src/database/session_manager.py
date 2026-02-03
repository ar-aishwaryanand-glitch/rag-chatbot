"""
Session Manager for PostgreSQL-backed conversation sessions.

This module provides high-level session management:
- Session creation and restoration
- Message logging
- Memory integration
- Session search and filtering
"""

import os
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

from .postgres_backend import PostgresBackend
from .models import Session, Message, EpisodicMemory, SessionStats


class SessionManager:
    """
    High-level session management with PostgreSQL backend.

    Integrates with the agent's memory system to provide persistent
    conversation storage and session restoration.
    """

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize Session Manager.

        Args:
            connection_string: PostgreSQL connection string (optional)
        """
        # Check if PostgreSQL is enabled
        self.enabled = self._check_postgres_enabled()

        if self.enabled:
            try:
                self.backend = PostgresBackend(connection_string)
                self.backend.initialize_database()
            except Exception as e:
                print(f"⚠️  PostgreSQL connection failed: {e}")
                print("📝 Falling back to file-based memory storage")
                self.enabled = False
                self.backend = None
        else:
            self.backend = None

    def _check_postgres_enabled(self) -> bool:
        """Check if PostgreSQL is enabled via environment variable."""
        return os.getenv('USE_POSTGRES', 'false').lower() == 'true'

    def is_available(self) -> bool:
        """Check if PostgreSQL backend is available."""
        return self.enabled and self.backend is not None

    # Session operations

    def create_session(self, user_id: Optional[str] = None, title: Optional[str] = None) -> Optional[str]:
        """
        Create a new session.

        Args:
            user_id: Optional user identifier
            title: Optional session title

        Returns:
            Session ID if successful, None otherwise
        """
        if not self.is_available():
            return None

        try:
            session_id = str(uuid.uuid4())
            session = Session(
                session_id=session_id,
                user_id=user_id,
                title=title or "New Conversation",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            if self.backend.create_session(session):
                return session_id
            return None
        except Exception as e:
            print(f"Error creating session: {e}")
            return None

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session object if found, None otherwise
        """
        if not self.is_available():
            return None

        return self.backend.get_session(session_id)

    def list_sessions(self, user_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List all sessions.

        Args:
            user_id: Filter by user ID (optional)
            limit: Maximum number of sessions to return

        Returns:
            List of session dictionaries with metadata
        """
        if not self.is_available():
            return []

        sessions = self.backend.list_sessions(user_id, limit)

        # Enhance with message counts
        result = []
        for session in sessions:
            messages = self.backend.get_messages(session.session_id)
            result.append({
                'session_id': session.session_id,
                'title': session.title,
                'created_at': session.created_at,
                'updated_at': session.updated_at,
                'message_count': len(messages),
                'is_active': session.is_active
            })

        return result

    def restore_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Restore a complete session with all messages and memory.

        Args:
            session_id: Session to restore

        Returns:
            Dictionary with session data and messages
        """
        if not self.is_available():
            return None

        try:
            session = self.backend.get_session(session_id)
            if not session:
                return None

            messages = self.backend.get_messages(session_id)
            memories = self.backend.get_memories(session_id)
            stats = self.backend.get_stats(session_id)

            # Convert to conversation format
            conversation = []
            for msg in messages:
                conversation.append({
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'sources': msg.sources
                })

            return {
                'session': {
                    'id': session.session_id,
                    'title': session.title,
                    'created_at': session.created_at.isoformat(),
                    'updated_at': session.updated_at.isoformat()
                },
                'conversation': conversation,
                'memories': [
                    {
                        'type': mem.memory_type,
                        'content': mem.content,
                        'importance': mem.importance
                    }
                    for mem in memories
                ],
                'stats': {
                    'total_messages': stats.total_messages if stats else len(messages),
                    'tools_used': stats.tools_used if stats else {},
                    'success_rate': stats.success_rate if stats else 0.0
                } if stats else None
            }
        except Exception as e:
            print(f"Error restoring session: {e}")
            return None

    def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session title."""
        if not self.is_available():
            return False

        return self.backend.update_session(session_id, title=title)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all related data."""
        if not self.is_available():
            return False

        return self.backend.delete_session(session_id)

    # Message operations

    def log_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict]] = None,
        sources: Optional[List[Dict]] = None
    ) -> bool:
        """
        Log a conversation message.

        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            tool_calls: Optional tool calls made
            sources: Optional sources used

        Returns:
            True if successful
        """
        if not self.is_available():
            return False

        try:
            message = Message(
                session_id=session_id,
                role=role,
                content=content,
                timestamp=datetime.now(),
                tool_calls=tool_calls,
                sources=sources
            )

            message_id = self.backend.add_message(message)
            return message_id is not None
        except Exception as e:
            print(f"Error logging message: {e}")
            return False

    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages

        Returns:
            List of message dictionaries
        """
        if not self.is_available():
            return []

        messages = self.backend.get_messages(session_id, limit)

        return [
            {
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'sources': msg.sources
            }
            for msg in messages
        ]

    # Memory operations

    def store_memory(
        self,
        session_id: str,
        memory_type: str,
        content: str,
        importance: float = 0.5,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Store an episodic memory.

        Args:
            session_id: Session identifier
            memory_type: Type of memory (conversation, fact, preference, task)
            content: Memory content
            importance: Importance score (0-1)
            metadata: Optional metadata

        Returns:
            True if successful
        """
        if not self.is_available():
            return False

        try:
            memory = EpisodicMemory(
                session_id=session_id,
                memory_type=memory_type,
                content=content,
                importance=importance,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )

            memory_id = self.backend.add_memory(memory)
            return memory_id is not None
        except Exception as e:
            print(f"Error storing memory: {e}")
            return False

    def get_session_memories(self, session_id: str, memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get episodic memories for a session."""
        if not self.is_available():
            return []

        memories = self.backend.get_memories(session_id, memory_type)

        return [
            {
                'type': mem.memory_type,
                'content': mem.content,
                'importance': mem.importance,
                'timestamp': mem.timestamp.isoformat()
            }
            for mem in memories
        ]

    # Stats operations

    def update_session_stats(
        self,
        session_id: str,
        total_messages: Optional[int] = None,
        total_tokens: Optional[int] = None,
        tools_used: Optional[Dict[str, int]] = None,
        success_rate: Optional[float] = None
    ) -> bool:
        """Update session statistics."""
        if not self.is_available():
            return False

        try:
            # Get current stats or create new
            stats = self.backend.get_stats(session_id)
            if not stats:
                stats = SessionStats(session_id=session_id)

            # Update fields
            if total_messages is not None:
                stats.total_messages = total_messages
            if total_tokens is not None:
                stats.total_tokens = total_tokens
            if tools_used is not None:
                stats.tools_used = tools_used
            if success_rate is not None:
                stats.success_rate = success_rate

            stats.last_activity = datetime.now()

            return self.backend.update_stats(stats)
        except Exception as e:
            print(f"Error updating stats: {e}")
            return False

    # Search and filter

    def search_sessions(self, query: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search sessions by title or content.

        Args:
            query: Search query
            user_id: Optional user filter

        Returns:
            List of matching sessions
        """
        if not self.is_available():
            return []

        # Simple implementation - can be enhanced with full-text search
        all_sessions = self.list_sessions(user_id)

        return [
            session for session in all_sessions
            if query.lower() in session['title'].lower()
        ]

    def close(self):
        """Close database connections."""
        if self.backend:
            self.backend.close()
