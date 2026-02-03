"""
Database models for PostgreSQL session and memory storage.

This module defines the database schema for:
- User sessions
- Conversation messages
- Episodic memory
- Session metadata
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import json


@dataclass
class Session:
    """Represents a conversation session."""
    session_id: str
    user_id: Optional[str] = None
    title: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'title': self.title,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': json.dumps(self.metadata),
            'is_active': self.is_active
        }


@dataclass
class Message:
    """Represents a conversation message."""
    message_id: Optional[int] = None
    session_id: str = ""
    role: str = "user"  # user, assistant, system
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tool_calls: Optional[List[Dict[str, Any]]] = None
    sources: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'message_id': self.message_id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': json.dumps(self.metadata),
            'tool_calls': json.dumps(self.tool_calls) if self.tool_calls else None,
            'sources': json.dumps(self.sources) if self.sources else None
        }


@dataclass
class EpisodicMemory:
    """Represents an episodic memory entry."""
    memory_id: Optional[int] = None
    session_id: str = ""
    memory_type: str = "conversation"  # conversation, fact, preference, task
    content: str = ""
    importance: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'memory_id': self.memory_id,
            'session_id': self.session_id,
            'memory_type': self.memory_type,
            'content': self.content,
            'importance': self.importance,
            'timestamp': self.timestamp.isoformat(),
            'metadata': json.dumps(self.metadata),
            'embedding': json.dumps(self.embedding) if self.embedding else None
        }


@dataclass
class SessionStats:
    """Represents session statistics."""
    session_id: str
    total_messages: int = 0
    total_tokens: int = 0
    tools_used: Dict[str, int] = field(default_factory=dict)
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    last_activity: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'total_messages': self.total_messages,
            'total_tokens': self.total_tokens,
            'tools_used': json.dumps(self.tools_used),
            'success_rate': self.success_rate,
            'avg_response_time': self.avg_response_time,
            'last_activity': self.last_activity.isoformat()
        }
