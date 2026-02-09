# Coding Conventions

**Analysis Date:** 2026-02-09

## Naming Patterns

**Files:**
- Snake_case for Python files: `config.py`, `embeddings.py`, `agent_executor_v3.py`
- Feature-specific versioning: `agent_executor_v3.py` (Phase 3), tool names with suffixes like `_tool.py`
- Descriptive module names that reflect purpose: `conversation_memory.py`, `document_manager.py`

**Classes:**
- PascalCase for class names: `EmbeddingManager`, `RAGChain`, `ConversationMemory`, `AgentExecutorV3`
- Descriptive compound names when appropriate: `PolicyEngine`, `CheckpointManager`, `VectorStoreManager`

**Functions:**
- snake_case for function names: `get_reranker()`, `_initialize_embedding_model()`, `chunk_documents()`
- Private/internal functions prefixed with underscore: `_detect_vector_store_type()`, `_initialize_backend()`
- Factory/loader functions use get_ prefix: `get_reranker()`, `get_observability()`, `get_checkpoint_manager()`

**Variables:**
- snake_case for variables: `vector_store_type`, `embedding_manager`, `session_id`
- Private module-level variables prefixed with underscore: `_reranker` (cached lazy-loaded module)
- Class constants in UPPER_CASE: `AGENT_ENABLED`, `LLM_PROVIDER`, `CHUNK_SIZE`

**Types:**
- Type hints used throughout: `List[str]`, `Dict[str, Any]`, `Optional[str]`
- TypedDict for structured state: `AgentState` defined as TypedDict with explicit field types
- Literal types for constrained options: `VectorStoreType = Literal["faiss", "pinecone"]`

## Code Style

**Formatting:**
- Line length: Generally follows Python conventions (80-100 char soft limit)
- Indentation: 4 spaces consistently throughout codebase
- String quotes: Double quotes preferred for consistency
- No explicit formatter tool configured (no Black, Ruff formatter)

**Linting:**
- **Tool:** Ruff (configured in `ruff.toml`)
- **Enabled rules:** E (pycodestyle errors), F (Pyflakes), W (pycodestyle warnings)
- **Ignored rules:**
  - `E402`: Module level import not at top (allowed in `src/ui/streamlit_app_agent.py` for sys.path manipulation)
  - `E501`: Line too long (not enforced)
- **Per-file ignores:**
  - Streamlit app: Allows late imports for setup needs
  - Test files: Allows unused variables `F841` for mock setup
  - Optional dependency imports: Allows unused imports `F401` to check availability

## Import Organization

**Order:**
1. Standard library imports (`os`, `sys`, `json`, `time`, `datetime`, `re`, etc.)
2. Third-party library imports (`langchain`, `langgraph`, `pytest`, `dotenv`, etc.)
3. Relative imports from current package (`.config`, `.agent_state`, etc.)
4. Lazy imports for performance (conditional imports within functions)

**Path Aliases:**
- Absolute imports from project root: `from src.config import Config`
- Relative imports within same package: `from .agent_state import AgentState`
- TYPE_CHECKING blocks for avoiding circular imports: Used in `rag_chain.py` for VectorStoreManager type hints

**Example pattern from `src/agent/agent_executor_v3.py`:**
```python
import re
import time
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from .agent_state import AgentState
from .tool_registry import ToolRegistry
from src.observability import get_observability

try:
    from src.policy import PolicyEngine
    POLICY_ENGINE_AVAILABLE = True
except ImportError:
    POLICY_ENGINE_AVAILABLE = False
```

## Error Handling

**Patterns:**
- Try/except blocks around optional feature initialization: Policy engine, checkpoint manager, observability
- Graceful degradation: If optional feature fails, set to None and print warning message
- Exception details printed for debugging: `print(f"⚠️ Checkpointing disabled: {e}")`
- ValueError and RuntimeError for meaningful error messages: `raise ValueError("Checkpoint storage not available...")`

**Error message conventions:**
- Include emoji prefix for user-visible errors: `⚠️ Warning`, `❌ Error`, `✅ Success`
- Include context in error messages: "Requires PostgreSQL connection", "Enable USE_POSTGRES=true"
- Print full tracebacks in debug contexts: `traceback.format_exc()`

**Example from `src/agent/agent_executor_v3.py`:**
```python
try:
    from src.database import get_checkpoint_manager
    self.checkpoint_manager = get_checkpoint_manager()
    if not self.checkpoint_manager.is_available():
        self.checkpoint_manager = None
except Exception as e:
    print(f"⚠️  Checkpointing disabled: {e}")
    self.checkpoint_manager = None
```

## Logging

**Framework:** `print()` statements (no logging module)

**Patterns:**
- Progress indicators with emoji: `"✂️  Split {len(documents)} documents into {len(chunks)} chunks"`
- Status updates: `"📦 Document Manager initialized with {self.vector_store_type.upper()} backend"`
- Debug output: `"[DEBUG] Agent is None, initializing..."`
- Warning/error indicators: `"⚠️  Failed to auto-save memory: {e}"`

**When to Log:**
- User-visible operations (document splitting, model initialization)
- Debug state transitions in agent execution
- Warning conditions (failed optional features, retry attempts)
- Success confirmations (initialization complete, data saved)

**Example pattern from `src/embeddings.py`:**
```python
print(f"✂️  Split {len(documents)} documents into {len(chunks)} chunks")
print(f"🔢 Generated embeddings for {len(texts)} texts")
```

## Comments

**When to Comment:**
- Class-level docstrings explaining purpose and features: All classes have docstrings
- Method docstrings with Args, Returns, Raises sections
- Complex algorithm explanations or non-obvious logic
- Configuration-related comments explaining what values mean

**JSDoc/TSDoc:**
- Python docstring format used throughout
- Google-style docstrings with `Args:`, `Returns:`, `Raises:` sections
- Example from `src/agent/memory/conversation_memory.py`:
```python
"""
Add a message to conversation history.

Args:
    role: Message role ('user', 'assistant', 'system')
    content: Message content
    metadata: Optional metadata (tool used, sources, etc.)
"""
```

**Module docstrings:**
- Always present at file start: `"""Text chunking and embedding generation for RAG Agent POC."""`
- Describe file purpose, key classes, and features provided

## Function Design

**Size:**
- Most functions 20-50 lines
- Methods with complex logic (agent execution, tool routing) may exceed 100 lines
- Helper functions kept short (10-20 lines)

**Parameters:**
- Type hints on all parameters: `documents: List`, `session_id: Optional[str] = None`
- Default values for optional parameters: `batch_size: int = None`, `show_progress: bool = True`
- Keep parameter count < 5; use config objects for many settings

**Return Values:**
- Type hints on all return values: `-> List[Document]`, `-> Optional[str]`
- Return None explicitly for no result: `-> Optional[List[str]]`
- Return dictionaries with consistent keys for complex results:
```python
def ask(self, question: str) -> Dict[str, Any]:
    return {
        "question": str,
        "answer": str,
        "context": List[Document],
        "sources": List[Dict[str, str]]
    }
```

**Example from `src/embeddings.py`:**
```python
def chunk_documents(self, documents: List) -> List[Document]:
    """
    Split documents into smaller chunks.

    Args:
        documents: List of document dictionaries with 'content' and 'metadata',
                   or LangChain Document objects

    Returns:
        List of LangChain Document objects (chunks)
    """
```

## Module Design

**Exports:**
- Public API explicitly imported: Classes and main functions available at module level
- Private functions/variables prefixed with underscore: `_get_cached_embedding_model()`, `_reranker`
- Direct instantiation preferred over factory functions where simple

**Barrel Files:**
- Limited use of `__init__.py` barrel files in agent modules
- Selective imports: `from src.agent import AgentExecutorV3` vs full module export
- Module organization by feature: `agent/`, `database/`, `ui/`, `policy/` directories

**Example from `src/agent/__init__.py`:**
```python
# Selective exports, not all module contents
from .agent_executor_v3 import AgentExecutorV3
from .agent_state import AgentState
```

## Configuration

**Pattern:**
- Single `Config` class in `src/config.py` with class attributes
- Environment variables read with `os.getenv()` with sensible defaults
- Config loaded once at module import: No reloading or dynamic updates
- Nested configuration sections with comments: LLM, Agent, Advanced Features, Observability

**Example from `src/config.py`:**
```python
class Config:
    """Configuration settings for the RAG system."""

    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Chunking Configuration
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
```

## Type System

**Usage:**
- Type hints mandatory on function signatures
- `Optional[T]` for nullable values
- `Union[A, B]` for multiple possible types
- `Literal["option1", "option2"]` for constrained strings
- `Dict[str, Any]` for flexible dictionaries
- `List[T]` for sequences

**Dataclasses:**
- Used for message structures: `Message` dataclass with role, content, timestamp, metadata
- Used for structured state: `AgentState` TypedDict
- Default values with `field(default_factory=...)` for mutable defaults

---

*Convention analysis: 2026-02-09*
