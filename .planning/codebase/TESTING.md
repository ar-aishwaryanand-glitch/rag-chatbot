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
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest tests/unit               # Run only unit tests
pytest tests/integration        # Run only integration tests
pytest -m unit                  # Run tests marked @pytest.mark.unit
pytest -m integration           # Run tests marked @pytest.mark.integration
pytest --cov=src               # Coverage report
pytest tests/ -v --tb=short    # Verbose with short traceback
```

**Test Discovery:**
- Test files: `test_*.py` and `*_test.py`
- Test classes: `Test*` prefix
- Test functions: `test_*` prefix
- All tests located in `tests/` directory

## Test File Organization

**Location:**
- Co-located by feature, not mixed: Separate directories for unit and integration tests
- Structure mirrors source structure: `tests/unit/test_embeddings.py` mirrors `src/embeddings.py`
- Fixtures in shared `tests/conftest.py` file

**Directory Layout:**
```
tests/
├── conftest.py                  # Shared fixtures and configuration
├── unit/                        # Fast, isolated unit tests
│   ├── __init__.py
│   ├── test_embeddings.py
│   ├── test_rag_chain_unit.py
│   ├── test_config.py
│   ├── test_memory.py
│   ├── test_tools.py
│   └── test_vector_store.py
└── integration/                 # Tests requiring services/APIs
    ├── __init__.py
    ├── test_rag_chain.py
    ├── test_agent_system.py
    ├── test_manager_agent.py
    ├── test_qa_tools.py
    └── test_critical_fixes.py
```

**Naming:**
- `test_<module_name>.py`: Matches source module being tested
- Suffixes for test type: `_unit.py`, no suffix for integration
- Classes group related tests: `TestEmbeddingManagerChunking`, `TestRAGChainQuery`

## Test Structure

**Suite Organization:**
```python
class TestEmbeddingManagerImport:
    """Tests for EmbeddingManager imports."""

    def test_embedding_manager_import(self):
        """Test that EmbeddingManager can be imported."""
        from src.embeddings import EmbeddingManager
        assert EmbeddingManager is not None

    def test_cached_embedding_function_import(self):
        """Test that cached embedding function exists."""
        from src.embeddings import _get_cached_embedding_model
        assert _get_cached_embedding_model is not None


class TestEmbeddingManagerChunking:
    """Tests for document chunking functionality."""

    @patch('src.embeddings._get_cached_embedding_model')
    def test_chunk_documents_basic(self, mock_get_model):
        """Test basic document chunking."""
        from src.embeddings import EmbeddingManager

        mock_get_model.return_value = MagicMock()
        manager = EmbeddingManager()
        # ... test continues
```

**Patterns:**

1. **Class grouping:** Tests organized by feature/class, not by test type
2. **Descriptive test names:** `test_chunk_documents_preserves_metadata` not `test_1`
3. **One assertion focus per test:** Each test validates single behavior
4. **AAA pattern (Arrange, Act, Assert):**
   - Arrange: Set up test data and mocks
   - Act: Call the function/method being tested
   - Assert: Verify expected behavior

**Example from `tests/unit/test_embeddings.py`:**
```python
@patch('src.embeddings._get_cached_embedding_model')
def test_chunk_documents_preserves_metadata(self, mock_get_model):
    """Test that metadata is preserved during chunking."""
    # Arrange
    from src.embeddings import EmbeddingManager
    mock_get_model.return_value = MagicMock()
    manager = EmbeddingManager()
    documents = [
        {
            "content": "Test content here.",
            "metadata": {"source": "file.md", "topic": "testing", "author": "test"}
        }
    ]

    # Act
    chunks = manager.chunk_documents(documents)

    # Assert
    assert chunks[0].metadata["source"] == "file.md"
    assert chunks[0].metadata["topic"] == "testing"
    assert chunks[0].metadata["author"] == "test"
```

## Mocking

**Framework:** `unittest.mock` (Python standard library)

**Patterns:**
```python
from unittest.mock import MagicMock, patch

# Method 1: Direct instantiation with MagicMock
mock_vector_store = MagicMock()
mock_vector_store.similarity_search.return_value = []

# Method 2: Decorator-based patching
@patch('src.embeddings._get_cached_embedding_model')
def test_method(self, mock_get_model):
    mock_get_model.return_value = MagicMock()
    # test code

# Method 3: Context manager patching
with patch('src.agent.agent_executor_v3.ChatGroq') as mock_llm_class:
    mock_llm = MagicMock()
    mock_llm_class.return_value = mock_llm
    # test code
```

**Patch locations:**
- Patch at import location, not source: `@patch('src.rag_chain.VectorStoreManager')`
- Avoid patching built-ins unnecessarily
- Use `patch.dict` for environment variable mocking: `patch.dict('sys.modules', {'module': MagicMock()})`

**What to Mock:**
- External dependencies: LLMs, vector stores, databases
- API calls: Web search, Confluence, external services
- File I/O: Use `temp_dir` fixture instead
- System features: Time, environment variables

**What NOT to Mock:**
- Classes being tested directly (test the real implementation)
- Internal helper methods (test through public interface)
- Data structures and simple utilities
- Configuration loading (use test config fixture)

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
Fixtures in `tests/conftest.py` provide reusable test objects:

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
            page_content="Vector databases store embeddings for semantic search.",
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

# Usage in test
def test_something(self, mock_llm_response):
    response1 = mock_llm_response("First response")
    response2 = mock_llm_response("Second response")
```

**Location:**
- All shared fixtures in `tests/conftest.py` (19 fixtures defined)
- Test-specific fixtures in same test file (if not reused)
- Fixtures organized by category with comment sections:
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

**Requirements:** Not enforced (no CI check)

**Configuration in `pytest.ini`:**
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
pytest --cov=src --cov-report=html    # Generate HTML report
pytest --cov=src                      # Terminal report
```

**Coverage Targets:**
- UI components excluded from coverage (complex Streamlit integration)
- Pragmatic coverage: Focus on business logic, not 100% line coverage

## Test Types

**Unit Tests (location: `tests/unit/`):**
- Scope: Single function/method/class in isolation
- Approach: Mock all external dependencies
- Speed: Fast (< 1 second per test)
- Examples:
  - `test_embeddings.py`: EmbeddingManager chunking, embedding generation
  - `test_config.py`: Config class loading and defaults
  - `test_memory.py`: Message creation, conversation memory management
  - `test_tools.py`: Individual tool functionality
  - `test_vector_store.py`: Vector store operations

**Integration Tests (location: `tests/integration/`):**
- Scope: Multiple components working together
- Approach: Use real or semi-mocked dependencies
- Speed: Slower (seconds to minutes)
- Examples:
  - `test_rag_chain.py`: RAGChain with document retrieval
  - `test_agent_system.py`: Agent with tools and memory
  - `test_manager_agent.py`: Manager agent features
  - `test_qa_tools.py`: QA generation pipeline
  - `test_critical_fixes.py`: Cross-cutting concerns

**E2E Tests:**
- Not implemented in current test suite
- Would require: Full system setup, real API keys, external services

## Markers

**Defined in `pytest.ini`:**
```ini
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (may require external services)
    slow: Slow tests (database, LLM calls)
    requires_db: Tests requiring PostgreSQL
    requires_redis: Tests requiring Redis
    requires_api: Tests requiring external API keys
```

**Usage:**
```python
@pytest.mark.slow
@pytest.mark.requires_api
def test_llm_call():
    """Test that calls actual LLM."""
    pass

# Run specific marker
pytest -m "not slow"              # Skip slow tests
pytest -m "requires_api"          # Run only tests needing APIs
```

**Skip Markers (defined in `conftest.py`):**
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

## Common Patterns

**Async Testing:**
- Not implemented (codebase is synchronous)
- Would use: `@pytest.mark.asyncio` decorator

**Error Testing:**
```python
def test_unsupported_provider_raises_error(self):
    """Test that unsupported provider raises ValueError."""
    from src.embeddings import _get_cached_embedding_model

    _get_cached_embedding_model.cache_clear()

    with pytest.raises(ValueError) as exc_info:
        _get_cached_embedding_model("unsupported_provider", "model")

    assert "Unsupported embedding provider" in str(exc_info.value)
```

**Parametrized Tests:**
- Used where multiple similar cases should be tested
- Example: Query sanitization test with multiple inputs

```python
def test_query_sanitization(self):
    """Test that queries are properly sanitized."""
    test_queries = [
        "What is RAG?",
        "  Leading whitespace  ",
        "Query with\nnewlines",
        "",  # Empty query
    ]

    for query in test_queries:
        sanitized = query.strip()
        assert isinstance(sanitized, str)
```

**Import Testing:**
```python
def test_embedding_manager_import(self):
    """Test that EmbeddingManager can be imported."""
    from src.embeddings import EmbeddingManager
    assert EmbeddingManager is not None
```

**State Verification:**
```python
def test_initialization(self, conversation_memory):
    """Test conversation memory initialization."""
    assert conversation_memory.session_id == "test_session_123"
    assert conversation_memory.max_messages == 10
    assert conversation_memory.messages == []
    assert conversation_memory.turn_count == 0
```

## Fixture Scope

**Session Scope (`@pytest.fixture(scope="session")`):**
```python
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ.setdefault("LLM_PROVIDER", "groq")
    os.environ.setdefault("GROQ_API_KEY", "test_key_for_unit_tests")
    # ... more setup
    yield
```

**Function Scope (default):**
- Fresh fixture for each test
- Most fixtures are function-scoped
- Used for mocks, temporary files, test data

**Cleanup Pattern:**
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

## Test Statistics

**Current Coverage:**
- 7 unit test modules
- 12 integration test modules
- ~100+ individual test functions
- Configuration verification tests
- Memory system tests
- RAG chain tests
- Agent system tests
- Tool functionality tests

**Test Modules:**
- `tests/unit/test_embeddings.py`: 6+ test classes, embedding/chunking validation
- `tests/unit/test_rag_chain_unit.py`: RAG chain unit behavior
- `tests/unit/test_config.py`: Configuration loading and defaults
- `tests/unit/test_memory.py`: Memory management and statistics
- `tests/unit/test_tools.py`: Tool registry and execution
- `tests/unit/test_vector_store.py`: Vector store operations
- `tests/integration/test_rag_chain.py`: End-to-end RAG pipeline
- `tests/integration/test_agent_system.py`: Agent orchestration
- `tests/integration/test_manager_agent.py`: Manager agent features
- `tests/integration/test_qa_tools.py`: QA generation tooling
- `tests/integration/test_critical_fixes.py`: System-level validations

---

*Testing analysis: 2026-02-09*
