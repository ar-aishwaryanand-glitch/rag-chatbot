"""Conversation memory for managing short-term context within a session."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import uuid


@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationMemory:
    """
    Manages conversation history within a single session.

    Features:
    - Stores recent messages (configurable limit)
    - Automatically summarizes older messages to save tokens
    - Provides context for agent prompts
    - Tracks conversation statistics
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        max_messages: int = 10,
        summarize_threshold: int = 20
    ):
        """
        Initialize conversation memory.

        Args:
            session_id: Unique identifier for this conversation session
            max_messages: Maximum number of recent messages to keep in full
            summarize_threshold: Summarize when total messages exceed this
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.max_messages = max_messages
        self.summarize_threshold = summarize_threshold

        self.messages: List[Message] = []
        self.summary: Optional[str] = None
        self.session_start = datetime.now()
        self.turn_count = 0

        # Statistics
        self.stats = {
            "total_user_messages": 0,
            "total_assistant_messages": 0,
            "total_tokens_approximate": 0,
            "topics_discussed": []
        }

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to conversation history.

        Args:
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            metadata: Optional metadata (tool used, sources, etc.)
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )

        self.messages.append(message)

        # Update statistics
        if role == "user":
            self.stats["total_user_messages"] += 1
            self.turn_count += 1
        elif role == "assistant":
            self.stats["total_assistant_messages"] += 1

        # Approximate token count (rough estimate: 1 token ≈ 4 chars)
        self.stats["total_tokens_approximate"] += len(content) // 4

        # Trigger summarization if needed
        if len(self.messages) > self.summarize_threshold:
            self._auto_summarize()

    def get_recent_messages(self, n: Optional[int] = None) -> List[Message]:
        """
        Get the N most recent messages.

        Args:
            n: Number of messages to retrieve (default: max_messages)

        Returns:
            List of recent messages
        """
        n = n or self.max_messages
        return self.messages[-n:]

    def get_context_string(self, max_messages: Optional[int] = None) -> str:
        """
        Get conversation context as a formatted string.

        Args:
            max_messages: Number of recent messages to include

        Returns:
            Formatted conversation history
        """
        context_parts = []

        # Add summary if exists
        if self.summary:
            context_parts.append(f"[Previous conversation summary]\n{self.summary}\n")

        # Add recent messages
        recent = self.get_recent_messages(max_messages)

        if recent:
            context_parts.append("[Recent conversation]")
            for msg in recent:
                prefix = "User" if msg.role == "user" else "Assistant"
                context_parts.append(f"{prefix}: {msg.content}")

        return "\n".join(context_parts)

    def get_last_user_message(self) -> Optional[str]:
        """Get the most recent user message."""
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg.content
        return None

    def get_last_assistant_message(self) -> Optional[str]:
        """Get the most recent assistant message."""
        for msg in reversed(self.messages):
            if msg.role == "assistant":
                return msg.content
        return None

    def _auto_summarize(self) -> None:
        """
        Automatically summarize older messages when threshold is exceeded.

        Keeps the most recent max_messages in full, summarizes the rest.
        """
        if len(self.messages) <= self.max_messages:
            return

        # Messages to summarize (all except recent max_messages)
        to_summarize = self.messages[:-self.max_messages]

        if not to_summarize:
            return

        # Simple extraction-based summarization (could use LLM in future)
        user_queries = [m.content for m in to_summarize if m.role == "user"]
        assistant_responses = [m.content for m in to_summarize if m.role == "assistant"]

        summary_parts = []

        if user_queries:
            summary_parts.append(f"User asked about: {', '.join(user_queries[:3])}")
            if len(user_queries) > 3:
                summary_parts.append(f"and {len(user_queries) - 3} other topics")

        if assistant_responses:
            tools_used = []
            for msg in to_summarize:
                if msg.role == "assistant" and msg.metadata.get("tools_used"):
                    tools_used.extend(msg.metadata["tools_used"])

            if tools_used:
                unique_tools = list(set(tools_used))
                summary_parts.append(f"Used tools: {', '.join(unique_tools)}")

        self.summary = ". ".join(summary_parts)

        # Remove summarized messages to save memory
        self.messages = self.messages[-self.max_messages:]

    def clear(self) -> None:
        """Clear all conversation history."""
        self.messages = []
        self.summary = None
        self.turn_count = 0
        self.stats = {
            "total_user_messages": 0,
            "total_assistant_messages": 0,
            "total_tokens_approximate": 0,
            "topics_discussed": []
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        duration = (datetime.now() - self.session_start).total_seconds()

        return {
            **self.stats,
            "session_id": self.session_id,
            "turn_count": self.turn_count,
            "total_messages": len(self.messages),
            "session_duration_seconds": duration,
            "has_summary": self.summary is not None
        }

    def to_dict(self) -> Dict[str, Any]:
        """Export conversation to dictionary format."""
        return {
            "session_id": self.session_id,
            "session_start": self.session_start.isoformat(),
            "turn_count": self.turn_count,
            "summary": self.summary,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in self.messages
            ],
            "stats": self.stats
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMemory':
        """Load conversation from dictionary format."""
        memory = cls(session_id=data["session_id"])
        memory.turn_count = data["turn_count"]
        memory.summary = data.get("summary")
        memory.session_start = datetime.fromisoformat(data["session_start"])
        memory.stats = data.get("stats", memory.stats)

        # Restore messages
        for msg_data in data.get("messages", []):
            message = Message(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                metadata=msg_data.get("metadata", {})
            )
            memory.messages.append(message)

        return memory
