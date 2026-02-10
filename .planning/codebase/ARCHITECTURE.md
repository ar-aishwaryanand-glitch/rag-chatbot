# Architecture

**Analysis Date:** 2026-02-09

## Pattern Overview

**Overall:** Layered agentic RAG (Retrieval-Augmented Generation) system with multi-agent orchestration, memory management, and policy governance.

**Key Characteristics:**
- LangGraph-based agent framework with state management
- Pluggable multi-vector-store backend (FAISS local or Pinecone cloud)
- Multi-tier memory system (conversation + episodic + learning)
- Tool registry pattern with base abstraction for extensible tooling
- Policy engine for agent behavior governance and safety constraints
- Optional Redis task queue for distributed coordination
- PostgreSQL session persistence with checkpoint recovery

## Layers

**Presentation Layer:**
- Purpose: Web-based UI for user interaction
- Location: `src/ui/`
- Contains: Streamlit components, enhanced UI components, state management, input validation
- Depends on: Agent layer, RAG layer, configuration
- Used by: End users via Streamlit web interface

**Agent Orchestration Layer:**
- Purpose: Multi-agent coordination with specialized role-based agents
- Location: `src/agent/manager_agent.py`, `src/agent/specialized_agents.py`, `src/agent/task_scheduler.py`
- Contains: ManagerAgent (orchestrator), QAAgentInterface, specialized agent implementations, task scheduling
- Depends on: Tool registry, memory manager, RAG chain, policy engine
- Used by: Streamlit UI, external task schedulers

**Agent Execution Layer:**
- Purpose: Core agent reasoning and tool invocation
- Location: `src/agent/agent_executor_v3.py`
- Contains: AgentExecutorV3 (LangGraph-based state machine), tool execution routing, checkpoint management
- Depends on: Tool registry, memory system, reflection modules, policy engine, observability
- Used by: ManagerAgent, specialized agents

**Memory & Learning Layer:**
- Purpose: Persistent context management and learning from interactions
- Location: `src/agent/memory/`, `src/agent/reflection/`, `src/database/`
- Contains: ConversationMemory (short-term), EpisodicMemory (long-term patterns), ReflectionModule (self-evaluation), LearningModule (pattern extraction)
- Depends on: Database backends (PostgreSQL or file-based), embeddings
- Used by: Agent executor, manager agent

**Tool Ecosystem:**
- Purpose: Pluggable operations for agent task execution
- Location: `src/agent/tools/`
- Contains: Base tool abstraction, RAG tool, document management, web search, calculator, code executor, QA-specialized tools (test case generator, BDD generator, etc.)
- Depends on: Configuration, external APIs, RAG chain, embeddings
- Used by: Agent executor via ToolRegistry

**RAG Pipeline Layer:**
- Purpose: Document retrieval and question-answering with quality improvements
- Location: `src/rag_chain.py`
- Contains: RAGChain (retrieval logic, LLM integration), prompt templates for Q&A and test generation, reranking orchestration
- Depends on: Vector store manager, embedding manager, LLM providers, observability
- Used by: Agent tools, direct UI calls

**Vector Store & Embeddings Layer:**
- Purpose: Document indexing, similarity search, and text encoding
- Location: `src/vector_store.py`, `src/vector_store_pinecone.py`, `src/embeddings.py`, `src/document_manager.py`
- Contains: VectorStoreManager (FAISS), Pinecone integration, EmbeddingManager, DocumentManager (backend-agnostic wrapper)
- Depends on: Configuration, external embedding APIs
- Used by: RAG chain, document loaders, auto-indexing

**Data Access Layer:**
- Purpose: Document loading, indexing, and session persistence
- Location: `src/document_loader.py`, `src/confluence_loader.py`, `src/database/`, `src/auto_indexer.py`
- Contains: Document loaders (PDF, Confluence), PostgreSQL backend, checkpoint manager, auto-indexing scheduler
- Depends on: Vector store, embeddings, configuration
- Used by: System initialization, Streamlit upload handlers

**Infrastructure Layer:**
- Purpose: Cross-cutting concerns and external integrations
- Location: `src/config.py`, `src/policy/`, `src/task_queue/`, `src/observability.py`
- Contains: Configuration management, policy engine (YAML-based rule definitions), Redis task queue, OpenTelemetry observability
- Depends on: External services (LLMs, Redis, PostgreSQL, Pinecone)
- Used by: All layers

## Data Flow

**Chat/Q&A Request Flow:**

1. **Input** → User message via Streamlit UI (`src/ui/streamlit_app_agent.py`)
2. **Validation** → InputValidator checks constraints (`src/ui/input_validation.py`)
3. **Agent Router** → ManagerAgent or AgentExecutorV3 routes to appropriate tool
4. **RAG Pipeline** (if RAG tool selected):
   - Query embedding via EmbeddingManager (`src/embeddings.py`)
   - Vector similarity search via DocumentManager/VectorStore (`src/document_manager.py`)
   - Optional reranking via CrossEncoder (`src/rag_chain.py:get_reranker()`)
   - Relevance filtering against RELEVANCE_THRESHOLD
   - Prompt construction with retrieved context
5. **LLM Generation** → ChatGroq or Google Gemini generates response
6. **Tool Execution** (if needed) → BaseTool subclasses execute (web search, code, etc.)
7. **Reflection** (optional) → ReflectionModule evaluates response quality and confidence
8. **Memory Storage**:
   - ConversationMemory: Short-window context for current session
   - EpisodicMemory: Long-term patterns and learning from successes/failures
   - PostgreSQL: Optional persistent session storage
9. **Output** → Rendered in Streamlit UI with sources and metadata

**Document Ingestion Flow:**

1. **Source** → PDF upload, Confluence API, or web scraping
2. **Loading** → DocumentLoader or ConfluenceLoader reads content
3. **Chunking** → EmbeddingManager splits via RecursiveCharacterTextSplitter
4. **Embedding** → EmbeddingManager generates vectors for chunks
5. **Indexing** → DocumentManager stores in FAISS or Pinecone backend
6. **Auto-Indexing** (optional) → AutoIndexer monitors file system and auto-reindexes
7. **Metadata** → Chunk IDs, source references, timestamps added

**Task Queue Flow (Redis-enabled):**

1. **Task Creation** → AgentExecutor or ManagerAgent enqueues to TaskQueue
2. **Routing** → Task routed by priority (URGENT, HIGH, NORMAL, LOW)
3. **Worker Processing** → Worker.py pulls tasks and executes via tool system
4. **Result Storage** → Results cached with TTL, published via Pub/Sub
5. **Status Tracking** → Consumers (Streamlit) receive updates in real-time

**State Management:**

- **StreamlitSessionState** (`src/ui/state_manager.py`): Page-level UI state (messages, settings, selections)
- **AgentState** (`src/agent/agent_state.py`): LangGraph state for agent reasoning (messages, tool calls, context)
- **CheckpointState** (`src/database/checkpoint_backend.py`): Crash recovery checkpoints
- **SessionMemory** (`src/database/session_manager.py`): Persistent conversation history

## Key Abstractions

**BaseTool (Tool Protocol):**
- Purpose: Standard interface for all agent-executable operations
- Examples: `src/agent/tools/rag_tool.py`, `src/agent/tools/web_search_tool.py`, `src/agent/tools/test_strategy_tool.py`
- Pattern: Abstract class with `_run()` implementation, wrapping with timing/error handling in `run()`, returning ToolResult

**Tool Routing Logic:**
- Purpose: Intelligent dispatch of user requests to appropriate tools
- Examples: `src/agent/manager_agent.py:QAAgentInterface._route_instruction()`, `src/agent/agent_executor_v3.py:_should_use_tool()`
- Pattern: Instruction analysis with keyword/similarity matching to select 1+ tools, instruction enrichment with context

**Memory Abstraction:**
- Purpose: Unified interface for conversation + episodic storage
- Examples: `src/agent/memory/memory_manager.py`, `src/agent/memory/conversation_memory.py`
- Pattern: MemoryManager composes ConversationMemory (vector-searchable context window) and EpisodicMemory (indexed patterns)

**VectorStore Abstraction:**
- Purpose: Backend-agnostic document storage and retrieval
- Examples: `src/vector_store.py` (FAISS), `src/vector_store_pinecone.py` (Pinecone)
- Pattern: DocumentManager delegates to backend based on config (USE_PINECONE flag), consistent API across implementations

**Policy Evaluation:**
- Purpose: Rule-based governance of agent behavior
- Examples: `src/policy/policy_engine.py`, `src/policy/policy_definitions.py`
- Pattern: PolicyEngine evaluates context against YAML policies, returns PolicyAction (allow/deny/flag)

## Entry Points

**Web Interface:**
- Location: `run_agent_ui.py` or `streamlit run src/ui/streamlit_app_agent.py`
- Triggers: User starts web app
- Responsibilities: Initializes Streamlit session, loads agent, handles user input → output loop

**Task Queue Worker:**
- Location: `queue_worker.py`
- Triggers: Distributed task processing
- Responsibilities: Polls Redis queue, executes tasks via agent tools, publishes results

**System Initialization:**
- Location: `src/system_init.py:initialize_system()`
- Triggers: Called by UI or scripts at startup
- Responsibilities: Creates DocumentManager, builds RAGChain, initializes vector store

## Error Handling

**Strategy:** Graceful degradation with fallbacks, try/except with informative logging

**Patterns:**

- **LLM Provider Fallback** (`src/rag_chain.py:_initialize_llm()`): Attempts Groq, falls back to Gemini
- **Embedding Provider Fallback** (`src/config.py:validate()`): Falls back HuggingFace if Google unavailable
- **Vector Store Graceful Degradation** (`src/document_manager.py:_detect_vector_store_type()`): Uses FAISS if Pinecone unavailable
- **PostgreSQL Graceful Degradation** (`src/database/session_manager.py`): Falls back to file-based memory if DB unavailable
- **Tool Execution Error Recovery** (`src/agent/tools/base_tool.py:run()`): ToolResult captures errors with duration/metadata
- **Policy Engine Optional** (`src/agent/agent_executor_v3.py`): Checks POLICY_ENGINE_AVAILABLE, continues without if unavailable
- **Redis Optional** (`src/task_queue/task_queue.py`): Disabled by default, gracefully disabled if unavailable

## Cross-Cutting Concerns

**Logging:**
- Approach: Centralized logging via `src/logging_config.py` + OpenTelemetry structured logging
- All modules use `get_logger(__name__)` from `logging_config.py`
- ObservabilityManager (`src/observability.py`) wraps operations with spans/traces

**Validation:**
- Approach: InputValidator for user input, pydantic models for typed structures
- Location: `src/ui/input_validation.py`, `src/agent/tools/base_tool.py`
- Pattern: Validators run before tool execution, raise informative exceptions

**Authentication:**
- Approach: API key validation at config load (Config.validate()), no session-level auth (Streamlit deployment model)
- Location: `src/config.py`

**Observability:**
- Approach: Optional OpenTelemetry instrumentation with console/OTLP/Jaeger exporters
- Location: `src/observability.py`
- Enabled: ENABLE_OBSERVABILITY config flag, traces for RAG/Agent/LLM operations

---

*Architecture analysis: 2026-02-10*
