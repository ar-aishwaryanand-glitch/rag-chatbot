# RAG Agent Codebase Guide

**Last Updated:** 2026-02-09
**Status:** Production-ready with Phase 4 features + bugfixes

---

## Table of Contents

1. [Overview](#overview)
2. [Quickstart](#quickstart)
3. [Architecture](#architecture)
4. [Project Structure](#project-structure)
5. [Core Components Deep Dive](#core-components-deep-dive)
   - [RAG Chain](#1-rag-chain)
   - [Agent Executor (LangGraph)](#2-agent-executor-langgraph-state-machine)
   - [Agent State](#3-agent-state)
   - [Tool Registry & Tools](#4-tool-registry--tools)
   - [Memory System](#5-memory-system-3-tier)
   - [Reflection & Learning](#6-reflection--learning-system)
   - [Manager Agent & Specialized Agents](#7-manager-agent--multi-agent-orchestration)
   - [QA Pipeline](#8-qa-pipeline)
   - [Policy Engine](#9-policy-engine)
   - [Database & Checkpoints](#10-database--checkpoint-persistence)
   - [Observability](#11-observability--monitoring)
   - [Task Queue](#12-redis-task-queue)
   - [Streamlit UI](#13-streamlit-ui)
6. [Key Flows (End-to-End)](#key-flows-end-to-end)
7. [Configuration Reference](#configuration-reference)
8. [API Reference](#api-reference)
9. [Scripts & Utilities](#scripts--utilities)
10. [Testing](#testing)
11. [Design Patterns](#design-patterns)
12. [Security](#security)
13. [Deployment](#deployment)
14. [Troubleshooting](#troubleshooting)
15. [Glossary](#glossary)

---

## Overview

### What It Does

A production-ready Retrieval-Augmented Generation (RAG) system with autonomous agent capabilities, multi-tier conversation memory, self-reflection, and QA automation tools. Users ask questions, the system retrieves relevant documents, and generates accurate answers grounded in your data — with the ability to search the web, run calculations, generate test cases, and remember past conversations.

### Key Features

| Feature | Description |
|---------|-------------|
| **RAG Pipeline** | Document upload → chunking → embedding → vector search → reranking → LLM answer |
| **Agent System** | 15+ specialized tools with intelligent LLM-based routing |
| **3-Tier Memory** | Session memory + episodic memory (JSON) + checkpoint recovery (PostgreSQL) |
| **Self-Reflection** | Agent evaluates its own decisions and learns from patterns |
| **Web Browsing** | Autonomous Playwright-based web agent with content extraction |
| **QA Automation** | Test case generation, BDD/Gherkin, bug reports, traceability matrix |
| **Multi-Agent** | Manager agent orchestrating specialized QA/Dev/Doc agents |
| **Production Ready** | Policy engine, Redis queue, OpenTelemetry, PostgreSQL, Pinecone |

### Performance

| Metric | Value |
|--------|-------|
| Page Load | Instant (lazy agent initialization) |
| Query Response | 3–5s average |
| Memory-Based Answers | ~1s (no tool overhead) |
| First-Time Startup | 3–5s (model download on first run: ~90MB) |

### Who Uses It

| User Type | Access Method |
|-----------|---------------|
| End Users | Streamlit web UI (chat interface) |
| Developers | Python API — `RAGChain.ask()` or `AgentExecutorV3.execute()` |
| Workers | Redis task queue for async processing |

---

## Quickstart

### Prerequisites

- Python 3.11+ (3.9+ minimum)
- 4GB RAM minimum
- Groq API key (free at https://console.groq.com)

### Setup

```bash
# Option A: Automated setup (recommended)
chmod +x setup.sh && ./setup.sh   # Mac/Linux
setup.bat                          # Windows

# Option B: Manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Minimal .env

```bash
GROQ_API_KEY=your_key_here
LLM_PROVIDER=groq
GROQ_MODEL=llama-3.3-70b-versatile
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Run

```bash
# Mac: double-click run.command in Finder
# Windows: double-click run.bat

# Or via Makefile
make run

# Or directly
streamlit run src/ui/streamlit_app_agent.py
# Open http://localhost:8501
```

### Quick Test (Python API)

```python
from src.system_init import initialize_system

rag = initialize_system()
result = rag.ask("What is retrieval-augmented generation?")
print(result['answer'])
```

---

## Architecture

### High-Level Component Diagram

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   User      │────▶│   Streamlit UI   │────▶│  State Manager  │
│             │     │ (Chat Interface)  │     │ (Session State) │
└─────────────┘     └──────────────────┘     └────────┬────────┘
                                                       │
                    ┌──────────────────────────────────┼──────────────────────────┐
                    │                                  │                          │
                    ▼                                  ▼                          ▼
           ┌────────────────┐              ┌───────────────────┐       ┌──────────────────┐
           │   RAG Chain    │              │  Agent Executor   │       │  Policy Engine   │
           │ (retrieve+gen) │              │  (LangGraph FSM)  │       │ (rules & limits) │
           └───────┬────────┘              └────────┬──────────┘       └──────────────────┘
                   │                                │
                   ▼                                ▼
           ┌────────────────┐              ┌───────────────────┐
           │  Vector Store  │              │  Tool Registry    │
           │ (FAISS/Pinecone│              │  (15+ tools)      │
           └────────────────┘              └────────┬──────────┘
                                                    │
                                    ┌───────────────┼───────────────┐
                                    ▼               ▼               ▼
                             ┌────────────┐  ┌────────────┐  ┌────────────┐
                             │  Memory    │  │ Reflection │  │ Checkpoint │
                             │  Manager   │  │ + Learning │  │ (Postgres) │
                             └────────────┘  └────────────┘  └────────────┘
```

### Data Flow Summary

| Flow | Path |
|------|------|
| **RAG Query** | Question → Embed → Vector Search → Rerank → LLM Generate → Answer + Sources |
| **Agent Query** | Query → Memory Context → LLM Route → Tool Execute → LLM Synthesize → Reflect |
| **Memory Answer** | Query → Memory Context → LLM answers directly (no tool) |

---

## Project Structure

```
rag-work/
├── src/
│   ├── __init__.py
│   ├── config.py                      # Central configuration (150+ settings)
│   ├── system_init.py                 # System bootstrap & initialization
│   ├── rag_chain.py                   # Core RAG pipeline (retrieve + generate)
│   ├── embeddings.py                  # Text chunking & embedding generation
│   ├── vector_store.py                # FAISS vector store backend
│   ├── vector_store_pinecone.py       # Pinecone cloud vector store backend
│   ├── document_manager.py            # Unified document interface (FAISS/Pinecone)
│   ├── document_loader.py             # PDF, DOCX, TXT, MD file parsing
│   ├── auto_indexer.py                # Automatic document indexing
│   ├── confluence_loader.py           # Confluence wiki integration
│   ├── observability.py               # OpenTelemetry tracing & metrics
│   │
│   ├── agent/                         # ========== AGENT SYSTEM ==========
│   │   ├── __init__.py                # Module exports
│   │   ├── agent_executor_v3.py       # LangGraph state machine (1113 lines)
│   │   ├── agent_state.py             # AgentState TypedDict definition
│   │   ├── types.py                   # Shared types: AgentType, TaskAssignment, etc.
│   │   ├── tool_registry.py           # Tool registration & lookup
│   │   ├── manager_agent.py           # Multi-agent orchestrator
│   │   ├── manager_memory.py          # Manager state tracking
│   │   ├── specialized_agents.py      # DevAgent, DocAgent, SecurityAgent
│   │   ├── task_scheduler.py          # Task scheduling for agents
│   │   ├── qa_pipeline.py             # Automated QA workflow
│   │   │
│   │   ├── tools/                     # ---- Agent Tools (15+) ----
│   │   │   ├── __init__.py
│   │   │   ├── base_tool.py           # BaseTool abstract class
│   │   │   ├── rag_tool.py            # document_search — query indexed docs
│   │   │   ├── web_search_tool.py     # web_search — DuckDuckGo search
│   │   │   ├── web_agent_tool.py      # web_agent — Playwright page extraction
│   │   │   ├── news_api_tool.py       # news_search — NewsAPI integration
│   │   │   ├── relevance_evaluator.py # Relevance scoring for search results
│   │   │   ├── calculator_tool.py     # calculator — math expressions
│   │   │   ├── code_executor_tool.py  # python_executor — sandboxed Python
│   │   │   ├── file_ops_tool.py       # file_operations — read/write files
│   │   │   ├── doc_management_tool.py # document_manager — manage uploads
│   │   │   ├── qa_analysis_tool.py    # QA analysis & coverage
│   │   │   ├── bug_report_tool.py     # Bug report generation
│   │   │   ├── test_strategy_tool.py  # Test strategy creation
│   │   │   ├── requirements_extractor_tool.py  # Requirement extraction
│   │   │   ├── traceability_matrix_tool.py     # Req→Test traceability
│   │   │   ├── bdd_generator_tool.py  # BDD/Gherkin scenario generation
│   │   │   └── test_data_generator_tool.py     # Test data generation
│   │   │
│   │   ├── memory/                    # ---- Memory System ----
│   │   │   ├── __init__.py
│   │   │   ├── conversation_memory.py # Tier 1: Session short-term memory
│   │   │   ├── episodic_memory.py     # Tier 2: Cross-session long-term memory
│   │   │   └── memory_manager.py      # Unified coordinator for both tiers
│   │   │
│   │   └── reflection/                # ---- Self-Reflection ----
│   │       ├── __init__.py
│   │       ├── reflection_module.py   # Agent self-evaluation
│   │       └── learning_module.py     # Pattern extraction & optimization
│   │
│   ├── database/                      # ========== PERSISTENCE ==========
│   │   ├── __init__.py
│   │   ├── models.py                  # Session, Message, Memory dataclasses
│   │   ├── checkpoint_backend.py      # Tier 3: LangGraph checkpoint (PostgreSQL)
│   │   ├── postgres_backend.py        # PostgreSQL CRUD operations
│   │   └── session_manager.py         # Session lifecycle management
│   │
│   ├── policy/                        # ========== POLICY ENGINE ==========
│   │   ├── __init__.py
│   │   ├── policy_engine.py           # Rule evaluation & enforcement
│   │   ├── policy_definitions.py      # Policy types (tool, rate, content, cost)
│   │   └── policy_store.py            # Policy persistence
│   │
│   ├── task_queue/                    # ========== REDIS QUEUE ==========
│   │   ├── __init__.py
│   │   ├── task_queue.py              # Queue management & submission
│   │   ├── task_models.py             # Task dataclasses
│   │   ├── scheduler.py              # Task scheduling
│   │   └── worker.py                  # Worker pool
│   │
│   └── ui/                            # ========== STREAMLIT UI ==========
│       ├── __init__.py
│       ├── streamlit_app_agent.py     # Main application (2433 lines)
│       ├── state_manager.py           # Session state initialization
│       ├── components.py              # Basic UI components
│       ├── enhanced_components.py     # Advanced components (cards, dashboards)
│       ├── styles.py                  # CSS styling
│       ├── input_validation.py        # Input sanitization & validation
│       ├── document_handler.py        # Document upload handling
│       ├── url_handler.py             # URL processing
│       └── auto_index_integration.py  # Auto-indexing UI
│
├── scripts/
│   ├── setup/
│   │   ├── init_database.py           # PostgreSQL table creation
│   │   └── migrate_to_pinecone.py     # FAISS → Pinecone migration
│   ├── maintenance/
│   │   └── reindex_documents.py       # Rebuild vector store
│   └── monitoring/
│       └── check_backend_status.py    # Health check all services
│
├── tests/
│   ├── conftest.py                    # Pytest fixtures
│   ├── unit/                          # Unit tests
│   │   ├── test_config.py
│   │   ├── test_embeddings.py
│   │   ├── test_rag_chain_unit.py
│   │   ├── test_memory.py
│   │   ├── test_tools.py
│   │   └── test_vector_store.py
│   └── integration/                   # Integration tests
│       ├── test_agent_system.py
│       ├── test_manager_agent.py
│       ├── test_manager_features.py
│       ├── test_qa_tools.py
│       ├── test_qa_generation.py
│       ├── test_rag_chain.py
│       ├── test_auto_index.py
│       ├── test_conversation_memory_fix.py
│       ├── test_critical_fixes.py
│       ├── test_relevance_filter.py
│       └── test_streamlit_integration.py
│
├── docs/                              # Extended documentation
│   ├── CONFIGURATION.md
│   ├── AUTO_INDEXING_GUIDE.md
│   ├── CHECKPOINT_GUIDE.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── EXTERNAL_SERVICES_SETUP.md
│   ├── OBSERVABILITY_GUIDE.md
│   ├── PINECONE_MIGRATION_GUIDE.md
│   ├── POLICY_ENGINE_GUIDE.md
│   ├── POSTGRES_SETUP.md
│   ├── QA_FEATURES_REFERENCE.md
│   ├── QA_TOOLS_GUIDE.md
│   ├── REDIS_QUEUE_GUIDE.md
│   ├── RELEVANCE_FILTERING.md
│   ├── STREAMLIT_DEPLOYMENT.md
│   └── WEB_SCRAPING_ENHANCEMENTS.md
│
├── data/                              # Runtime data (gitignored)
│   ├── documents/                     # Source docs (PDF, DOCX, TXT, MD)
│   ├── vector_store/                  # FAISS index files
│   ├── episodic_memory/               # Session JSON files (long-term memory)
│   ├── learning/                      # learning_data.pkl (tool stats)
│   ├── reflections/                   # reflections.jsonl (agent evaluations)
│   ├── workspace/                     # File operations sandbox
│   └── .index_metadata.json           # Auto-indexing metadata
│
├── .env / .env.example                # Environment configuration
├── requirements.txt                   # Python dependencies
├── Makefile                           # Dev commands (run, test, clean, etc.)
├── run.command                        # macOS launcher (double-click)
├── run.bat                            # Windows launcher (double-click)
├── setup.sh / setup.bat               # First-time setup scripts
├── run_agent_ui.py                    # Alternative UI launcher
└── README.md
```

### Makefile Commands

```bash
make run          # Start the Streamlit app
make test         # Run all tests
make test-quick   # Run quick unit tests only
make setup        # Initialize database
make reindex      # Reindex all documents
make check        # Check backend service status
make clean        # Clean cache files
make lint         # Check code style
```

---

## Core Components Deep Dive

### 1. RAG Chain

**File:** `src/rag_chain.py` (~762 lines)
**Class:** `RAGChain`

The core retrieval-augmented generation pipeline. Retrieves relevant document chunks via vector similarity search, optionally reranks them, and passes them to an LLM to generate grounded answers.

**Initialization:**
- Creates LLM instance (Groq or Google Gemini based on `LLM_PROVIDER`)
- Sets up prompt templates for QA, test case generation, and pytest code generation
- Lazy-loads cross-encoder reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`)

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `ask(question, top_k=5)` | Main query — retrieve + rerank + generate answer |
| `retrieve_context(query, k)` | Vector similarity search in FAISS/Pinecone |
| `format_context(docs)` | Format retrieved documents for LLM prompt |
| `generate_test_cases(requirements, k)` | Generate test cases from requirements |
| `generate_pytest_code(requirements, k)` | Generate pytest code from requirements |

**Pipeline:**
```
Query → Embed → Vector Search (top_k) → Rerank (cross-encoder) → Format Context → LLM → Answer + Sources
```

**Returns:** `{ question, answer, context, sources, documents }`

---

### 2. Agent Executor (LangGraph State Machine)

**File:** `src/agent/agent_executor_v3.py` (~1113 lines)
**Class:** `AgentExecutorV3`

The brain of the system. Uses LangGraph's `StateGraph` to orchestrate a multi-step workflow: understand the query, pick the right tool, execute it, synthesize an answer, and reflect on the decision.

**Constructor Parameters:**

```python
AgentExecutorV3(
    llm,                          # LLM instance (Groq/Gemini)
    tool_registry: ToolRegistry,  # All available tools
    config,                       # Config object
    enable_memory=True,           # Tier 1+2 memory
    enable_reflection=True,       # Self-reflection after each query
    enable_checkpoints=True,      # Tier 3 PostgreSQL checkpoints
    enable_policy_engine=True     # Policy enforcement
)
```

**LangGraph Nodes & Edges:**

```
┌──────────────┐
│  understand   │  ← Add query to memory, load context
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    route      │  ← LLM selects tool (or "none" for memory answer)
└──────┬───────┘
       │
       ├── tool == None ──▶ ┌────────┐
       │                    │ finish  │ ──▶ synthesize
       │                    └────────┘
       │
       ├── tool selected ──▶ ┌─────────┐
       │                     │ execute  │ ← Run tool, policy check
       │                     └────┬────┘
       │                          │
       │                          ▼
       │                    ┌─────────────┐
       │                    │ synthesize   │ ← LLM generates final answer
       │                    └──────┬──────┘
       │                           │
       │                           ▼
       │                    ┌─────────────┐
       │                    │  reflect     │ ← Evaluate decision, record learning
       │                    └──────┬──────┘
       │                           │
       └───────────────────────────▼
                                  END
```

**Core Node Methods:**

| Node | Method | What It Does |
|------|--------|--------------|
| understand | `_understand_query()` | Adds user message to memory, loads conversation + episodic context |
| route | `_route_to_tool()` | LLM picks the best tool from available list (or "none") |
| — | `_should_continue()` | Conditional edge: go to execute or finish |
| execute | `_execute_tool()` | Runs selected tool with policy checks, records timing |
| synthesize | `_synthesize_answer()` | LLM synthesizes clean response from tool result + memory |
| reflect | `_reflect_on_interaction()` | Self-evaluation, pattern recording, learning updates |

**Answer Synthesis (in synthesize node):**

For `web_search`, `web_agent`, and `news_api` results, the raw tool output is passed through an LLM synthesis step that converts raw snippets into 3 concise, readable paragraphs. Other tools (calculator, document_search, etc.) return their results directly.

**Tool Selection Logic (in route node):**

| Query Type | Tool Selected | Reason |
|------------|---------------|--------|
| "What does our architecture doc say about X?" | `document_search` | Knowledge base query |
| "Latest AI news" | `web_agent` | Real-time web info with full page extraction |
| "Summarize this URL: https://..." | `web_agent` | Full page extraction |
| "Calculate 15% of $2500" | `calculator` | Math operation |
| "Generate BDD scenarios for login" | `bdd_generator` | QA tool |
| "What did we discuss earlier?" | `none` | Memory-based answer (no tool) |

---

### 3. Agent State

**File:** `src/agent/agent_state.py`
**Type:** `TypedDict` (AgentState)

All data flows through this state object as it passes between LangGraph nodes.

```python
AgentState = {
    "messages": Sequence[BaseMessage],        # LangChain message history
    "query": str,                             # Current user query
    "final_answer": str,                      # Generated response
    "current_phase": str,                     # Current execution phase
    "iteration": int,                         # Current iteration number
    "max_iterations": int,                    # Safety limit (default 10)
    "selected_tool": Optional[str],           # Tool chosen by router
    "tools_used": List[str],                  # All tools used this query
    "tool_results": List[Dict[str, Any]],     # Outputs from tools
    "needs_retry": bool,                      # Should retry flag
    "last_error": Optional[str],              # Last error message
    "memory_context": Optional[str],          # Injected memory context
    "conversation_messages": Optional[List],  # Serializable messages (for checkpoints)
    "answer_from_memory": bool,               # True if answered without tools
    "start_time": Optional[float],            # Query start timestamp
    "execution_metadata": Dict[str, Any]      # Extra metadata
}
```

---

### 4. Tool Registry & Tools

**Registry File:** `src/agent/tool_registry.py`
**Class:** `ToolRegistry`

Central registry managing all tools. Tools register themselves; the agent queries the registry for available tools and descriptions.

**Key Methods:**
- `register(tool)` — Add a tool instance
- `get_tool(name)` — Retrieve by name
- `get_all_tools()` — List all tools
- `get_tool_descriptions()` — Formatted list for LLM prompts
- `get_tool_names()` — List of names

**Base Class:** `BaseTool` (`src/agent/tools/base_tool.py`)
- Abstract properties: `name`, `description`
- Abstract method: `_run(*args, **kwargs) -> str`
- Concrete wrapper: `run()` — adds timing, error handling, returns `ToolResult`

**Complete Tool List:**

| # | Tool Name | File | Purpose | Enabled By Default |
|---|-----------|------|---------|-------------------|
| 1 | `document_search` | `rag_tool.py` | Search indexed documents via RAG | Yes |
| 2 | `web_search` | `web_search_tool.py` | DuckDuckGo web search with dedup | Yes |
| 3 | `web_agent` | `web_agent_tool.py` | Playwright full-page extraction | Yes |
| 4 | `news_search` | `news_api_tool.py` | NewsAPI current events | Yes (needs key) |
| 5 | `calculator` | `calculator_tool.py` | Math expressions (safe eval) | Yes |
| 6 | `python_executor` | `code_executor_tool.py` | Sandboxed Python execution | **No** (safety) |
| 7 | `file_operations` | `file_ops_tool.py` | Read/write in workspace dir | Yes |
| 8 | `document_manager` | `doc_management_tool.py` | Manage uploaded documents | Yes |
| 9 | `qa_analysis` | `qa_analysis_tool.py` | QA coverage & risk analysis | Yes |
| 10 | `bug_report` | `bug_report_tool.py` | Generate structured bug reports | Yes |
| 11 | `test_strategy` | `test_strategy_tool.py` | Create test strategies | Yes |
| 12 | `requirements_extractor` | `requirements_extractor_tool.py` | Extract requirements from docs | Yes |
| 13 | `traceability_matrix` | `traceability_matrix_tool.py` | Req → Test mapping | Yes |
| 14 | `bdd_generator` | `bdd_generator_tool.py` | Gherkin/BDD scenario generation | Yes |
| 15 | `test_data_generator` | `test_data_generator_tool.py` | Test data & edge cases | Yes |
| — | `relevance_evaluator` | `relevance_evaluator.py` | Internal: scores search relevance | Internal |

---

### 5. Memory System (3-Tier)

#### Tier 1: Conversation Memory (session-scoped)

**File:** `src/agent/memory/conversation_memory.py`
**Class:** `ConversationMemory`

Stores the current session's messages in-memory. Automatically summarizes older messages when the count exceeds a threshold.

```python
ConversationMemory(
    session_id="uuid",           # Auto-generated if not provided
    max_messages=10,             # Keep last 10 messages in full
    summarize_threshold=20       # Summarize when >20 messages total
)
```

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `add_message(role, content, metadata)` | Store a message (user/assistant/system) |
| `get_recent_messages(n)` | Get last N messages |
| `get_context_string()` | Format as "[Previous summary]\n[Recent conversation]" |
| `get_last_user_message()` | Most recent user input |
| `_auto_summarize()` | Triggered when messages > threshold; prunes old messages |
| `to_dict()` / `from_dict()` | Serialize/deserialize (for checkpoint persistence) |
| `clear()` | Reset all messages |
| `get_stats()` | Session statistics |

**Auto-Summarization Flow:**
```
Messages exceed threshold (20)
  → Extract user queries from old messages
  → Extract tools used from metadata
  → Generate text summary: "User asked about: X, Y, Z. Used tools: A, B"
  → Keep only last max_messages (10)
  → Store summary for future context
```

**Data Stored per Message:**
```python
Message(
    role="user",                        # user | assistant | system
    content="What is RAG?",
    timestamp=datetime.now(),
    metadata={"tools_used": ["document_search"]}
)
```

#### Tier 2: Episodic Memory (cross-session, persisted to disk)

**File:** `src/agent/memory/episodic_memory.py`
**Class:** `EpisodicMemory`

Persists summaries of past conversations as JSON files. Survives app restarts. Enables the agent to recall what a user asked days or weeks ago.

**Storage:** `data/episodic_memory/{session_id}.json`

**Episode Data Structure:**
```python
Episode(
    session_id="480de419-...",
    timestamp=datetime(2026, 2, 5),
    summary="User asked about: latest AI news. Tools used: web_agent",
    user_queries=["tell me latest ai news", "latest ai news"],
    tools_used=["web_agent"],
    outcomes=["success"],
    key_entities=["AI", "news"],
    user_preferences={"prefers_detailed_answers": True}
)
```

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `add_episode(episode)` | Store and persist to JSON |
| `create_episode_from_conversation(...)` | Build episode from session data |
| `search_episodes(query, max_results=5)` | Keyword search with relevance scoring |
| `get_recent_episodes(n=5)` | Get N most recent sessions |
| `get_episodes_by_tool(tool_name)` | Find sessions that used a specific tool |
| `get_aggregated_preferences()` | Aggregate user preferences across all sessions |
| `get_tool_usage_stats()` | Tool usage frequency across all sessions |
| `clear_old_episodes(days=30)` | Cleanup old data |

**Search Scoring:**
- Match in summary → 3 points
- Match in user queries → 2 points
- Match in key entities → 1 point
- Results sorted by score (descending), then timestamp (descending)

#### Tier 3: Checkpoint Storage (crash recovery via PostgreSQL)

**File:** `src/database/checkpoint_backend.py`
**Class:** `CheckpointManager`

Saves the full agent execution state to PostgreSQL at each LangGraph node. If the app crashes mid-query, the conversation can be resumed from the last checkpoint.

**Requirements:** `USE_POSTGRES=true` + `USE_CHECKPOINTS=true` + valid `DATABASE_URL`

**Key Methods:**
- `get_checkpointer()` — Returns `PostgresSaver` for LangGraph graph compilation
- `is_available()` — Check if PostgreSQL is configured and reachable
- `cleanup()` — Close connections

#### Memory Manager (Coordinator)

**File:** `src/agent/memory/memory_manager.py`
**Class:** `MemoryManager`

Single entry point that coordinates Tier 1 + Tier 2. No external code should directly access `ConversationMemory` or `EpisodicMemory`.

```python
MemoryManager(
    session_id=None,                # Auto-generated UUID
    storage_path=None,              # Default: data/episodic_memory/
    max_conversation_messages=10
)
```

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `add_user_message(content, metadata)` | → ConversationMemory |
| `add_assistant_message(content, tools_used, metadata)` | → ConversationMemory |
| `get_conversation_context()` | Current session formatted context |
| `get_relevant_history(query)` | Search episodic memory for past conversations |
| `get_full_context(query, include_episodic=True)` | **Combined**: past episodes + current session |
| `finalize_session(summary, outcomes, entities)` | End session → save as Episode to disk |
| `search_past_conversations(query)` | Direct episodic search |
| `get_user_preferences()` | Aggregated preferences |
| `clear_conversation()` | Clear session (keep episodic) |
| `clear_all_memory()` | Clear everything (use with caution) |

**`get_full_context()` output example:**

```
[Relevant past conversations]
1. 2026-01-15: User asked about deployment strategies. Tools used: web_search
   Topics: kubernetes, docker

[Previous conversation summary]
User asked about: setting up Redis. Used tools: rag_search

[Recent conversation]
User: How do I connect Redis to my Flask app?
Assistant: You can use the flask-redis extension...
User: What about caching?
```

---

### 6. Reflection & Learning System

#### Reflection Module

**File:** `src/agent/reflection/reflection_module.py`
**Class:** `ReflectionModule`

After each query, the agent evaluates its own performance: Did it pick the right tool? Was the answer good? What could be improved?

**Reflection Types** (enum):
- `TOOL_SELECTION` — Was the right tool chosen?
- `TOOL_EXECUTION` — Did the tool run correctly?
- `ANSWER_QUALITY` — Was the answer helpful?
- `ERROR_ANALYSIS` — What went wrong?
- `SESSION_SUMMARY` — End-of-session review

**Key Methods:**
- `evaluate_tool_selection(context) -> Reflection`
- `evaluate_answer_quality(context) -> Reflection`
- `analyze_error(error, context) -> Reflection`
- `save_reflection(reflection)` — Persist to `data/reflections/reflections.jsonl`

#### Learning Module

**File:** `src/agent/reflection/learning_module.py`
**Class:** `LearningModule`

Extracts patterns from reflections and tool usage over time. Helps the agent make better decisions.

**What It Tracks:**
- Tool usage counters (how often each tool is used)
- Tool success rates (success/failure per tool)
- Tool response times (average duration per tool)
- Query → tool mappings (which queries map to which tools)
- Error patterns (recurring error categories)
- Quality scores (answer quality over time)

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `record_tool_use(tool, success, duration)` | Log a tool execution |
| `record_error(error_category, tool)` | Log an error |
| `get_optimal_tool_for_query(query_type)` | Suggest best tool based on history |
| `get_success_rate(tool)` | Success % for a tool |
| `get_improvement_suggestions()` | Auto-generated improvement tips |

**Storage:** `data/learning/learning_data.pkl` (Python pickle)

---

### 7. Manager Agent & Multi-Agent Orchestration

**File:** `src/agent/manager_agent.py`
**Class:** `ManagerAgent`

For complex tasks, the manager agent breaks the work into subtasks and distributes them to specialized agents.

**Architecture:**
```
ManagerAgent (planner + coordinator)
  ├── QAAgentInterface → QA tools (test cases, BDD, bug reports)
  ├── DevAgentInterface → Code generation & analysis
  ├── DocAgentInterface → Documentation generation
  └── SecurityAgentInterface → Security analysis (future)
```

**Specialized Agents** (`src/agent/specialized_agents.py`):
- Each agent wraps a set of tools relevant to its domain
- Has a `capabilities` property describing what it can do
- Has an `execute(instruction, context)` method

**Shared Types** (`src/agent/types.py`):

| Type | Fields | Purpose |
|------|--------|---------|
| `AgentType` (enum) | QA, DEVELOPER, DOCUMENTATION, SECURITY, PERFORMANCE | Agent categories |
| `AgentCapability` | name, description, tools, keywords | What an agent can do |
| `TaskAssignment` | task_id, agent_type, instruction, priority, dependencies, status | A unit of work |
| `ExecutionPlan` | goal, tasks, execution_order, estimated_steps | Manager's plan |
| `ToolResult` | success, output, error, metadata | Tool execution result |

---

### 8. QA Pipeline

**File:** `src/agent/qa_pipeline.py`
**Class:** `QAPipeline`

Automated multi-stage QA workflow that runs after document import.

**Stages** (`PipelineStage` enum):

```
EXTRACT_REQUIREMENTS → GENERATE_TEST_CASES → ANALYZE_GAPS → COMPLETE
```

| Stage | What It Does |
|-------|--------------|
| Extract Requirements | Pull requirements from uploaded documents |
| Generate Test Cases | Create test cases from extracted requirements |
| Analyze Gaps | Identify coverage gaps and missing tests |
| Complete | Pipeline finished |

**Key Method:**
```python
result = pipeline.run(
    topic="Login feature",
    document_filter=None,
    skip_gaps=False
)
# Returns: { requirements, test_cases, gap_analysis, errors }
```

**Callbacks:** Progress updates via callback function for UI progress bars.

---

### 9. Policy Engine

**File:** `src/policy/policy_engine.py`
**Class:** `PolicyEngine`

Controls agent behavior, enforces rules, and maintains an audit trail.

**Policy Types:**

| Policy | What It Controls |
|--------|-----------------|
| `ToolPolicy` | Which tools can/cannot be used (allow/deny/warn/throttle) |
| `RateLimitPolicy` | Requests per minute/hour/day, tokens per session |
| `ContentPolicy` | Block inappropriate content via pattern matching |
| `CostPolicy` | Spending limits per request/session/day |
| `AccessPolicy` | User/role permissions, time-based access |

**Key Method:**
```python
decision = policy_engine.evaluate_tool_usage(context)
# decision.allowed = True/False
# decision.action = ALLOW | DENY | WARN | THROTTLE | REQUIRE_APPROVAL
# decision.message = "Explanation..."
```

**Enabled by:** `USE_POLICY_ENGINE=true`

---

### 10. Database & Checkpoint Persistence

**Files:** `src/database/`

| File | Class | Purpose |
|------|-------|---------|
| `models.py` | Session, Message, EpisodicMemory | Database model definitions |
| `postgres_backend.py` | PostgresBackend | PostgreSQL CRUD operations |
| `session_manager.py` | SessionManager | Session lifecycle (create, resume, end) |
| `checkpoint_backend.py` | CheckpointManager | LangGraph state checkpointing |

**Session Model Fields:**
- `session_id`, `user_id`, `title`, `created_at`, `updated_at`, `metadata`, `is_active`

**Message Model Fields:**
- `message_id`, `session_id`, `role`, `content`, `timestamp`, `metadata`, `tool_calls`, `sources`

---

### 11. Observability & Monitoring

**File:** `src/observability.py`
**Class:** `ObservabilityManager` (singleton)

OpenTelemetry instrumentation for distributed tracing and metrics.

**Features:**
- Traces RAG operations, agent execution, tool calls, LLM invocations
- Span processors with `BatchSpanProcessor`
- Context propagation across components

**Exporters:**

| Exporter | Use Case |
|----------|----------|
| Console | Development — print spans to terminal |
| OTLP/gRPC | Production — send to Jaeger, Honeycomb, Datadog, Grafana |
| Jaeger | Direct Jaeger exporter |

**Key Methods:**
- `get_tracer(name)` — Get tracer for a component
- `trace_operation(name, attributes)` — Context manager for tracing
- `record_metric(name, value, attributes)` — Record a metric

**Enabled by:** `ENABLE_OBSERVABILITY=true`

---

### 12. Redis Task Queue

**Files:** `src/task_queue/`

Async task processing for heavy workloads.

| File | Class | Purpose |
|------|-------|---------|
| `task_queue.py` | TaskQueue | Submit & manage tasks |
| `task_models.py` | Task, TaskPriority | Task data structures |
| `scheduler.py` | Scheduler | Task scheduling |
| `worker.py` | Worker | Worker pool |

**Usage:**
```python
from src.task_queue import TaskQueue, TaskPriority

queue = TaskQueue()
task_id = queue.submit_task(query="Analyze data", priority=TaskPriority.HIGH, user_id="user123")
result = queue.get_result(task_id, timeout=60)
```

**Enabled by:** `USE_REDIS_QUEUE=true`

---

### 13. Streamlit UI

**Main File:** `src/ui/streamlit_app_agent.py` (~2450 lines)

**Page Config:**
- Title: "QA Expert Assistant"
- Icon: test tube emoji
- Layout: wide
- Sidebar: expanded

**Tab-Based Layout:**

The app uses a two-level tab structure so Chat and Tools are always accessible:

```
Top-level:  [ 💬 Chat ]  [ 🛠️ Tools & Features ]

Inside "Tools & Features":
  [ 🚀 Quick Start ] [ 🎯 QA Tools ] [ 📁 Documents ] [ 🧪 Test Generator ] [ ⚙️ Settings ]
```

- **Chat tab** — Conversation UI. Shows welcome message when empty, chat history when active. Chat input is always at the bottom (outside tabs so it's visible on both).
- **Tools & Features tab** — Contains all sub-tabs for QA tools, document management, test generation, and settings.
- **QA tool forms** — When a QA tool button is clicked in the Tools tab, the input form appears **inline below the buttons** (not in a separate page). The selected button highlights with primary color and a checkmark. Submitted results go to Chat history.

Users can switch between Chat and Tools at any time without losing conversation state.

**Major Functions:**

| Function | Purpose |
|----------|---------|
| `configure_page()` | Page settings, CSS injection |
| `initialize_agent_session_state()` | Setup session variables |
| `initialize_agent_system()` | Lazy-init agent with all tools |
| `get_or_create_agent()` | Get cached agent or initialize on first use |
| `render_minimal_sidebar()` | Session stats, quick actions (Clear/Reset) |
| `render_main_chat_agent()` | Top-level tab layout + chat rendering |
| `render_welcome_message_agent()` | Feature sub-tabs (QA Tools, Documents, etc.) |
| `handle_agent_query(prompt)` | Main query handler → `agent.execute()` |
| `render_chat_message_agent(msg)` | Render a single chat message with styling |

**Session State Variables:**
```python
st.session_state = {
    "messages": [],                    # Chat history
    "agent": None,                     # AgentExecutorV3 instance (lazy)
    "agent_initialized": False,
    "enable_memory": True,
    "enable_reflection": True,
    "conversation_thread_id": "uuid",
    "session_queries": 0
}
```

**Supporting UI Files:**

| File | Purpose |
|------|---------|
| `state_manager.py` | Initialize defaults, cached RAG chain |
| `enhanced_components.py` | Welcome cards, dashboards, QA panels |
| `styles.py` | Custom CSS for modern dark theme |
| `input_validation.py` | Input sanitization via `InputValidator` class |
| `components.py` | Basic reusable components |

---

## Key Flows (End-to-End)

### Flow 1: User Query → Agent Response

```
1. USER INPUT (Streamlit)
   └─ streamlit_app_agent.py → process_user_query()
   └─ Message added to st.session_state.messages

2. AGENT EXECUTION (LangGraph state machine)
   └─ agent_executor_v3.py → graph.invoke(state)

   a. UNDERSTAND NODE
      ├─ memory_manager.add_user_message(query)
      ├─ context = memory_manager.get_full_context(query)
      │   ├─ Search episodic memory for relevant past conversations
      │   ├─ Get conversation summary (if exists)
      │   └─ Get recent messages (last 10)
      └─ state['memory_context'] = context

   b. ROUTE NODE
      ├─ LLM sees: query + tool descriptions + memory context
      ├─ Outputs: tool name (or "none" for memory-only answer)
      └─ state['selected_tool'] = chosen tool

   c. CONDITIONAL: execute or finish?
      ├─ If tool == None → skip to SYNTHESIZE (memory answer)
      └─ If tool selected → continue to EXECUTE

   d. EXECUTE NODE
      ├─ Policy engine check (if enabled)
      ├─ tool = tool_registry.get_tool(name)
      ├─ result = tool.run(query)
      ├─ learning_module.record_tool_use(name, success, duration)
      └─ state['tool_results'].append(result)

   e. SYNTHESIZE NODE
      ├─ LLM generates response from tool result + memory context
      ├─ memory_manager.add_assistant_message(answer, tools_used)
      └─ state['final_answer'] = answer

   f. REFLECT NODE (if enabled)
      ├─ reflection_module.evaluate_tool_selection(context)
      ├─ reflection_module.evaluate_answer_quality(context)
      └─ learning_module records patterns

3. RESPONSE DELIVERY
   ├─ Display answer in Streamlit chat
   ├─ Show sources (if RAG)
   └─ Update session stats

4. PERSISTENCE
   ├─ Checkpoint state to PostgreSQL (if enabled)
   └─ On session end: memory_manager.finalize_session() → saves Episode JSON
```

### Flow 2: Document Upload & Indexing

```
Upload file (Streamlit)
  → Parse (PyPDF2, python-docx, or plain text)
  → Chunk (RecursiveCharacterTextSplitter, 800 chars, 100 overlap)
  → Embed (HuggingFace sentence-transformers/all-MiniLM-L6-v2)
  → Store (FAISS local index or Pinecone cloud)
  → Save index to disk
```

### Flow 3: QA Pipeline

```
Trigger pipeline (user clicks "Run QA")
  → Stage 1: Extract requirements from uploaded docs
  → Stage 2: Generate test cases from requirements
  → Stage 3: Analyze gaps in coverage
  → Return: { requirements, test_cases, gap_analysis }
```

---

## Configuration Reference

### Required

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key (free at console.groq.com) |

### LLM

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `groq` | `groq` or `google` |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model name |
| `GEMINI_MODEL` | `gemini-2.0-flash-exp` | Google model name |
| `LLM_TEMPERATURE` | `0.7` | Creativity (0.0–1.0) |
| `LLM_MAX_TOKENS` | `2048` | Max response length |

### Embeddings

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_PROVIDER` | `huggingface` | `huggingface` or `google` |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `GOOGLE_API_KEY` | — | Required if using Google embeddings |

### RAG

| Variable | Default | Description |
|----------|---------|-------------|
| `CHUNK_SIZE` | `800` | Characters per text chunk |
| `CHUNK_OVERLAP` | `100` | Overlap between chunks |
| `TOP_K_RESULTS` | `5` | Number of chunks retrieved |
| `TOP_K_REQUIREMENTS` | `10` | Chunks for requirement queries |
| `ENABLE_RERANKING` | `true` | Cross-encoder reranking |
| `RERANK_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Reranker model |
| `RELEVANCE_THRESHOLD` | `0.3` | Minimum relevance score (0–1) |

### Agent

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_ENABLED` | `true` | Enable agent system |
| `AGENT_MODE` | `hybrid` | `react`, `plan-execute`, or `hybrid` |
| `AGENT_MAX_ITERATIONS` | `10` | Max tool execution loops |
| `AGENT_TIMEOUT` | `120` | Timeout in seconds |
| `AGENT_VERBOSE` | `true` | Show reasoning in output |

### Memory

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_ENABLED` | `true` | Enable memory system |
| `MEMORY_WINDOW_SIZE` | `10` | Recent messages to keep in full |
| `MEMORY_SUMMARY_FREQUENCY` | `5` | How often to summarize |

### Tools

| Variable | Default | Description |
|----------|---------|-------------|
| `WEB_SEARCH_ENABLED` | `true` | Enable web search |
| `WEB_SEARCH_PROVIDER` | `duckduckgo` | `duckduckgo` or `tavily` |
| `TAVILY_API_KEY` | — | Required if using Tavily |
| `NEWSAPI_KEY` | — | Optional for news tool |
| `CALCULATOR_ENABLED` | `true` | Enable calculator |
| `CODE_EXECUTOR_ENABLED` | `false` | Enable Python executor (security risk) |
| `FILE_OPS_ENABLED` | `true` | Enable file operations |

### Vector Store

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_PINECONE` | `false` | Use Pinecone (else FAISS) |
| `PINECONE_API_KEY` | — | Required if using Pinecone |
| `PINECONE_INDEX_NAME` | `rag-agent` | Pinecone index name |
| `PINECONE_NAMESPACE` | `""` | Pinecone namespace |
| `PINECONE_METRIC` | `cosine` | cosine, euclidean, dotproduct |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_POSTGRES` | `false` | Enable PostgreSQL |
| `USE_CHECKPOINTS` | `true` | Enable LangGraph checkpoints |
| `DATABASE_URL` | — | Full connection string |
| `POSTGRES_USER` | `postgres` | DB username |
| `POSTGRES_PASSWORD` | `postgres` | DB password |
| `POSTGRES_HOST` | `localhost` | DB host |
| `POSTGRES_PORT` | `5432` | DB port |
| `POSTGRES_DB` | `rag_chatbot` | DB name |

### Policy & Queue

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_POLICY_ENGINE` | `true` | Enable policy enforcement |
| `USE_REDIS_QUEUE` | `false` | Enable Redis task queue |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |

### Confluence

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFLUENCE_ENABLED` | `false` | Enable Confluence integration |
| `CONFLUENCE_URL` | — | Confluence base URL |
| `CONFLUENCE_USERNAME` | — | Confluence email |
| `CONFLUENCE_API_TOKEN` | — | Confluence API token |
| `CONFLUENCE_SPACE_KEY` | `DEFAULT` | Space to import from |

### Observability

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_OBSERVABILITY` | `false` | Enable OpenTelemetry |
| `OTEL_SERVICE_NAME` | `rag-agent` | Service name in traces |
| `OTEL_ENVIRONMENT` | `development` | Environment label |
| `OTEL_EXPORTER_TYPE` | `console` | `console`, `otlp`, or `jaeger` |
| `OTEL_EXPORTER_ENDPOINT` | `http://localhost:4317` | Exporter endpoint |
| `TRACE_RAG_OPERATIONS` | `true` | Trace RAG pipeline |
| `TRACE_AGENT_OPERATIONS` | `true` | Trace agent execution |
| `TRACE_TOOL_CALLS` | `true` | Trace tool calls |
| `TRACE_LLM_CALLS` | `true` | Trace LLM invocations |

---

## API Reference

### RAG Chain (direct document Q&A)

```python
from src.system_init import initialize_system

rag_chain = initialize_system(use_documents=True)
result = rag_chain.ask(question="What is RAG?", top_k=3)
# Returns: { question, answer, context, sources, documents }
```

### Agent Executor (full agent with tools + memory)

```python
from src.agent.agent_executor_v3 import AgentExecutorV3
from src.agent.tool_registry import ToolRegistry

agent = AgentExecutorV3(
    llm=llm,
    tool_registry=tool_registry,
    config=Config,
    enable_memory=True,
    enable_reflection=True
)

result = agent.execute(query="What's the latest AI news?", session_id="user123")
# Returns: { answer, reasoning, tools_used, sources, memory_context }
```

### Memory Manager (standalone usage)

```python
from src.agent.memory import MemoryManager

mm = MemoryManager(session_id="session-1")
mm.add_user_message("What is RAG?")
mm.add_assistant_message("RAG is...", tools_used=["document_search"])

# Get full context for next query
context = mm.get_full_context("Tell me more", include_episodic=True)

# End session — saves to disk as Episode
mm.finalize_session()
```

### Redis Queue (async processing)

```python
from src.task_queue import TaskQueue, TaskPriority

queue = TaskQueue()
task_id = queue.submit_task(query="Analyze this data", priority=TaskPriority.HIGH)
result = queue.get_result(task_id, timeout=60)
```

---

## Scripts & Utilities

| Script | Location | Command | Purpose |
|--------|----------|---------|---------|
| Setup DB | `scripts/setup/init_database.py` | `make setup` | Create PostgreSQL tables & indexes |
| Migrate to Pinecone | `scripts/setup/migrate_to_pinecone.py` | Manual | Migrate FAISS → Pinecone |
| Reindex Docs | `scripts/maintenance/reindex_documents.py` | `make reindex` | Rebuild the entire vector store |
| Health Check | `scripts/monitoring/check_backend_status.py` | `make check` | Check all service connections |

---

## Testing

### Run Tests

```bash
make test          # All tests
make test-quick    # Unit tests only (fast)
```

### Test Structure

| Directory | Tests | What They Cover |
|-----------|-------|-----------------|
| `tests/unit/` | `test_config.py` | Configuration validation |
| | `test_embeddings.py` | Embedding generation |
| | `test_rag_chain_unit.py` | RAG pipeline logic |
| | `test_memory.py` | Memory system (conversation + episodic) |
| | `test_tools.py` | Individual tool execution |
| | `test_vector_store.py` | Vector store operations |
| `tests/integration/` | `test_agent_system.py` | Full agent workflow |
| | `test_manager_agent.py` | Multi-agent orchestration |
| | `test_qa_tools.py` | QA tool integration |
| | `test_rag_chain.py` | RAG end-to-end |
| | `test_conversation_memory_fix.py` | Memory persistence |
| | `test_relevance_filter.py` | Reranking accuracy |

**Fixtures:** `tests/conftest.py` — shared pytest fixtures and mocks.

---

## Design Patterns

| Pattern | Where Used | Example |
|---------|------------|---------|
| **State Machine** | Agent Executor | LangGraph nodes + conditional edges |
| **Registry** | Tool Registry | `register()`, `get_tool()`, `get_all_tools()` |
| **Strategy** | Tools | Common `BaseTool` interface, interchangeable implementations |
| **Singleton** | Observability | `ObservabilityManager` — single instance |
| **Factory** | Document Manager | Picks FAISS or Pinecone based on config |
| **Coordinator** | Memory Manager | Unified interface over ConversationMemory + EpisodicMemory |
| **Template Method** | BaseTool | `run()` wraps `_run()` with timing/error handling |
| **Observer** | QA Pipeline | Progress callbacks for UI updates |

---

## Security

### Protected Against

| Threat | Mitigation |
|--------|------------|
| SQL Injection | Parameterized queries in PostgreSQL backend |
| Code Injection | RestrictedPython sandbox for code executor |
| Path Traversal | File operations sandboxed to `data/workspace/` |
| Prompt Injection | Input validation via `InputValidator` class |
| Rate Abuse | Policy engine rate limits (requests/min, tokens/session) |
| Unsafe Tools | `CODE_EXECUTOR_ENABLED=false` and `FILE_OPS_ENABLED` scoped by default |

### Secret Handling

- All secrets loaded from `.env` via `python-dotenv`
- Never logged, printed, or exposed in UI
- `.env` is gitignored

### Security TODO

- User authentication (OAuth/JWT)
- HTTPS in production
- Secrets manager integration (Vault/AWS Secrets Manager)
- Content Security Policy headers

---

## Deployment

### Local

```bash
make run
# or: double-click run.command (Mac) / run.bat (Windows)
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt && playwright install chromium
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "src/ui/streamlit_app_agent.py", "--server.port", "8501"]
```

### Production Checklist

- [ ] Set `USE_POLICY_ENGINE=true`
- [ ] Configure PostgreSQL (`USE_POSTGRES=true`)
- [ ] Enable observability (`ENABLE_OBSERVABILITY=true`)
- [ ] Set up Redis for queue (`USE_REDIS_QUEUE=true`)
- [ ] Disable dangerous tools (`CODE_EXECUTOR_ENABLED=false`)
- [ ] Configure rate limits in policy engine
- [ ] Add user authentication
- [ ] Use HTTPS / reverse proxy
- [ ] Set `OTEL_ENVIRONMENT=production`

---

## Troubleshooting

### Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Vector store not initialized" | No documents indexed | Upload documents via UI or place in `data/documents/` |
| Slow first query (~90s) | Embedding model downloading | One-time download; subsequent runs are instant |
| LLM rate limit errors | Groq free tier limits | Wait and retry, or upgrade Groq plan |
| Web agent fails | Playwright not installed | Run `playwright install chromium` |
| PostgreSQL connection failed | DB not running | Set `USE_POSTGRES=false` in `.env` if not using PostgreSQL |
| Memory not persisting | episodic_memory dir missing | Auto-created on first use; check permissions |
| "No module named src" | Wrong working directory | Run from project root |
| Streamlit port in use | Another instance running | Kill process on port 8501 or use `--server.port 8502` |
| App hangs with no response | `USE_POSTGRES=true` but no DB running | Set `USE_POSTGRES=false` in `.env` — TCP timeout causes hang |
| Agent not initialized error | `FileOpsTool()` missing argument | Already fixed — `workspace_root` path now passed automatically |
| Raw gibberish in web responses | LLM synthesis not running | Already fixed — `web_agent` results now go through synthesis |

### Performance Issues

| Symptom | Fix |
|---------|-----|
| Slow page load (10s+) | Already fixed — agent uses lazy initialization |
| Slow queries (60s+) | Already fixed — async DB writes |
| Repetitive web results | Already fixed — fingerprint-based deduplication |
| Wrong tool for conversation | Already fixed — "none" option for memory-based answers |
| Raw search snippets in output | Already fixed — web_agent + web_search + news_api results synthesized by LLM |

### Python 3.14 Compatibility

This codebase runs on Python 3.14 which has stricter variable scoping rules. Key fixes applied:

- **No local re-imports in nested scopes** — `import re` and `from langchain_core.messages import HumanMessage` must be at the top of the file, not inside `try` blocks or methods. Python 3.14 treats local imports as shadowing the module-level import for the entire enclosing function, causing `UnboundLocalError` when the import is in an `if` branch that isn't taken.
- **`@st.cache_resource` not stacked** — Using two `@st.cache_resource` decorators on the same function causes caching corruption. Use only one.

---

## Glossary

| Term | Definition |
|------|------------|
| **RAG** | Retrieval-Augmented Generation — retrieve relevant docs, then generate answer |
| **Embedding** | Dense vector representation of text for similarity search |
| **Vector Store** | Database for storing/searching embeddings (FAISS local or Pinecone cloud) |
| **Chunk** | Text segment (~800 chars) created by splitting documents for indexing |
| **Reranking** | Cross-encoder model that re-scores retrieved chunks for relevance |
| **LangGraph** | State machine framework for building agent workflows |
| **Tool** | Agent capability (search docs, browse web, calculate, generate tests, etc.) |
| **Episodic Memory** | Long-term JSON summaries of past conversation sessions |
| **Conversation Memory** | Short-term in-session message history with auto-summarization |
| **Checkpoint** | Serialized agent state saved to PostgreSQL for crash recovery |
| **Reflection** | Agent self-evaluation of its decisions and answer quality |
| **Learning Module** | Pattern extractor that tracks tool success rates and optimizes future decisions |
| **Policy Engine** | Rule system controlling which tools/actions are allowed |
| **Manager Agent** | Orchestrator that breaks complex tasks into subtasks for specialized agents |
| **QA Pipeline** | Automated workflow: extract requirements → generate tests → analyze gaps |

---

## Key Classes Quick Reference

| Component | Class | File | Purpose |
|-----------|-------|------|---------|
| Agent | `AgentExecutorV3` | `src/agent/agent_executor_v3.py` | LangGraph state machine orchestrator |
| State | `AgentState` | `src/agent/agent_state.py` | TypedDict defining execution state |
| Tools | `ToolRegistry` | `src/agent/tool_registry.py` | Tool registry & management |
| Tool Base | `BaseTool` | `src/agent/tools/base_tool.py` | Abstract tool base class |
| RAG | `RAGChain` | `src/rag_chain.py` | Retrieval-augmented generation |
| Memory | `MemoryManager` | `src/agent/memory/memory_manager.py` | Unified memory interface |
| Conversation | `ConversationMemory` | `src/agent/memory/conversation_memory.py` | Session memory |
| Episodic | `EpisodicMemory` | `src/agent/memory/episodic_memory.py` | Cross-session memory |
| Reflection | `ReflectionModule` | `src/agent/reflection/reflection_module.py` | Self-evaluation |
| Learning | `LearningModule` | `src/agent/reflection/learning_module.py` | Pattern extraction |
| Manager | `ManagerAgent` | `src/agent/manager_agent.py` | Multi-agent orchestrator |
| Config | `Config` | `src/config.py` | Central configuration |
| Embeddings | `EmbeddingManager` | `src/embeddings.py` | Text splitting & embeddings |
| Vector Store | `VectorStoreManager` | `src/vector_store.py` | FAISS vector store |
| Doc Manager | `DocumentManager` | `src/document_manager.py` | Unified doc interface |
| Checkpoints | `CheckpointManager` | `src/database/checkpoint_backend.py` | LangGraph checkpointing |
| Policy | `PolicyEngine` | `src/policy/policy_engine.py` | Behavior control & audit |
| Observability | `ObservabilityManager` | `src/observability.py` | OpenTelemetry tracing |
| Task Queue | `TaskQueue` | `src/task_queue/task_queue.py` | Redis task management |
| UI | `streamlit_app_agent.py` | `src/ui/streamlit_app_agent.py` | Web interface |
| State Mgr | `state_manager.py` | `src/ui/state_manager.py` | Session state |

---

## Related Documentation

| Document | Location | Topic |
|----------|----------|-------|
| Configuration | `docs/CONFIGURATION.md` | All config options |
| Auto Indexing | `docs/operations/AUTO_INDEXING_GUIDE.md` | Automatic document indexing |
| Checkpoints | `docs/operations/CHECKPOINT_GUIDE.md` | Crash recovery setup |
| Deployment | `docs/setup/DEPLOYMENT_GUIDE.md` | Production deployment |
| External Services | `docs/setup/EXTERNAL_SERVICES_SETUP.md` | Third-party integrations |
| Observability | `docs/operations/OBSERVABILITY_GUIDE.md` | Monitoring & tracing |
| Pinecone Migration | `docs/operations/PINECONE_MIGRATION_GUIDE.md` | FAISS → Pinecone |
| Policy Engine | `docs/operations/POLICY_ENGINE_GUIDE.md` | Policy configuration |
| PostgreSQL | `docs/setup/POSTGRES_SETUP.md` | Database setup |
| QA Features | `docs/features/QA_FEATURES_REFERENCE.md` | QA tool reference |
| QA Tools | `docs/features/QA_TOOLS_GUIDE.md` | QA tool usage guide |
| Redis Queue | `docs/operations/REDIS_QUEUE_GUIDE.md` | Queue setup |
| Relevance | `docs/features/RELEVANCE_FILTERING.md` | Search relevance tuning |
| Streamlit Deploy | `docs/setup/STREAMLIT_DEPLOYMENT.md` | Streamlit Cloud deployment |
| Web Scraping | `docs/features/WEB_SCRAPING_ENHANCEMENTS.md` | Web agent details |

---

## Changelog (2026-02-09)

Bugfixes and improvements applied during this session:

### Bugs Fixed

| # | Bug | Root Cause | Fix | File(s) |
|---|-----|-----------|-----|---------|
| 1 | App hangs with no response | `USE_POSTGRES=true` in `.env` but PostgreSQL not running — TCP connection timeout blocks the entire query | Set `USE_POSTGRES=false` | `.env` |
| 2 | Agent silently fails to initialize | `FileOpsTool()` called without required `workspace_root` argument — crashes agent init, error swallowed | Pass `workspace_root=Path("data/workspace")` | `src/ui/streamlit_app_agent.py:183` |
| 3 | `UnboundLocalError: HumanMessage` | Local `from langchain_core.messages import HumanMessage` inside a `try` block shadows the module-level import on Python 3.14 | Removed local import; use top-level import only | `src/agent/agent_executor_v3.py:548` |
| 4 | `UnboundLocalError: re` | Local `import re` inside nested `try` blocks (3 occurrences) shadows the module-level import on Python 3.14 | Moved `import re` to top of file; removed all 3 local imports | `src/agent/agent_executor_v3.py:3` |
| 5 | Raw gibberish in web responses | LLM synthesis only ran for `web_search` and `news_api` but the router often selects `web_agent` — raw snippets returned unsynthesized | Added `web_agent` to the synthesis condition | `src/agent/agent_executor_v3.py:588` |
| 6 | Double `@st.cache_resource` decorator | Two stacked `@st.cache_resource` decorators on `_get_rag_chain()` caused caching corruption | Removed the duplicate decorator | `src/ui/streamlit_app_agent.py:138` |

### UI Improvements

| # | Change | Before | After | File(s) |
|---|--------|--------|-------|---------|
| 1 | Tab-based layout | Welcome tabs disappear when chat starts | Two top-level tabs: "Chat" and "Tools & Features" — always accessible | `src/ui/streamlit_app_agent.py` |
| 2 | LLM answer quality | Wall of raw search snippets concatenated together | 3 short, readable paragraphs structured as a news briefing | `src/agent/agent_executor_v3.py` (synthesis prompt) |
| 3 | macOS launcher | No way to start app by clicking | `run.command` file — double-click in Finder to start | `run.command` (new file) |
| 4 | QA tool forms inline | Clicking QA tool button did nothing visible (form appeared in hidden Chat tab) | Form appears inline below buttons in the Tools tab; selected button highlights with primary color + checkmark | `src/ui/streamlit_app_agent.py`, `src/ui/enhanced_components.py` |
| 5 | QA button selected state | No visual feedback when a QA tool is selected | Selected button turns primary color with ✓ indicator; others stay secondary | `src/ui/enhanced_components.py` |

### Security & Performance (commit `c8200c7`)

| Area | Changes |
|------|---------|
| Code executor | Block sandbox escapes (`__mro__`, `__reduce__`), add Windows timeout |
| File ops | Symlink validation, TOCTOU protection, glob escaping |
| Web agent | Fix SSRF/DNS rebinding, block numeric IPs, remove `--no-sandbox` |
| Policy engine | Rate limit persistence, regex timeout protection |
| Learning module | `RestrictedUnpickler`, SHA256 integrity checks, atomic writes |
| Vector store | FAISS checksum verification, batch size 50, adaptive delay |
| Memory manager | Request-level caching, LRU cache for episodic search, cache invalidation |
| Reflection module | Write batching with background flush |
| Task queue worker | Document indexing (PDF, DOCX, TXT, MD), adaptive polling with backoff |
| RAG chain | Pytest syntax validation, test case parsing |
| Tests | 57 new security and bug fix tests (`tests/test_security.py`, `tests/test_bug_fixes.py`) |

### Files Modified

| File | Changes |
|------|---------|
| `.env` | `USE_POSTGRES=false` |
| `src/agent/agent_executor_v3.py` | Added `import re` at top; removed 3 local `import re`; removed local `import HumanMessage`; added `web_agent` to synthesis; improved synthesis prompt |
| `src/ui/streamlit_app_agent.py` | Fixed `FileOpsTool(workspace_root=...)` init; removed duplicate `@st.cache_resource`; tab-based layout; QA tool forms inline in Tools tab; chat input outside tabs |
| `src/ui/enhanced_components.py` | QA dashboard buttons with selected state (primary color + checkmark) |
| `src/agent/memory/memory_manager.py` | Request-level context caching, LRU cache for episodic search, cache invalidation |
| `src/agent/reflection/learning_module.py` | RestrictedUnpickler, SHA256 integrity, atomic writes |
| `src/agent/reflection/reflection_module.py` | Write batching with background flush |
| `src/agent/tools/code_executor_tool.py` | Block sandbox escapes, Windows timeout |
| `src/agent/tools/file_ops_tool.py` | Symlink validation, TOCTOU protection |
| `src/agent/tools/web_agent_tool.py` | SSRF/DNS rebinding fix, block numeric IPs |
| `src/policy/policy_engine.py` | Rate limit persistence, regex timeout protection |
| `src/rag_chain.py` | Pytest syntax validation, test case parsing |
| `src/vector_store.py` | FAISS checksum verification, batch size 50 |
| `src/task_queue/worker.py` | Document indexing, adaptive polling with backoff |
| `run.command` | New file — macOS double-click launcher |
| `docs/architecture/CODEBASE_GUIDE.md` | Comprehensive rewrite with all components documented |

---

*This document reflects the codebase as of 2026-02-09.*
