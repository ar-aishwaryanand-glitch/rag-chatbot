"""Memory manager that coordinates conversation and episodic memory."""

from typing import Optional, Dict, Any, List
from pathlib import Path

from .conversation_memory import ConversationMemory
from .episodic_memory import EpisodicMemory, Episode


class MemoryManager:
    """
    Unified interface for managing both short-term and long-term memory.

    Coordinates:
    - ConversationMemory: Short-term context within a session
    - EpisodicMemory: Long-term summaries across sessions
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        storage_path: Optional[Path] = None,
        max_conversation_messages: int = 10
    ):
        """
        Initialize memory manager.

        Args:
            session_id: Unique session identifier (generated if None)
            storage_path: Path for episodic memory storage
            max_conversation_messages: Max messages in conversation buffer
        """
        # Initialize conversation memory for this session
        self.conversation_memory = ConversationMemory(
            session_id=session_id,
            max_messages=max_conversation_messages
        )

        # Initialize episodic memory (shared across sessions)
        self.episodic_memory = EpisodicMemory(storage_path=storage_path)

        self.session_id = self.conversation_memory.session_id

    # ===== Conversation Memory Methods =====

    def add_user_message(self, content: str, metadata: Optional[Dict] = None) -> None:
        """Add a user message to conversation memory."""
        self.conversation_memory.add_message("user", content, metadata)

    def add_assistant_message(
        self,
        content: str,
        tools_used: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """Add an assistant message to conversation memory."""
        metadata = metadata or {}
        if tools_used:
            metadata["tools_used"] = tools_used

        self.conversation_memory.add_message("assistant", content, metadata)

    def get_conversation_context(self, max_messages: Optional[int] = None) -> str:
        """Get formatted conversation context."""
        return self.conversation_memory.get_context_string(max_messages)

    def get_last_user_message(self) -> Optional[str]:
        """Get the most recent user message."""
        return self.conversation_memory.get_last_user_message()

    # ===== Episodic Memory Methods =====

    def finalize_session(
        self,
        summary: Optional[str] = None,
        outcomes: Optional[List[str]] = None,
        key_entities: Optional[List[str]] = None
    ) -> Episode:
        """
        Finalize the current session and store it as an episode.

        Args:
            summary: Optional custom summary (auto-generated if None)
            outcomes: Success/failure notes
            key_entities: Important topics or entities

        Returns:
            Created Episode
        """
        # Generate summary if not provided
        if summary is None:
            summary = self._generate_session_summary()

        # Extract user queries
        user_queries = [
            msg.content for msg in self.conversation_memory.messages
            if msg.role == "user"
        ]

        # Extract tools used
        tools_used = []
        for msg in self.conversation_memory.messages:
            if msg.role == "assistant" and msg.metadata.get("tools_used"):
                tools_used.extend(msg.metadata["tools_used"])

        # Create and store episode
        episode = self.episodic_memory.create_episode_from_conversation(
            session_id=self.session_id,
            conversation_summary=summary,
            user_queries=user_queries,
            tools_used=tools_used,
            outcomes=outcomes,
            key_entities=key_entities
        )

        return episode

    def search_past_conversations(self, query: str, max_results: int = 3) -> List[Episode]:
        """
        Search past conversations for relevant context.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of relevant episodes
        """
        return self.episodic_memory.search_episodes(query, max_results)

    def get_relevant_history(self, current_query: str) -> str:
        """
        Get relevant historical context for the current query.

        Args:
            current_query: The user's current question

        Returns:
            Formatted string with relevant past context
        """
        # Search for relevant past episodes
        relevant_episodes = self.search_past_conversations(current_query, max_results=2)

        if not relevant_episodes:
            return ""

        context_parts = ["[Relevant past conversations]"]

        for i, episode in enumerate(relevant_episodes, 1):
            context_parts.append(f"\n{i}. {episode.timestamp.strftime('%Y-%m-%d')}: {episode.summary}")

            if episode.key_entities:
                context_parts.append(f"   Topics: {', '.join(episode.key_entities[:3])}")

        return "\n".join(context_parts)

    def get_user_preferences(self) -> Dict[str, Any]:
        """Get aggregated user preferences from past sessions."""
        return self.episodic_memory.get_aggregated_preferences()

    # ===== Combined Context Methods =====

    def get_full_context(
        self,
        current_query: str,
        include_episodic: bool = True,
        max_conversation_messages: Optional[int] = None
    ) -> str:
        """
        Get complete context including conversation history and relevant past episodes.

        Args:
            current_query: Current user query
            include_episodic: Whether to include past episodes
            max_conversation_messages: Max conversation messages to include

        Returns:
            Formatted context string
        """
        context_parts = []

        # Add relevant past episodes
        if include_episodic:
            past_context = self.get_relevant_history(current_query)
            if past_context:
                context_parts.append(past_context)

        # Add current conversation
        conversation_context = self.get_conversation_context(max_conversation_messages)
        if conversation_context:
            context_parts.append(conversation_context)

        return "\n\n".join(context_parts)

    # ===== Statistics and Monitoring =====

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for the current session."""
        return self.conversation_memory.get_stats()

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get overall memory system summary."""
        return {
            "current_session": self.get_session_stats(),
            "episodic_memory": self.episodic_memory.get_summary()
        }

    # ===== Helper Methods =====

    def _generate_session_summary(self) -> str:
        """Generate a summary of the current session."""
        stats = self.conversation_memory.get_stats()

        # Simple extraction-based summary
        user_queries = [
            msg.content for msg in self.conversation_memory.messages
            if msg.role == "user"
        ]

        tools_used = []
        for msg in self.conversation_memory.messages:
            if msg.role == "assistant" and msg.metadata.get("tools_used"):
                tools_used.extend(msg.metadata["tools_used"])

        unique_tools = list(set(tools_used))

        summary_parts = []

        if user_queries:
            # Summarize first few queries
            summary_parts.append(f"User asked about: {user_queries[0]}")
            if len(user_queries) > 1:
                summary_parts.append(f"and {len(user_queries) - 1} other question(s)")

        if unique_tools:
            summary_parts.append(f"Tools used: {', '.join(unique_tools)}")

        return ". ".join(summary_parts) if summary_parts else "Brief conversation session"

    def clear_conversation(self) -> None:
        """Clear current conversation memory (keeps episodic)."""
        self.conversation_memory.clear()

    def clear_all_memory(self) -> None:
        """Clear all memory (conversation + episodic). Use with caution!"""
        self.conversation_memory.clear()
        self.episodic_memory.clear_all()
