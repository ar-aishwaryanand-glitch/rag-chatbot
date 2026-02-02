"""Episodic memory for storing and retrieving past conversation summaries."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
import json
import pickle


@dataclass
class Episode:
    """Represents a summary of a past conversation session."""
    session_id: str
    timestamp: datetime
    summary: str
    user_queries: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    outcomes: List[str] = field(default_factory=list)  # success/failure notes
    key_entities: List[str] = field(default_factory=list)  # important topics/names
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert episode to dictionary."""
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "summary": self.summary,
            "user_queries": self.user_queries,
            "tools_used": self.tools_used,
            "outcomes": self.outcomes,
            "key_entities": self.key_entities,
            "user_preferences": self.user_preferences,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Episode':
        """Create episode from dictionary."""
        return cls(
            session_id=data["session_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            summary=data["summary"],
            user_queries=data.get("user_queries", []),
            tools_used=data.get("tools_used", []),
            outcomes=data.get("outcomes", []),
            key_entities=data.get("key_entities", []),
            user_preferences=data.get("user_preferences", {}),
            metadata=data.get("metadata", {})
        )


class EpisodicMemory:
    """
    Stores and retrieves summaries of past conversations.

    Features:
    - Persists conversation summaries to disk
    - Searches past conversations by keywords or similarity
    - Learns user preferences over time
    - Tracks tool usage patterns
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize episodic memory.

        Args:
            storage_path: Path to store memory files (default: data/episodic_memory)
        """
        if storage_path is None:
            storage_path = Path(__file__).parent.parent.parent.parent / "data" / "episodic_memory"

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.episodes: Dict[str, Episode] = {}  # session_id -> Episode
        self._load_episodes()

    def add_episode(self, episode: Episode) -> None:
        """
        Add a new episode to memory.

        Args:
            episode: Episode to store
        """
        self.episodes[episode.session_id] = episode
        self._save_episode(episode)

    def create_episode_from_conversation(
        self,
        session_id: str,
        conversation_summary: str,
        user_queries: List[str],
        tools_used: List[str],
        outcomes: Optional[List[str]] = None,
        key_entities: Optional[List[str]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Episode:
        """
        Create and store an episode from a conversation.

        Args:
            session_id: Unique session identifier
            conversation_summary: Summary of the conversation
            user_queries: List of user questions/requests
            tools_used: List of tools used during conversation
            outcomes: Success/failure notes
            key_entities: Important topics or entities
            user_preferences: Learned user preferences

        Returns:
            Created Episode
        """
        episode = Episode(
            session_id=session_id,
            timestamp=datetime.now(),
            summary=conversation_summary,
            user_queries=user_queries or [],
            tools_used=list(set(tools_used)) if tools_used else [],  # Deduplicate
            outcomes=outcomes or [],
            key_entities=key_entities or [],
            user_preferences=user_preferences or {}
        )

        self.add_episode(episode)
        return episode

    def get_episode(self, session_id: str) -> Optional[Episode]:
        """Retrieve a specific episode by session ID."""
        return self.episodes.get(session_id)

    def get_recent_episodes(self, n: int = 5) -> List[Episode]:
        """
        Get the N most recent episodes.

        Args:
            n: Number of episodes to retrieve

        Returns:
            List of recent episodes, sorted by timestamp (newest first)
        """
        sorted_episodes = sorted(
            self.episodes.values(),
            key=lambda e: e.timestamp,
            reverse=True
        )
        return sorted_episodes[:n]

    def search_episodes(self, query: str, max_results: int = 5) -> List[Episode]:
        """
        Search episodes by keyword matching.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of matching episodes, ranked by relevance
        """
        query_lower = query.lower()
        scored_episodes = []

        for episode in self.episodes.values():
            score = 0

            # Search in summary
            if query_lower in episode.summary.lower():
                score += 3

            # Search in user queries
            for user_query in episode.user_queries:
                if query_lower in user_query.lower():
                    score += 2

            # Search in key entities
            for entity in episode.key_entities:
                if query_lower in entity.lower():
                    score += 1

            if score > 0:
                scored_episodes.append((score, episode))

        # Sort by score (descending) and timestamp (descending)
        scored_episodes.sort(key=lambda x: (x[0], x[1].timestamp), reverse=True)

        return [episode for _, episode in scored_episodes[:max_results]]

    def get_episodes_by_tool(self, tool_name: str) -> List[Episode]:
        """
        Get all episodes where a specific tool was used.

        Args:
            tool_name: Name of the tool

        Returns:
            List of episodes using that tool
        """
        return [
            episode for episode in self.episodes.values()
            if tool_name in episode.tools_used
        ]

    def get_aggregated_preferences(self) -> Dict[str, Any]:
        """
        Aggregate user preferences across all episodes.

        Returns:
            Dictionary of common preferences
        """
        aggregated = {}

        for episode in self.episodes.values():
            for key, value in episode.user_preferences.items():
                if key not in aggregated:
                    aggregated[key] = []
                aggregated[key].append(value)

        # Convert to most common values
        preferences = {}
        for key, values in aggregated.items():
            if values:
                # For now, just take the most recent
                preferences[key] = values[-1]

        return preferences

    def get_tool_usage_stats(self) -> Dict[str, int]:
        """
        Get statistics on tool usage across episodes.

        Returns:
            Dictionary mapping tool names to usage counts
        """
        tool_counts = {}

        for episode in self.episodes.values():
            for tool in episode.tools_used:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1

        return dict(sorted(tool_counts.items(), key=lambda x: x[1], reverse=True))

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all episodic memory.

        Returns:
            Dictionary with memory statistics
        """
        return {
            "total_episodes": len(self.episodes),
            "date_range": {
                "earliest": min((e.timestamp for e in self.episodes.values()), default=None),
                "latest": max((e.timestamp for e in self.episodes.values()), default=None)
            },
            "total_queries": sum(len(e.user_queries) for e in self.episodes.values()),
            "tool_usage": self.get_tool_usage_stats(),
            "common_preferences": self.get_aggregated_preferences()
        }

    def clear_old_episodes(self, days: int = 30) -> int:
        """
        Remove episodes older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of episodes removed
        """
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        old_sessions = [
            session_id for session_id, episode in self.episodes.items()
            if episode.timestamp.timestamp() < cutoff
        ]

        for session_id in old_sessions:
            del self.episodes[session_id]
            # Remove file
            episode_file = self.storage_path / f"{session_id}.json"
            if episode_file.exists():
                episode_file.unlink()

        return len(old_sessions)

    def _save_episode(self, episode: Episode) -> None:
        """Save a single episode to disk."""
        episode_file = self.storage_path / f"{episode.session_id}.json"

        with open(episode_file, 'w') as f:
            json.dump(episode.to_dict(), f, indent=2)

    def _load_episodes(self) -> None:
        """Load all episodes from disk."""
        if not self.storage_path.exists():
            return

        for episode_file in self.storage_path.glob("*.json"):
            try:
                with open(episode_file, 'r') as f:
                    data = json.load(f)
                    episode = Episode.from_dict(data)
                    self.episodes[episode.session_id] = episode
            except Exception as e:
                print(f"Warning: Failed to load episode from {episode_file}: {e}")

    def save_all(self) -> None:
        """Save all episodes to disk."""
        for episode in self.episodes.values():
            self._save_episode(episode)

    def clear_all(self) -> None:
        """Clear all episodes from memory and disk."""
        for episode_file in self.storage_path.glob("*.json"):
            episode_file.unlink()

        self.episodes.clear()
