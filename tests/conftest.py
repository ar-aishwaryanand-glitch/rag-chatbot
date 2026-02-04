"""
Pytest fixtures and configuration for RAG Agent tests.

This module provides shared fixtures used across all test modules.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Generator, Dict, Any
from unittest.mock import MagicMock

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# Environment Setup Fixtures
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Set minimal env vars for testing (don't need real API keys for unit tests)
    os.environ.setdefault("LLM_PROVIDER", "groq")
    os.environ.setdefault("GROQ_API_KEY", "test_key_for_unit_tests")
    os.environ.setdefault("EMBEDDING_PROVIDER", "huggingface")
    os.environ.setdefault("USE_POSTGRES", "false")
    os.environ.setdefault("USE_REDIS_QUEUE", "false")
    os.environ.setdefault("ENABLE_OBSERVABILITY", "false")
    yield


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def temp_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary file for testing."""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("Test content for unit tests.")
    yield file_path


# ============================================================================
# Tool Fixtures
# ============================================================================

@pytest.fixture
def mock_tool():
    """Create a mock tool for testing."""
    from src.agent.tools.base_tool import BaseTool

    class MockTool(BaseTool):
        @property
        def name(self) -> str:
            return "mock_tool"

        @property
        def description(self) -> str:
            return "A mock tool for testing purposes"

        def _run(self, query: str = "") -> str:
            return f"Mock result for: {query}"

    return MockTool()


@pytest.fixture
def calculator_tool():
    """Create a calculator tool instance."""
    from src.agent.tools.calculator_tool import CalculatorTool
    return CalculatorTool()


@pytest.fixture
def tool_registry():
    """Create an empty tool registry."""
    from src.agent.tool_registry import ToolRegistry
    return ToolRegistry()


@pytest.fixture
def populated_tool_registry(tool_registry, mock_tool, calculator_tool):
    """Create a tool registry with some tools registered."""
    tool_registry.register(mock_tool)
    tool_registry.register(calculator_tool)
    return tool_registry


# ============================================================================
# Memory Fixtures
# ============================================================================

@pytest.fixture
def conversation_memory():
    """Create a fresh conversation memory instance."""
    from src.agent.memory.conversation_memory import ConversationMemory
    return ConversationMemory(session_id="test_session_123")


@pytest.fixture
def populated_conversation_memory(conversation_memory):
    """Create a conversation memory with some messages."""
    conversation_memory.add_message("user", "Hello, how are you?")
    conversation_memory.add_message("assistant", "I'm doing well, thank you!")
    conversation_memory.add_message("user", "What is RAG?")
    conversation_memory.add_message(
        "assistant",
        "RAG stands for Retrieval-Augmented Generation.",
        {"tools_used": ["document_search"]}
    )
    return conversation_memory


@pytest.fixture
def episodic_memory(temp_dir):
    """Create an episodic memory instance with temporary storage."""
    from src.agent.memory.episodic_memory import EpisodicMemory
    return EpisodicMemory(storage_path=temp_dir)


# ============================================================================
# Mock LLM Fixtures
# ============================================================================

@pytest.fixture
def mock_llm():
    """Create a mock LLM that returns predictable responses."""
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content="Mock LLM response")
    return mock


@pytest.fixture
def mock_llm_response():
    """Factory for creating mock LLM responses."""
    def _create_response(content: str):
        response = MagicMock()
        response.content = content
        return response
    return _create_response


# ============================================================================
# Vector Store Fixtures
# ============================================================================

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    mock = MagicMock()
    mock.similarity_search.return_value = []
    mock.add_documents.return_value = None
    return mock


@pytest.fixture
def sample_documents():
    """Create sample document chunks for testing."""
    from langchain_core.documents import Document

    return [
        Document(
            page_content="RAG stands for Retrieval-Augmented Generation. It combines retrieval with generation.",
            metadata={"source": "rag-overview.md", "chunk_id": 0}
        ),
        Document(
            page_content="Vector databases store embeddings for semantic search.",
            metadata={"source": "vector-databases.md", "chunk_id": 0}
        ),
        Document(
            page_content="LangChain is a framework for building LLM applications.",
            metadata={"source": "langchain-intro.md", "chunk_id": 0}
        ),
    ]


# ============================================================================
# Database Fixtures (for integration tests)
# ============================================================================

@pytest.fixture
def mock_db_connection():
    """Create a mock database connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return mock_conn


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_config():
    """Create a test configuration dict."""
    return {
        "llm_provider": "groq",
        "embedding_provider": "huggingface",
        "chunk_size": 800,
        "chunk_overlap": 100,
        "top_k_results": 3,
        "use_postgres": False,
        "use_redis": False,
    }


# ============================================================================
# JSON/Data Fixtures
# ============================================================================

@pytest.fixture
def sample_episode_data() -> Dict[str, Any]:
    """Create sample episode data for testing."""
    return {
        "session_id": "test_session_123",
        "timestamp": datetime.now().isoformat(),
        "summary": "User asked about RAG and machine learning",
        "interactions": [
            {
                "user_message": "What is RAG?",
                "assistant_response": "RAG is Retrieval-Augmented Generation.",
                "tool_used": "document_search",
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
        ],
        "tools_used": ["document_search"],
        "key_entities": ["RAG", "retrieval", "generation"]
    }


@pytest.fixture
def sample_checkpoint_data() -> Dict[str, Any]:
    """Create sample checkpoint data for testing."""
    return {
        "thread_id": "test_thread_123",
        "checkpoint_id": "cp_abc123",
        "state": {
            "query": "What is RAG?",
            "final_answer": "RAG stands for Retrieval-Augmented Generation.",
            "tools_used": ["document_search"],
            "conversation_messages": []
        },
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "session_id": "test_session"
        }
    }


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def capture_print(capsys):
    """Helper to capture print output."""
    def _capture():
        return capsys.readouterr().out
    return _capture


@pytest.fixture
def json_file(temp_dir) -> Generator[Path, None, None]:
    """Create a temporary JSON file."""
    file_path = temp_dir / "test_data.json"
    data = {"key": "value", "nested": {"a": 1, "b": 2}}
    file_path.write_text(json.dumps(data))
    yield file_path


# ============================================================================
# Skip Markers
# ============================================================================

# Skip if no API key
requires_groq_api = pytest.mark.skipif(
    os.environ.get("GROQ_API_KEY", "test_key").startswith("test_"),
    reason="Requires real GROQ_API_KEY"
)

requires_postgres = pytest.mark.skipif(
    os.environ.get("USE_POSTGRES", "false").lower() != "true",
    reason="Requires PostgreSQL connection"
)

requires_redis = pytest.mark.skipif(
    os.environ.get("USE_REDIS_QUEUE", "false").lower() != "true",
    reason="Requires Redis connection"
)
