# Coding Conventions

**Analysis Date:** 2026-02-09

## Naming Patterns

**Files:**
- Python modules use `snake_case`: `rag_chain.py`, `document_loader.py`, `vector_store.py`
- Test files prefix with `test_`: `test_security.py`, `test_tools.py`, `test_memory.py`
- Tool modules suffix with `_tool`: `calculator_tool.py`, `web_search_tool.py`, `code_executor_tool.py`
- Entry scripts use descriptive names: `run_agent_ui.py`, `queue_worker.py`

**Functions:**
- Use `snake_case`: `load_text_files()`, `get_reranker()`, `add_message()`
- Private methods prefix with underscore: `_run()`, `_compute_checksum()`, `_auto_summarize()`
- Factory functions prefix with `get_`: `get_observability()`, `get_auto_indexer()`, `get_document_manager()`

**Variables:**
- Use `snake_case`: `session_id`, `turn_count`, `max_messages`
- Constants use `UPPER_CASE`: `TOP_K_RESULTS`, `CHUNK_SIZE`, `LLM_PROVIDER`
- Boolean flags prefix with verb: `enable_memory`, `enable_reflection`, `verify_integrity`

**Classes:**
- Use `PascalCase`: `RAGChain`, `VectorStoreManager`, `ConversationMemory`, `AgentExecutorV3`
- Abstract base classes: `BaseTool`, `BaseAgent`
- Dataclasses for data containers: `Message`, `ToolResult`, `AgentState`

**Types:**
- Enums use `PascalCase`: `PolicyAction`, `TaskStatus`

## Code Style

**Formatting:**
- Tool: Ruff (configured in `ruff.toml`)
- Line length: Max 100-120 characters (E501 ignored, handled by formatter)
- Indentation: 4 spaces

**Linting:**
- Tool: Ruff with Pyflakes and pycodestyle rules
- Enabled rules: E (pycodestyle errors), F (Pyflakes), W (pycodestyle warnings)
- Key ignored rules:
  - E402: Module level import not at top (for Streamlit path setup)
  - E501: Line too long (handled by formatter)
  - F841: Unused variables in test files (for mocking)
  - F401: Unused imports for optional dependencies and availability checks

**Syntax checking:**
- Uses `python -m py_compile` for validation (see `Makefile`)

## Import Organization

**Order:**
1. Standard library imports (sorted alphabetically)
2. Third-party imports (LangChain, external dependencies)
3. Local project imports (using relative imports from `src/`)

**Pattern observed:**
```python
# Standard library
import os
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Third-party
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

# Local
from .config import Config
from .embeddings import EmbeddingManager
```

**Path Aliases:**
- No path aliases configured
- Uses relative imports within `src/`: `from .config import Config`
- Tests use absolute imports: `from src.agent.tools.base_tool import BaseTool`

**Lazy imports:**
- Optional dependencies imported inside functions with try/except:
```python
try:
    from docx import Document
except ImportError:
    raise ImportError("python-docx not installed. Run: pip install python-docx")
```

## Error Handling

**Patterns:**
- Specific exception types: `except ImportError:`, `except SyntaxError as e:`
- Always capture exception as `e`: `except Exception as e:`
- Return structured error responses in tools via `ToolResult`:
```python
return ToolResult(
    success=False,
    output="",
    error=str(e),
    duration=duration
)
```
- Use try/finally for cleanup operations
- Validation errors raise `ValueError` with descriptive messages

**Error propagation:**
- Tools catch exceptions and return `ToolResult` with `success=False`
- Core functions propagate exceptions to caller
- Integration points provide fallbacks for missing dependencies

## Logging

**Framework:** Python's built-in `logging` module

**Patterns:**
- Create module-level loggers: `logger = logging.getLogger(__name__)`
- Used in: `src/agent/manager_memory.py`, `src/agent/task_scheduler.py`
- Console output with `print()` for user-facing messages:
  - Success: `print("✅ Message")`
  - Warning: `print("⚠️  Message")`
  - Info: `print("📝 Message")`
  - Error: `print("❌ Message")`
  - Progress: `print("🔍 Message")`

**When to log:**
- `logger.info()`: Major state changes, task completion
- `logger.error()`: Errors with context for debugging
- `logger.warning()`: Recoverable issues
- `print()`: User-facing status messages in scripts and tools

**Observability:**
- Optional OpenTelemetry integration via `src/observability.py`
- Use `get_observability()` for tracing when enabled

## Comments

**When to Comment:**
- Module-level docstrings: All Python modules start with `"""Module purpose."""`
- Class docstrings: Describe purpose and key features
- Function docstrings: Args, Returns, and brief description
- Inline comments for non-obvious logic
- Security-critical sections marked with comments
- TODO comments use format: `# TODO: Description`

**Docstring style:**
```python
def function_name(arg1: str, arg2: int) -> Dict[str, Any]:
    """
    Brief description.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value
    """
```

**Test docstrings:**
```python
def test_feature_name():
    """Test that specific behavior works correctly."""
```

## Function Design

**Size:**
- Prefer functions under 100 lines
- Large functions accepted for complex state machines (e.g., agent executors)
- Extract complex logic into helper methods (prefixed with `_`)

**Parameters:**
- Use type hints for all parameters: `def add_message(role: str, content: str, metadata: Optional[Dict[str, Any]] = None)`
- Optional parameters default to `None` rather than mutable defaults
- Use `**kwargs` sparingly, primarily in base classes

**Return Values:**
- Use type hints: `-> List[Message]`, `-> Optional[str]`, `-> ToolResult`
- Return structured objects (dataclasses) rather than dicts for complex data
- Tools return `ToolResult` with `success`, `output`, `error`, `duration` fields

## Module Design

**Exports:**
- No explicit `__all__` in most modules
- Use `__init__.py` to expose public API:
```python
# src/policy/__init__.py
from .policy_definitions import (
    PolicyAction,
    PolicyViolation,
    # ...
)
from .policy_engine import PolicyEngine
```

**Barrel Files:**
- Used in subpackages: `src/agent/tools/__init__.py`, `src/policy/__init__.py`
- Import commonly used classes/functions for convenience

**Singletons:**
- Factory functions with internal state: `get_observability()`, `get_auto_indexer()`
- Lazy initialization pattern for expensive resources (reranker model)

## Dataclasses

**Pattern:**
- Use `@dataclass` for data containers
- Use `field(default_factory=dict)` for mutable defaults:
```python
@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

## Abstract Base Classes

**Pattern:**
```python
from abc import ABC, abstractmethod

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def _run(self, *args, **kwargs) -> str:
        pass
```

## Type Checking

**Usage:**
- `TYPE_CHECKING` for circular import prevention:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .vector_store import VectorStoreManager
```
- All function signatures include type hints
- Use `Optional[T]` for nullable values
- Use `Union[A, B]` for alternative types

## Security Patterns

**Code validation:**
- AST-based safety checks before execution (`check_code_safety_ast()`)
- Blocklist dangerous attributes: `__bases__`, `__mro__`, `__reduce__`, `__globals__`, `__builtins__`
- Reject string patterns: `__subclasses__`, `__import__`

**File operations:**
- Resolve paths and check for symlink traversal
- Validate file paths stay within allowed directories

**Configuration:**
- Never commit secrets (`.env` in `.gitignore`)
- Use environment variables for API keys
- Provide `.env.example` with placeholder values

---

*Convention analysis: 2026-02-09*
