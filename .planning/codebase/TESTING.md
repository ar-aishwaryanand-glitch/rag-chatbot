# Testing Patterns

**Analysis Date:** 2026-02-09

## Test Framework

**Runner:**
- pytest (configured in `pytest.ini`)
- Config: `pytest.ini` at project root

**Assertion Library:**
- Standard assert statements (built-in Python)
- pytest assertions for exception testing: `pytest.raises()`

**Run Commands:**
```bash
pytest tests/ -v                # Run all tests with verbose output
pytest tests/unit/ -v           # Run only unit tests
pytest tests/integration/ -v    # Run only integration tests
pytest -m unit                  # Run tests marked as unit
pytest -m "not slow"            # Skip slow tests
pytest --cov=src                # Run with coverage report
make test                       # Via Makefile
make test-quick                 # Unit tests only (fast)
```

## Test File Organization

**Location:**
- Separate by type: `tests/unit/` for unit tests, `tests/integration/` for integration tests
- Shared fixtures: `tests/conftest.py` (309 lines, 19+ fixtures)
- Structure mirrors source: `tests/unit/test_embeddings.py` tests `src/embeddings.py`

**Naming:**
- Test files: `test_*.py` (e.g., `test_security.py`, `test_tools.py`)
- Test classes: `Test*` prefix (e.g., `TestToolResult`, `TestConversationMemory`)
- Test functions: `test_*` prefix (e.g., `test_basic_arithmetic`, `test_initialization`)

**Structure:**
```
tests/
├── conftest.py                  # Shared fixtures (19 fixtures)
├── __init__.py
├── test_security.py             # Security validation tests
├── test_bug_fixes.py            # Regression tests
├── unit/                        # Unit tests (fast, isolated)
│   ├── __init__.py
│   ├── test_embeddings.py       # Chunking, embedding generation
│   ├── test_rag_chain_unit.py   # RAG chain logic
│   ├── test_config.py           # Configuration loading
│   ├── test_memory.py           # Memory management
│   ├── test_tools.py            # Tool execution
│   └── test_vector_store.py     # Vector store operations
└── integration/                 # Integration tests (slower)
    ├── __init__.py
    ├── test_rag_chain.py        # End-to-end RAG flow
    ├── test_agent_system.py     # Agent orchestration
    ├── test_manager_agent.py    # Manager agent (813 lines)
    ├── test_qa_tools.py         # QA generation (928 lines)
    ├── test_qa_generation.py
    ├── test_relevance_filter.py
    ├── test_auto_index.py
    └── test_critical_fixes.py   # System-level fixes
```

## Test Structure

**Suite Organization:**
```python
class TestConversationMemory:
    """Tests for ConversationMemory class."""

    def test_initialization(self, conversation_memory):
        """Test conversation memory initialization."""
        assert conversation_memory.session_id == "test_session_123"
        assert conversation_memory.max_messages == 10
        assert conversation_memory.messages == []
        assert conversation_memory.turn_count == 0

    def test_add_user_message(self, conversation_memory):
        """Test adding a user message."""
        conversation_memory.add_message("user", "Hello!")
        assert len(conversation_memory.messages) == 1
        assert conversation_memory.messages[0].role == "user"
```

**Patterns:**
- Group tests by class/feature area
- Use descriptive class docstrings: `"""Tests for X functionality."""`
- One assertion focus per test
- AAA pattern (Arrange-Act-Assert):
```python
def test_add_message_with_metadata(self, conversation_memory):
    """Test adding message with metadata."""
    # Arrange
    metadata = {"tools_used": ["calculator"]}

    # Act
    conversation_memory.add_message("assistant", "Result: 42", metadata)

    # Assert
    assert conversation_memory.messages[0].metadata == metadata
```

## Mocking

**Framework:** `unittest.mock` (standard library)

**Patterns:**
```python
from unittest.mock import MagicMock, patch

# Pattern 1: Direct MagicMock creation
mock_llm = MagicMock()
mock_llm.invoke.return_value = MagicMock(content="Mock response")

# Pattern 2: Decorator-based patching
@patch('src.embeddings._get_cached_embedding_model')
def test_chunk_documents(self, mock_get_model):
    mock_get_model.return_value = MagicMock()
    # test code

# Pattern 3: Multiple patches
@patch('src.rag_chain.VectorStoreManager')
@patch('src.rag_chain.EmbeddingManager')
def test_rag_chain(self, mock_embed, mock_vs):
    # test code
```

**What to Mock:**
- LLM providers (Groq, Gemini): Mock `invoke()` method
- Vector stores: Mock `similarity_search()`, `add_documents()`
- Database connections: Mock cursor and connection objects
- External APIs: Web search, Confluence, news APIs
- File system operations: Use `temp_dir` fixture

**What NOT to Mock:**
- The class/function under test (test real implementation)
- Simple data structures (lists, dicts, dataclasses)
- Configuration objects (use `test_config` fixture)
- Internal helper methods (test through public API)

**Example from `tests/conftest.py`:**
```python
@pytest.fixture
def mock_llm():
    """Create a mock LLM that returns predictable responses."""
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content="Mock LLM response")
    return mock

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    mock = MagicMock()
    mock.similarity_search.return_value = []
    mock.add_documents.return_value = None
    return mock
```

## Fixtures and Factories

**Test Data:**
Located in `tests/conftest.py` (19 fixtures defined):

```python
@pytest.fixture
def sample_documents():
    """Create sample document chunks for testing."""
    from langchain_core.documents import Document

    return [
        Document(
            page_content="RAG stands for Retrieval-Augmented Generation.",
            metadata={"source": "rag-overview.md", "chunk_id": 0}
        ),
        Document(
            page_content="Vector databases store embeddings.",
            metadata={"source": "vector-databases.md", "chunk_id": 0}
        ),
    ]

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
```

**Factory Fixtures:**
```python
@pytest.fixture
def mock_llm_response():
    """Factory for creating mock LLM responses."""
    def _create_response(content: str):
        response = MagicMock()
        response.content = content
        return response
    return _create_response

# Usage
def test_something(mock_llm_response):
    response = mock_llm_response("Custom content")
```

**Location:**
- `tests/conftest.py`: All shared fixtures (organized by category with comments)
  - Environment Setup Fixtures
  - Tool Fixtures
  - Memory Fixtures
  - Mock LLM Fixtures
  - Vector Store Fixtures
  - Database Fixtures
  - Configuration Fixtures
  - JSON/Data Fixtures
  - Utility Fixtures

## Coverage

**Requirements:** Not enforced (no minimum threshold)

**Configuration:**
In `pytest.ini`:
```ini
[coverage:run]
source = src
omit =
    src/ui/*
    */__pycache__/*
    */tests/*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
```

**View Coverage:**
```bash
pytest --cov=src                      # Terminal report
pytest --cov=src --cov-report=html    # HTML report
```

**Coverage Strategy:**
- UI excluded (complex Streamlit integration)
- Focus on business logic (RAG chain, agents, tools)
- Pragmatic approach: Test critical paths, not 100% line coverage

## Test Types

**Unit Tests:**
- Scope: Single function/class in isolation
- Location: `tests/unit/`
- Speed: Fast (< 1 second per test)
- Dependencies: All external dependencies mocked
- Examples:
  - `tests/unit/test_tools.py`: Tool result dataclass, BaseTool interface, CalculatorTool logic
  - `tests/unit/test_memory.py`: Message creation, conversation memory, statistics
  - `tests/unit/test_embeddings.py`: Chunking, embedding generation
  - `tests/unit/test_config.py`: Configuration loading

**Integration Tests:**
- Scope: Multiple components working together
- Location: `tests/integration/`
- Speed: Slower (seconds to minutes)
- Dependencies: Some real, some mocked
- Examples:
  - `tests/integration/test_rag_chain.py`: RAGChain with retrieval and generation
  - `tests/integration/test_agent_system.py`: Agent with tools and memory
  - `tests/integration/test_qa_tools.py`: QA generation pipeline (928 lines)
  - `tests/integration/test_manager_agent.py`: Manager agent features (813 lines)

**E2E Tests:**
- Not implemented
- Would require real API keys, external services, full system

## Common Patterns

**Async Testing:**
Not used (codebase is synchronous)

**Error Testing:**
```python
def test_unsupported_provider_raises_error(self):
    """Test that unsupported provider raises ValueError."""
    from src.embeddings import _get_cached_embedding_model

    with pytest.raises(ValueError) as exc_info:
        _get_cached_embedding_model("unsupported", "model")

    assert "Unsupported embedding provider" in str(exc_info.value)
```

**State Verification:**
```python
def test_add_user_message(self, conversation_memory):
    """Test adding a user message."""
    conversation_memory.add_message("user", "Hello!")
    assert len(conversation_memory.messages) == 1
    assert conversation_memory.messages[0].role == "user"
    assert conversation_memory.turn_count == 1
```

**Import Testing:**
```python
def test_embedding_manager_import(self):
    """Test that EmbeddingManager can be imported."""
    from src.embeddings import EmbeddingManager
    assert EmbeddingManager is not None
```

**Parametrized-style Testing:**
```python
def test_query_sanitization(self):
    """Test that queries are properly sanitized."""
    test_queries = [
        "What is RAG?",
        "  Leading whitespace  ",
        "Query with\nnewlines",
        "",
    ]

    for query in test_queries:
        sanitized = query.strip()
        assert isinstance(sanitized, str)
```

**Context Formatting:**
```python
def test_context_formatting(self, sample_documents):
    """Test that documents are formatted correctly for context."""
    context_parts = []
    for doc in sample_documents:
        source = doc.metadata.get("source", "Unknown")
        context_parts.append(f"[Source: {source}]\n{doc.page_content}")

    context = "\n\n".join(context_parts)
    assert "rag-overview.md" in context
    assert "[Source:" in context
```

## Markers and Skip Conditions

**Defined Markers (in `pytest.ini`):**
```ini
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (may require external services)
    slow: Slow tests (database, LLM calls)
    requires_db: Tests requiring PostgreSQL
    requires_redis: Tests requiring Redis
    requires_api: Tests requiring external API keys
```

**Skip Markers (in `tests/conftest.py`):**
```python
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
```

**Usage:**
```python
@pytest.mark.integration
@pytest.mark.slow
def test_full_rag_pipeline():
    """Test complete RAG pipeline."""
    pass

@pytest.mark.skipif(True, reason="Requires actual API keys")
def test_real_llm_call():
    """Test with real LLM."""
    pass
```

**Run commands:**
```bash
pytest -m "not slow"           # Skip slow tests
pytest -m unit                 # Only unit tests
pytest -m integration          # Only integration tests
```

## Fixture Scope

**Session Scope:**
Used for one-time setup:
```python
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ.setdefault("LLM_PROVIDER", "groq")
    os.environ.setdefault("GROQ_API_KEY", "test_key_for_unit_tests")
    os.environ.setdefault("EMBEDDING_PROVIDER", "huggingface")
    os.environ.setdefault("USE_POSTGRES", "false")
    yield
```

**Function Scope (default):**
Most fixtures are function-scoped (fresh for each test):
```python
@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)
```

## Test Environment Setup

**Environment Variables:**
Set in session fixture (`tests/conftest.py`):
- `LLM_PROVIDER`: "groq"
- `GROQ_API_KEY`: "test_key_for_unit_tests" (for mocking)
- `EMBEDDING_PROVIDER`: "huggingface"
- `USE_POSTGRES`: "false"
- `USE_REDIS_QUEUE`: "false"
- `ENABLE_OBSERVABILITY`: "false"

**Temporary Resources:**
- `temp_dir`: Temporary directory (auto-cleanup)
- `temp_file`: Temporary test file
- `json_file`: Temporary JSON file with sample data

## Test Statistics

**Current Test Suite:**
- Total: ~6,574 lines of test code
- Unit tests: 7 modules
- Integration tests: 12 modules
- Shared fixtures: 19 in `conftest.py`

**Major Test Files:**
- `tests/integration/test_qa_tools.py`: 928 lines
- `tests/integration/test_manager_agent.py`: 813 lines
- `tests/test_bug_fixes.py`: 574 lines
- `tests/integration/test_manager_features.py`: 542 lines
- `tests/conftest.py`: 309 lines (fixtures)

**Key Test Areas:**
- Tool system: BaseTool, CalculatorTool, registry
- Memory system: ConversationMemory, episodic memory
- RAG chain: Document retrieval, answer generation
- Agent system: Executor, manager agent
- Configuration: Config loading, defaults
- Security: Sandbox escapes, symlink traversal, SSRF

---

*Testing analysis: 2026-02-09*
