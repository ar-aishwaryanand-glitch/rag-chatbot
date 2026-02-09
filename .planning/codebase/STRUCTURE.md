# Codebase Structure

**Analysis Date:** 2026-02-09

## Directory Layout

```
rag-work/
├── src/                          # Core application code
│   ├── agent/                    # Multi-agent orchestration and execution
│   │   ├── tools/               # Tool implementations (RAG, web search, QA)
│   │   ├── memory/              # Conversation and episodic memory
│   │   ├── reflection/          # Self-reflection and learning modules
│   │   ├── agent_executor_v3.py # LangGraph-based agent executor
│   │   ├── manager_agent.py     # Multi-agent orchestrator
│   │   ├── specialized_agents.py # Role-specific agent implementations
│   │   └── task_scheduler.py    # Task scheduling and management
│   ├── ui/                       # Streamlit web interface
│   │   ├── streamlit_app_agent.py # Main entry point (production UI)
│   │   ├── enhanced_components.py # Modern UI components
│   │   ├── styles.py            # CSS and styling
│   │   └── input_validation.py  # User input validation
│   ├── database/                 # Data persistence layer
│   │   ├── postgres_backend.py  # PostgreSQL client
│   │   ├── session_manager.py   # Session and conversation storage
│   │   └── checkpoint_backend.py # Crash recovery checkpoints
│   ├── policy/                   # Policy engine for governance
│   │   ├── policy_engine.py     # Rule evaluation engine
│   │   ├── policy_definitions.py # Policy types and contexts
│   │   └── default_policies.yaml # Default policy rules
│   ├── task_queue/              # Redis-based task queue
│   │   ├── task_queue.py        # Queue manager
│   │   ├── task_models.py       # Task and status models
│   │   ├── worker.py            # Queue worker executor
│   │   └── scheduler.py         # Task scheduling
│   ├── rag_chain.py             # Core RAG pipeline
│   ├── document_manager.py      # Backend-agnostic document management
│   ├── embeddings.py            # Text chunking and embedding generation
│   ├── vector_store.py          # FAISS vector store
│   ├── vector_store_pinecone.py # Pinecone cloud vector store
│   ├── document_loader.py       # PDF and text document loading
│   ├── confluence_loader.py     # Confluence API integration
│   ├── auto_indexer.py          # Automatic document indexing
│   ├── config.py                # Configuration management
│   ├── observability.py         # OpenTelemetry instrumentation
│   └── system_init.py           # System initialization
├── tests/                        # Test suite
│   ├── unit/                    # Unit tests
│   │   ├── test_rag_chain_unit.py
│   │   ├── test_embeddings.py
│   │   ├── test_config.py
│   │   ├── test_memory.py
│   │   ├── test_tools.py
│   │   └── test_vector_store.py
│   ├── integration/             # Integration tests
│   │   ├── test_agent_system.py
│   │   ├── test_manager_agent.py
│   │   ├── test_manager_features.py
│   │   ├── test_qa_tools.py
│   │   ├── test_rag_chain.py
│   │   ├── test_auto_index.py
│   │   └── test_streamlit_integration.py
│   ├── conftest.py              # Pytest fixtures and configuration
│   └── __init__.py
├── data/                         # Data storage (runtime-created)
│   ├── vector_store/            # FAISS index files
│   ├── memory_store/            # Conversation memory (JSON/pickle)
│   ├── episodic_memory/         # Episodic memory patterns
│   ├── workspace/               # File operations sandbox
│   ├── documents/               # Loaded documents cache
│   ├── uploaded/                # User-uploaded documents
│   ├── learning/                # Learning module data
│   └── reflections/             # Reflection logs (JSONL)
├── docs/                         # Documentation
│   ├── CONFIGURATION.md
│   ├── AUTO_INDEXING_GUIDE.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── EXTERNAL_SERVICES_SETUP.md
│   ├── OBSERVABILITY_GUIDE.md
│   ├── POSTGRES_SETUP.md
│   ├── PINECONE_MIGRATION_GUIDE.md
│   ├── QA_FEATURES_REFERENCE.md
│   └── [other guides]
├── scripts/                      # Utility scripts
├── .planning/                    # GSD planning documents
│   └── codebase/                # Codebase analysis (ARCHITECTURE.md, STRUCTURE.md, etc.)
├── .env.example                  # Environment variables template
├── .env                          # Environment variables (secrets, API keys)
├── config.py                     # Legacy: See src/config.py
├── run_agent_ui.py              # UI launcher (calls src/ui/streamlit_app_agent.py)
├── queue_worker.py              # Redis task queue worker
├── requirements.txt             # Python dependencies
├── pytest.ini                   # Pytest configuration
├── ruff.toml                    # Ruff linter configuration
├── Dockerfile                   # Docker container definition
├── docker-compose.yml           # (if present) Local dev environment
├── Makefile                     # Build/dev commands
└── README.md                    # Project overview
```

## Directory Purposes

**`src/agent/`:**
- Purpose: Multi-agent system with LangGraph-based reasoning
- Contains: Agent executors, tool registry, specialized agents, memory, reflection
- Key files: `agent_executor_v3.py` (core reasoning), `manager_agent.py` (orchestration)

**`src/agent/tools/`:**
- Purpose: Pluggable tools for agent execution
- Contains: ~18 tool implementations including RAG, web search, QA-specialized tools
- Key files: `base_tool.py` (abstraction), `rag_tool.py`, `web_search_tool.py`

**`src/agent/memory/`:**
- Purpose: Short and long-term memory management
- Contains: ConversationMemory, EpisodicMemory, MemoryManager
- Key files: `memory_manager.py` (coordination)

**`src/agent/reflection/`:**
- Purpose: Self-evaluation and learning from interactions
- Contains: ReflectionModule (confidence/quality assessment), LearningModule (pattern extraction)
- Key files: `reflection_module.py`

**`src/ui/`:**
- Purpose: Streamlit web interface
- Contains: Main app, enhanced components, styles, state management
- Key files: `streamlit_app_agent.py` (entry point, ~2500 lines)

**`src/database/`:**
- Purpose: Persistent storage and session management
- Contains: PostgreSQL backend, session manager, checkpoint system
- Key files: `postgres_backend.py`, `session_manager.py`

**`src/policy/`:**
- Purpose: Rule-based governance and safety
- Contains: Policy engine, policy definitions, YAML-based rules
- Key files: `policy_engine.py`

**`src/task_queue/`:**
- Purpose: Distributed task processing via Redis
- Contains: Task queue, models, worker, scheduler
- Key files: `task_queue.py`, `worker.py`

**`data/`:**
- Purpose: Runtime data storage (not code)
- Generated by: Vector indexing, memory storage, logging
- Committed: Only templates; actual data in .gitignore

**`tests/`:**
- Purpose: Unit and integration test suite
- Contains: Tests for RAG, embeddings, memory, agent, tools, integrations
- Pattern: Test files co-located with imports (e.g., test_rag_chain.py tests src/rag_chain.py)

## Key File Locations

**Entry Points:**
- `run_agent_ui.py`: Streamlit app launcher (calls `src/ui/streamlit_app_agent.py:main()`)
- `queue_worker.py`: Redis task queue worker (calls worker loop)
- `src/system_init.py:initialize_system()`: Core system initialization

**Configuration:**
- `src/config.py`: Environment-based configuration with validation
- `.env`: Runtime secrets and API keys (not committed)
- `.env.example`: Template with all configurable variables

**Core Logic:**
- `src/rag_chain.py`: RAG pipeline (retrieval + LLM generation)
- `src/agent/agent_executor_v3.py`: LangGraph agent reasoning loop
- `src/agent/manager_agent.py`: Multi-agent orchestration
- `src/document_manager.py`: Unified document store interface

**Vector Operations:**
- `src/embeddings.py`: Text chunking and embedding generation
- `src/vector_store.py`: FAISS vector store (default)
- `src/vector_store_pinecone.py`: Pinecone cloud vector store

**Testing:**
- `tests/conftest.py`: Shared fixtures (mock LLM, sample docs, etc.)
- `tests/unit/`: Isolated component tests
- `tests/integration/`: End-to-end system tests

## Naming Conventions

**Files:**
- Module files: `snake_case.py` (e.g., `agent_executor_v3.py`, `session_manager.py`)
- Test files: `test_<module>.py` (e.g., `test_rag_chain.py`)
- Config files: `config.py`, `.env`, `*.toml`, `*.yaml`, `*.sql`
- Data files: `<type>.<extension>` (e.g., `learning_data.pkl`, `reflections.jsonl`)

**Directories:**
- Module packages: `snake_case` (e.g., `agent`, `ui`, `database`)
- Sub-packages: Feature-based (e.g., `tools`, `memory`, `reflection`)
- Data dirs: Descriptor-based (e.g., `vector_store`, `memory_store`, `episodic_memory`)

**Python Classes:**
- Standard classes: `PascalCase` (e.g., `AgentExecutorV3`, `MemoryManager`, `RAGChain`)
- Abstract base classes: `Base<Name>` (e.g., `BaseTool`)
- Models (Pydantic): `<Name>` (e.g., `Task`, `Session`, `ToolResult`)

**Functions/Methods:**
- Standard functions: `snake_case()` (e.g., `initialize_system()`, `chunk_documents()`)
- Private methods: `_snake_case()` (e.g., `_initialize_llm()`, `_route_instruction()`)
- Properties: `snake_case` (e.g., `@property def name()`)

**Constants:**
- Config vars: `UPPERCASE` (e.g., `GROQ_API_KEY`, `TOP_K_RESULTS`)
- Enum values: `UPPERCASE` (e.g., `TaskStatus.PENDING`, `TaskPriority.HIGH`)

## Where to Add New Code

**New Feature (e.g., document clustering):**
- Primary code: `src/agent/tools/clustering_tool.py` (if agent-callable) or `src/clustering.py` (if core service)
- Tests: `tests/unit/test_clustering.py` and `tests/integration/test_clustering_integration.py`
- Documentation: `docs/CLUSTERING_GUIDE.md`

**New Agent Tool:**
- Implementation: `src/agent/tools/<tool_name>_tool.py`
- Inherit from: `BaseTool` (`src/agent/tools/base_tool.py`)
- Register with: `ToolRegistry` in `src/agent/tool_registry.py`
- Example pattern: See `src/agent/tools/rag_tool.py` or `src/agent/tools/web_search_tool.py`

**New Memory Type:**
- Implementation: `src/agent/memory/<memory_type>_memory.py`
- Register with: `MemoryManager` in `src/agent/memory/memory_manager.py`
- Example: See `src/agent/memory/conversation_memory.py`

**New UI Component:**
- Implementation: `src/ui/enhanced_components.py` (add function)
- Call from: `src/ui/streamlit_app_agent.py` main render loop
- Example pattern: `render_enhanced_chat_message()`, `render_stats_dashboard()`

**New Database Backend:**
- Implementation: `src/database/<backend>_backend.py`
- Inherit from: Interface defined in `src/database/session_manager.py`
- Example: See `src/database/postgres_backend.py`

**Utilities/Helpers:**
- Shared helpers: `src/<util_name>.py` (e.g., `src/observability.py`)
- Tool-specific utils: `src/agent/tools/<util_name>.py`

## Special Directories

**`data/vector_store/`:**
- Purpose: FAISS vector store files
- Generated: By `DocumentManager.add_documents()`
- Committed: No; .gitignore excludes
- Structure: FAISS index files + metadata

**`data/memory_store/`:**
- Purpose: Conversation memory (short-term context)
- Generated: By `ConversationMemory.save()`
- Committed: No; runtime-only
- Format: JSON or pickle files per session

**`data/episodic_memory/`:**
- Purpose: Episodic memory (patterns from interactions)
- Generated: By `EpisodicMemory.add_episode()`
- Committed: No; runtime-only
- Format: JSONL with indexed patterns

**`data/learning/`:**
- Purpose: Learning module data
- Generated: By `LearningModule.extract_patterns()`
- Committed: No; runtime-only
- Format: Pickle files with learned models

**`data/reflections/`:**
- Purpose: Reflection logs (decisions, quality assessments)
- Generated: By `ReflectionModule` after each action
- Committed: No; runtime-only
- Format: JSONL with timestamped reflections

**`.planning/codebase/`:**
- Purpose: GSD codebase analysis documents
- Generated: By gsd-map-codebase command
- Committed: Yes (markdown)
- Files: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, CONCERNS.md, STACK.md, INTEGRATIONS.md

## Import Patterns

**Layer imports (correct direction - no circular deps):**

```python
# UI layer can import:
from src.agent.agent_executor_v3 import AgentExecutorV3
from src.rag_chain import RAGChain
from src.config import Config
# But NOT data layer

# Agent layer can import:
from src.rag_chain import RAGChain
from src.agent.memory import MemoryManager
from src.config import Config
# But NOT UI layer

# RAG layer can import:
from src.embeddings import EmbeddingManager
from src.document_manager import DocumentManager
from src.config import Config
# But NOT agent or UI layers

# All layers can import:
from src.config import Config
from src.observability import get_observability
```

**Tool registration pattern:**
```python
# In src/agent/tools/__init__.py
from .base_tool import BaseTool, ToolResult
from .rag_tool import RAGTool
from .web_search_tool import WebSearchTool
# ... other tools

__all__ = ['BaseTool', 'ToolResult', 'RAGTool', 'WebSearchTool', ...]
```

---

*Structure analysis: 2026-02-09*
