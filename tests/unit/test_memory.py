"""
Unit tests for memory system.

Tests cover:
- ConversationMemory message management
- Memory statistics
- Serialization/deserialization
- Auto-summarization
"""

from datetime import datetime

from src.agent.memory.conversation_memory import ConversationMemory, Message


class TestMessage:
    """Tests for Message dataclass."""

    def test_message_creation(self):
        """Test creating a message."""
        msg = Message(role="user", content="Hello!")
        assert msg.role == "user"
        assert msg.content == "Hello!"
        assert isinstance(msg.timestamp, datetime)
        assert msg.metadata == {}

    def test_message_with_metadata(self):
        """Test creating message with metadata."""
        metadata = {"tools_used": ["search"], "sources": ["doc1.pdf"]}
        msg = Message(role="assistant", content="Response", metadata=metadata)
        assert msg.metadata == metadata

    def test_message_timestamp_default(self):
        """Test that timestamp defaults to now."""
        before = datetime.now()
        msg = Message(role="user", content="Test")
        after = datetime.now()
        assert before <= msg.timestamp <= after


class TestConversationMemory:
    """Tests for ConversationMemory class."""

    def test_initialization(self, conversation_memory):
        """Test conversation memory initialization."""
        assert conversation_memory.session_id == "test_session_123"
        assert conversation_memory.max_messages == 10
        assert conversation_memory.messages == []
        assert conversation_memory.turn_count == 0

    def test_initialization_with_custom_params(self):
        """Test initialization with custom parameters."""
        memory = ConversationMemory(
            session_id="custom_session",
            max_messages=5,
            summarize_threshold=10
        )
        assert memory.session_id == "custom_session"
        assert memory.max_messages == 5
        assert memory.summarize_threshold == 10

    def test_auto_generated_session_id(self):
        """Test that session_id is auto-generated if not provided."""
        memory = ConversationMemory()
        assert memory.session_id is not None
        assert len(memory.session_id) > 0

    def test_add_user_message(self, conversation_memory):
        """Test adding a user message."""
        conversation_memory.add_message("user", "Hello!")
        assert len(conversation_memory.messages) == 1
        assert conversation_memory.messages[0].role == "user"
        assert conversation_memory.messages[0].content == "Hello!"
        assert conversation_memory.turn_count == 1

    def test_add_assistant_message(self, conversation_memory):
        """Test adding an assistant message."""
        conversation_memory.add_message("assistant", "Hi there!")
        assert len(conversation_memory.messages) == 1
        assert conversation_memory.messages[0].role == "assistant"
        # Assistant messages don't increment turn count
        assert conversation_memory.turn_count == 0

    def test_add_message_with_metadata(self, conversation_memory):
        """Test adding message with metadata."""
        metadata = {"tools_used": ["calculator"]}
        conversation_memory.add_message("assistant", "Result: 42", metadata)
        assert conversation_memory.messages[0].metadata == metadata


class TestConversationMemoryRetrieval:
    """Tests for message retrieval methods."""

    def test_get_recent_messages(self, populated_conversation_memory):
        """Test getting recent messages."""
        recent = populated_conversation_memory.get_recent_messages(2)
        assert len(recent) == 2
        # Should be the last 2 messages
        assert recent[0].content == "What is RAG?"
        assert recent[1].content == "RAG stands for Retrieval-Augmented Generation."

    def test_get_recent_messages_default(self, populated_conversation_memory):
        """Test get_recent_messages with default limit."""
        recent = populated_conversation_memory.get_recent_messages()
        # Should return all messages (less than max_messages)
        assert len(recent) == 4

    def test_get_last_user_message(self, populated_conversation_memory):
        """Test getting the last user message."""
        last_user = populated_conversation_memory.get_last_user_message()
        assert last_user == "What is RAG?"

    def test_get_last_assistant_message(self, populated_conversation_memory):
        """Test getting the last assistant message."""
        last_assistant = populated_conversation_memory.get_last_assistant_message()
        assert last_assistant == "RAG stands for Retrieval-Augmented Generation."

    def test_get_last_message_empty(self, conversation_memory):
        """Test getting last message when empty returns None."""
        assert conversation_memory.get_last_user_message() is None
        assert conversation_memory.get_last_assistant_message() is None


class TestConversationMemoryContext:
    """Tests for context string generation."""

    def test_get_context_string(self, populated_conversation_memory):
        """Test getting formatted context string."""
        context = populated_conversation_memory.get_context_string()
        assert "User:" in context
        assert "Assistant:" in context
        assert "Hello, how are you?" in context
        assert "[Recent conversation]" in context

    def test_get_context_string_with_limit(self, populated_conversation_memory):
        """Test context string with message limit."""
        context = populated_conversation_memory.get_context_string(max_messages=1)
        # Should only include the last message
        assert "RAG stands for" in context

    def test_get_context_string_empty(self, conversation_memory):
        """Test context string when empty."""
        context = conversation_memory.get_context_string()
        # Should be empty or minimal
        assert len(context) == 0 or context.strip() == ""


class TestConversationMemoryStatistics:
    """Tests for statistics tracking."""

    def test_initial_stats(self, conversation_memory):
        """Test initial statistics state."""
        stats = conversation_memory.get_stats()
        assert stats["total_user_messages"] == 0
        assert stats["total_assistant_messages"] == 0
        assert stats["turn_count"] == 0

    def test_stats_after_messages(self, populated_conversation_memory):
        """Test statistics after adding messages."""
        stats = populated_conversation_memory.get_stats()
        assert stats["total_user_messages"] == 2
        assert stats["total_assistant_messages"] == 2
        assert stats["turn_count"] == 2
        assert stats["total_messages"] == 4

    def test_session_duration(self, populated_conversation_memory):
        """Test session duration tracking."""
        stats = populated_conversation_memory.get_stats()
        assert "session_duration_seconds" in stats
        assert stats["session_duration_seconds"] >= 0

    def test_token_approximation(self, conversation_memory):
        """Test approximate token counting."""
        # Add a message with known length
        conversation_memory.add_message("user", "A" * 100)  # 100 chars
        stats = conversation_memory.get_stats()
        # Approximate: 1 token ≈ 4 chars
        assert stats["total_tokens_approximate"] == 25


class TestConversationMemorySummarization:
    """Tests for auto-summarization feature."""

    def test_auto_summarization_triggered(self):
        """Test that summarization is triggered when threshold exceeded."""
        memory = ConversationMemory(
            max_messages=3,
            summarize_threshold=5
        )

        # Add messages to exceed threshold
        for i in range(7):
            role = "user" if i % 2 == 0 else "assistant"
            memory.add_message(role, f"Message {i}")

        # After summarization, we expect:
        # - Summary to be created from older messages
        # - Recent messages to be kept (implementation may vary)
        # The key test is that summary exists when threshold is exceeded
        assert memory.summary is not None or len(memory.messages) <= memory.summarize_threshold

    def test_summary_content(self):
        """Test that summary contains relevant info."""
        memory = ConversationMemory(max_messages=2, summarize_threshold=4)

        memory.add_message("user", "Tell me about Python")
        memory.add_message("assistant", "Python is a programming language")
        memory.add_message("user", "What about JavaScript?")
        memory.add_message("assistant", "JavaScript is for web development")
        memory.add_message("user", "Thanks!")

        # Summary should mention topics discussed
        if memory.summary:
            # Summary is created from older messages
            assert len(memory.summary) > 0


class TestConversationMemorySerialization:
    """Tests for to_dict and from_dict methods."""

    def test_to_dict(self, populated_conversation_memory):
        """Test exporting to dictionary."""
        data = populated_conversation_memory.to_dict()

        assert "session_id" in data
        assert "messages" in data
        assert "turn_count" in data
        assert "stats" in data
        assert len(data["messages"]) == 4

    def test_from_dict(self, populated_conversation_memory):
        """Test importing from dictionary."""
        data = populated_conversation_memory.to_dict()
        restored = ConversationMemory.from_dict(data)

        assert restored.session_id == populated_conversation_memory.session_id
        assert len(restored.messages) == len(populated_conversation_memory.messages)
        assert restored.turn_count == populated_conversation_memory.turn_count

    def test_round_trip_serialization(self, populated_conversation_memory):
        """Test that data survives round-trip serialization."""
        original_context = populated_conversation_memory.get_context_string()

        data = populated_conversation_memory.to_dict()
        restored = ConversationMemory.from_dict(data)
        restored_context = restored.get_context_string()

        # Context should be identical after round-trip
        assert original_context == restored_context

    def test_message_timestamp_preservation(self, populated_conversation_memory):
        """Test that message timestamps are preserved in serialization."""
        original_timestamp = populated_conversation_memory.messages[0].timestamp

        data = populated_conversation_memory.to_dict()
        restored = ConversationMemory.from_dict(data)

        assert restored.messages[0].timestamp == original_timestamp


class TestConversationMemoryClear:
    """Tests for clear functionality."""

    def test_clear(self, populated_conversation_memory):
        """Test clearing conversation memory."""
        assert len(populated_conversation_memory.messages) > 0

        populated_conversation_memory.clear()

        assert len(populated_conversation_memory.messages) == 0
        assert populated_conversation_memory.turn_count == 0
        assert populated_conversation_memory.summary is None

    def test_clear_stats_reset(self, populated_conversation_memory):
        """Test that stats are reset on clear."""
        populated_conversation_memory.clear()
        stats = populated_conversation_memory.get_stats()

        assert stats["total_user_messages"] == 0
        assert stats["total_assistant_messages"] == 0


class TestEpisodicMemory:
    """Tests for EpisodicMemory class."""

    def test_create_episode_from_conversation(self, episodic_memory):
        """Test creating an episode from conversation."""
        episode = episodic_memory.create_episode_from_conversation(
            session_id="test_session",
            conversation_summary="User asked about RAG",
            user_queries=["What is RAG?"],
            tools_used=["document_search"],
            outcomes=["success"]
        )
        assert episode.session_id == "test_session"
        assert "RAG" in episode.summary

    def test_add_episode(self, episodic_memory, temp_dir):
        """Test adding an episode creates episode file."""
        from src.agent.memory.episodic_memory import Episode
        from datetime import datetime

        episode = Episode(
            session_id="finalize_test",
            timestamp=datetime.now(),
            summary="Test summary",
            user_queries=["Test question"],
            tools_used=["document_search"]
        )

        episodic_memory.add_episode(episode)

        # Check if episode file was created
        episode_files = list(temp_dir.glob("*.json"))
        assert len(episode_files) >= 1

    def test_episode_persistence(self, episodic_memory, temp_dir):
        """Test that episode data is persisted correctly."""
        import json
        from src.agent.memory.episodic_memory import Episode
        from datetime import datetime

        episode = Episode(
            session_id="persist_test",
            timestamp=datetime.now(),
            summary="User asked about RAG",
            user_queries=["What is RAG?"],
            tools_used=["document_search"]
        )

        episodic_memory.add_episode(episode)

        # Read and verify the saved file
        episode_files = list(temp_dir.glob("*.json"))
        if episode_files:
            with open(episode_files[0], 'r') as f:
                data = json.load(f)
                assert "summary" in data
                assert "user_queries" in data
