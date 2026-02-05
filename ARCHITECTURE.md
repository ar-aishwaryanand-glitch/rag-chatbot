# System Architecture

## Overview

This is an **Agentic RAG (Retrieval-Augmented Generation) System** built with LangChain and LangGraph. The system combines document retrieval with an intelligent agent that can use multiple tools to answer questions, search the web, perform calculations, and more.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                      │
│                      (Streamlit Web App)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      Agent Execution Layer                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  AgentExecutorV3 (LangGraph State Machine)              │   │
│  │  ├─ Phase 1: Understanding (Query Analysis)             │   │
│  │  ├─ Phase 2: Tool Routing & Execution                   │   │
│  │  ├─ Phase 3: Answer Synthesis                           │   │
│  │  └─ Phase 4: Reflection (Optional)                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │  Tool Registry (10+ Tools)                              │   │
│  │  ├─ RAG Tool (Document Search)                          │   │
│  │  ├─ Web Search (DuckDuckGo/Tavily)                      │   │
│  │  ├─ Calculator                                           │   │
│  │  ├─ Code Executor                                        │   │
│  │  ├─ File Operations                                      │   │
│  │  ├─ News API                                             │   │
│  │  └─ Document Management                                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Memory Management Layer                       │
│  ┌────────────────────┐  ┌──────────────────────────────────┐   │
│  │ Conversation Memory│  │ Episodic Memory                  │   │
│  │ (Short-term)       │  │ (Long-term patterns)             │   │
│  └────────────────────┘  └──────────────────────────────────┘   │
│                             │                                    │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  Memory Manager (Unified Access)                       │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     RAG Core Components                          │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐     │
│  │  Embeddings  │  │ Vector Store  │  │ Document Manager │     │
│  │  (HuggingF)  │  │ (FAISS/Pine-  │  │ (Chunking, Meta) │     │
│  │              │  │  cone)        │  │                  │     │
│  └──────────────┘  └───────────────┘  └──────────────────┘     │
│                             │                                    │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  RAG Chain (Retrieve → Format → Generate)             │     │
│  └────────────────────────────────────────────────────────┘     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   Persistence & Infrastructure                   │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │  PostgreSQL  │  │  Checkpoint  │  │  Session Manager    │   │
│  │  (Supabase)  │  │  Backend     │  │  (Thread tracking)  │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. **Agent System** ([docs/AGENT_SYSTEM.md](docs/AGENT_SYSTEM.md))
- **AgentExecutorV3**: State machine-based agent using LangGraph
- **Tool Registry**: Manages all available tools
- **Agent State**: Tracks execution state across phases
- **Reflection Module**: Self-correction and learning

### 2. **Memory System** ([docs/MEMORY_SYSTEM.md](docs/MEMORY_SYSTEM.md))
- **Conversation Memory**: Short-term message history
- **Episodic Memory**: Long-term interaction patterns
- **Memory Manager**: Unified memory access and persistence
- **Checkpoint Integration**: Conversation state persists across restarts

### 3. **RAG Core** ([docs/RAG_CORE.md](docs/RAG_CORE.md))
- **Embeddings**: Convert text to vectors (HuggingFace/Google)
- **Vector Store**: FAISS (local) or Pinecone (cloud)
- **Document Manager**: Chunking, metadata, indexing
- **RAG Chain**: Retrieval + Generation pipeline

### 4. **Database & Persistence** ([docs/DATABASE_PERSISTENCE.md](docs/DATABASE_PERSISTENCE.md))
- **PostgreSQL Backend**: Session storage (Supabase)
- **Checkpoint Backend**: LangGraph state persistence
- **Session Manager**: Multi-user session handling

### 5. **Tools** ([docs/TOOLS_REFERENCE.md](docs/TOOLS_REFERENCE.md))
- Document search, web search, calculator
- Code execution, file operations
- News API, document management

## Data Flow

### Query Processing Flow

```
1. User submits query via Streamlit UI
   ↓
2. SessionManager retrieves/creates thread_id
   ↓
3. AgentExecutorV3.execute(query, thread_id)
   │
   ├─→ CheckpointBackend loads previous state (if exists)
   │
   ├─→ MemoryManager restores conversation_messages from state
   │
   ├─→ Phase 1: Understanding
   │   └─→ Add user message to memory
   │       Get memory context for LLM
   │
   ├─→ Phase 2: Tool Routing
   │   └─→ LLM selects appropriate tool
   │       Tool executes (e.g., RAG search, web search)
   │
   ├─→ Phase 3: Answer Synthesis
   │   └─→ LLM generates final answer
   │       Add assistant message to memory
   │       Save conversation_messages to state
   │
   └─→ Phase 4: Reflection (optional)
       └─→ Self-evaluate answer quality
   ↓
4. CheckpointBackend saves state to PostgreSQL
   ↓
5. Return answer to UI
```

### Document Indexing Flow

```
1. User uploads document (PDF/URL) via Streamlit
   ↓
2. DocumentLoader extracts text
   ↓
3. DocumentManager chunks text (800 chars, 100 overlap)
   ↓
4. EmbeddingManager generates vectors
   ↓
5. VectorStore stores embeddings
   ↓
6. Metadata saved for retrieval
```

## Technology Stack

### Core Framework
- **LangChain**: LLM orchestration and chains
- **LangGraph**: State machine for agent execution
- **Streamlit**: Web UI framework

### LLM & Embeddings
- **LLM**: Groq (Llama 3.3 70B) or Google Gemini
- **Embeddings**: HuggingFace (sentence-transformers) or Google

### Storage
- **Vector DB**: FAISS (local) or Pinecone (cloud)
- **Persistence**: PostgreSQL (Supabase)
- **Checkpoints**: langgraph-checkpoint-postgres

### Tools & APIs
- **Web Search**: DuckDuckGo, Tavily
- **News**: NewsAPI
- **Document Processing**: PyPDF2, BeautifulSoup

## Configuration

All configuration is managed via `.env` file and [src/config.py](src/config.py). See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for details.

### Key Settings

```bash
# LLM
LLM_PROVIDER=groq
GROQ_MODEL=llama-3.3-70b-versatile

# Agent
AGENT_ENABLED=true
AGENT_MODE=hybrid
MEMORY_ENABLED=true

# Database
USE_POSTGRES=true
USE_CHECKPOINTS=true
DATABASE_URL=postgresql://...

# Tools
WEB_SEARCH_ENABLED=true
CALCULATOR_ENABLED=true
CODE_EXECUTOR_ENABLED=false  # Disabled for safety
```

## Design Principles

### 1. **Modularity**
Each component (RAG, Agent, Memory, Tools) is independent and replaceable.

### 2. **State Persistence**
All agent state (including conversation messages) persists in checkpoints for crash recovery and multi-session continuity.

### 3. **Safety First**
- Code execution disabled by default
- Policy engine for content filtering
- Sandboxed file operations

### 4. **Observability**
- OpenTelemetry integration
- Metrics and tracing for all operations
- Performance monitoring

### 5. **Scalability**
- Pinecone for cloud vector storage
- PostgreSQL for multi-user sessions
- Redis task queue (optional)

## Key Features

### Multi-Phase Agent Execution
1. **Understanding**: Query analysis with memory context
2. **Routing**: Intelligent tool selection
3. **Synthesis**: Answer generation from tool results
4. **Reflection**: Self-evaluation and learning

### Conversation Memory Persistence
- Messages stored in agent state
- Restored from checkpoints on resume
- Full conversation history available across sessions

### Tool Ecosystem
- 10+ built-in tools
- Easy to extend with new tools
- Automatic parameter validation

### Document Management
- Support for PDF and web URLs
- Automatic chunking and indexing
- Metadata tracking (source, topic, upload date)

## Getting Started

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Index Documents**
   ```bash
   python reindex_documents.py
   ```

4. **Run Application**
   ```bash
   streamlit run src/ui/streamlit_app_agent.py
   ```

## Architecture Decisions

### Why LangGraph for Agent?
- State persistence via checkpoints
- Explicit control over agent phases
- Better observability than AgentExecutor
- Supports complex multi-step workflows

### Why Conversation Memory in State?
- Ensures memory persists across checkpoint resumes
- Prevents context loss on restart
- Enables true multi-session conversations

### Why PostgreSQL + FAISS?
- PostgreSQL: Session and checkpoint storage (persistent)
- FAISS: Fast local vector search (ephemeral)
- Can upgrade to Pinecone for production

## Related Documentation

- [Agent System Deep Dive](docs/AGENT_SYSTEM.md)
- [Memory System Guide](docs/MEMORY_SYSTEM.md)
- [RAG Core Components](docs/RAG_CORE.md)
- [Database & Persistence](docs/DATABASE_PERSISTENCE.md)
- [Tools Reference](docs/TOOLS_REFERENCE.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Conversation Memory Fix](CONVERSATION_MEMORY_FIX.md)

## Development

### Adding a New Tool
1. Extend `BaseTool` in `src/agent/tools/`
2. Implement `execute()` method
3. Register in tool registry
4. See [docs/TOOLS_REFERENCE.md](docs/TOOLS_REFERENCE.md)

### Adding a New Agent Phase
1. Update `AgentState` in `src/agent/agent_state.py`
2. Add phase method to `AgentExecutorV3`
3. Update state graph edges

### Enabling Observability
```bash
ENABLE_OBSERVABILITY=true
OTEL_EXPORTER_TYPE=otlp
OTEL_EXPORTER_ENDPOINT=http://localhost:4317
```

## Troubleshooting

### Conversation Memory Lost
- Ensure `USE_CHECKPOINTS=true` in `.env`
- Verify PostgreSQL connection
- See [CONVERSATION_MEMORY_FIX.md](CONVERSATION_MEMORY_FIX.md)

### Vector Store Issues
- Check if `data/vector_store/` exists
- Re-run `reindex_documents.py`
- Verify embeddings model is downloaded

### Agent Not Using Tools
- Check tool registration in startup
- Verify tool descriptions are clear
- Enable `AGENT_VERBOSE=true` for debugging

## Performance Considerations

- **Embedding Generation**: Cached after first load (~2GB memory)
- **Vector Search**: FAISS is fast for <100k docs (upgrade to Pinecone for more)
- **LLM Latency**: Groq is fastest (~500ms), Gemini ~1-2s
- **Checkpoint Save**: ~50ms per save to PostgreSQL

## Security

- API keys in `.env` (never commit)
- Code execution disabled by default
- File operations sandboxed to `data/workspace/`
- Policy engine for content filtering

## Future Enhancements

- [ ] Multi-modal document support (images, tables)
- [ ] Advanced query routing (semantic similarity)
- [ ] Tool composition (chain multiple tools)
- [ ] Real-time streaming responses
- [ ] Multi-agent collaboration
