# RAG Agent System - Requirements Specification

**Version:** 1.0
**Date:** February 2026
**System:** Agentic RAG with Multi-Tool Support

---

## 1. System Overview

The RAG Agent System is an intelligent question-answering application that combines Retrieval-Augmented Generation (RAG) with agentic capabilities. The system allows users to upload documents, ask questions, and receive AI-generated answers grounded in the uploaded content. Additionally, the system includes agent tools for web search, calculations, code execution, and web browsing.

### 1.1 Key Components
- Document upload and processing (PDF, TXT, MD, DOCX)
- Vector store for semantic search (FAISS local, Pinecone cloud)
- LLM integration (Groq, Google Gemini)
- Multi-tool agent system with LangGraph orchestration
- PostgreSQL session and memory storage
- Streamlit web UI
- Auto-indexing with change detection

---

## 2. Functional Requirements

### FR-1: Document Management

**FR-1.1 Document Upload**
- **Description:** Users shall be able to upload documents in multiple formats
- **Supported Formats:** PDF, TXT, MD, DOCX
- **Max File Size:** 200MB per file
- **Acceptance Criteria:**
  - System accepts files with extensions: .pdf, .txt, .md, .docx
  - System rejects unsupported file formats with clear error message
  - System displays upload progress indicator
  - System validates file size before processing

**FR-1.2 Document Processing**
- **Description:** System shall process uploaded documents into chunks for indexing
- **Chunking Strategy:**
  - Chunk size: 1000 characters
  - Chunk overlap: 200 characters
  - Recursive text splitting by paragraph, sentence, word
- **Acceptance Criteria:**
  - PDF files are parsed correctly with text extraction
  - Multi-page PDFs maintain source page metadata
  - Text files preserve formatting where possible
  - Each chunk contains source metadata (filename, page, file type)

**FR-1.3 Auto-Indexing**
- **Description:** System shall automatically detect and index new or modified documents
- **Change Detection:** MD5 hash-based file comparison
- **Acceptance Criteria:**
  - New files are automatically indexed on app startup
  - Modified files trigger full re-indexing
  - Deleted files are removed from index
  - System skips indexing if no changes detected
  - Indexing metadata stored in `.index_metadata.json`

### FR-2: Vector Store and Embeddings

**FR-2.1 Embedding Generation**
- **Description:** System shall generate embeddings for document chunks
- **Model:** HuggingFace sentence-transformers (all-MiniLM-L6-v2)
- **Embedding Dimension:** 384
- **Acceptance Criteria:**
  - Each document chunk generates a 384-dimensional embedding
  - Embeddings are normalized for cosine similarity
  - Batch processing for multiple chunks

**FR-2.2 Vector Store Options**
- **Description:** System shall support multiple vector store backends
- **Options:**
  - FAISS (local, file-based)
  - Pinecone (cloud, production)
- **Acceptance Criteria:**
  - User can switch between FAISS and Pinecone via config
  - FAISS index saved to `data/vector_store/`
  - Pinecone uses namespace-based organization
  - Both stores support similarity search with scores

**FR-2.3 Similarity Search**
- **Description:** System shall retrieve relevant document chunks for queries
- **Search Parameters:**
  - Top-K results (default: 5)
  - Similarity metric: Cosine similarity
- **Acceptance Criteria:**
  - Search returns top-K most similar chunks
  - Each result includes similarity score (0-1 range)
  - Results include source metadata
  - Search latency < 500ms for 10K documents

### FR-3: RAG Pipeline

**FR-3.1 Question Answering**
- **Description:** System shall answer user questions using retrieved context
- **Pipeline Steps:**
  1. User submits question
  2. System generates query embedding
  3. System retrieves top-K relevant chunks
  4. System formats chunks as context
  5. System prompts LLM with context + question
  6. System returns generated answer with sources
- **Acceptance Criteria:**
  - Answer grounded in retrieved context only
  - System cites source documents
  - System responds "insufficient information" if no relevant context found
  - Answer generation latency < 5 seconds

**FR-3.2 Context Formatting**
- **Description:** System shall format retrieved chunks for LLM consumption
- **Format:**
  ```
  [Source 1: filename.pdf (Topic: X)]
  <chunk content>
  ---
  [Source 2: document.txt (Topic: Y)]
  <chunk content>
  ```
- **Acceptance Criteria:**
  - Each source numbered sequentially
  - Source metadata clearly labeled
  - Chunks separated by visual delimiter

**FR-3.3 LLM Integration**
- **Description:** System shall support multiple LLM providers
- **Supported Providers:**
  - Groq (llama-3.3-70b-versatile)
  - Google Gemini (gemini-2.0-flash-exp)
- **Parameters:**
  - Temperature: 0.3 (configurable)
  - Max tokens: 2048 (configurable)
- **Acceptance Criteria:**
  - User can switch LLM via environment config
  - API keys loaded from .env file
  - System handles API errors gracefully
  - System retries on transient failures (max 3 attempts)

### FR-4: Agent System

**FR-4.1 Multi-Tool Support**
- **Description:** System shall provide agents with multiple tools
- **Available Tools:**
  1. **RAG Search Tool** - Search indexed documents
  2. **Web Search Tool** - DuckDuckGo web search
  3. **Calculator Tool** - Mathematical calculations
  4. **Code Executor Tool** - Execute Python code in sandbox
  5. **Web Agent Tool** - Browse websites with Playwright
  6. **News Search Tool** - NewsAPI and RSS feed search
- **Acceptance Criteria:**
  - Each tool has clear description and usage instructions
  - Tools return structured outputs
  - Tools handle errors without crashing agent

**FR-4.2 Agent Orchestration**
- **Description:** System shall use LangGraph for agent workflow
- **State Management:**
  - Messages history
  - Tool call tracking
  - Iteration limits (max 10)
- **Acceptance Criteria:**
  - Agent can chain multiple tool calls
  - Agent stops after task completion or iteration limit
  - Agent state persisted in PostgreSQL checkpoints
  - Agent handles tool errors and retries

**FR-4.3 Tool Selection**
- **Description:** Agent shall intelligently select appropriate tools
- **Selection Logic:**
  - RAG tool for questions about uploaded documents
  - Web search for current events/external information
  - Calculator for math problems
  - Code executor for data processing tasks
  - Web agent for accessing specific websites
- **Acceptance Criteria:**
  - Agent uses RAG tool when query relates to uploaded docs
  - Agent uses web search for queries about current events
  - Agent explains tool selection rationale
  - Agent can use multiple tools in sequence

### FR-5: Session Management

**FR-5.1 Session Creation**
- **Description:** System shall create and manage user sessions
- **Session Data:**
  - Unique session_id
  - User identifier (optional)
  - Session title
  - Created/updated timestamps
  - Active status flag
- **Acceptance Criteria:**
  - New session created on app start
  - Session ID is UUID format
  - Session persisted to PostgreSQL

**FR-5.2 Conversation History**
- **Description:** System shall store all conversation messages
- **Message Types:**
  - User messages
  - Assistant responses
  - System messages
  - Tool calls and results
- **Acceptance Criteria:**
  - All messages stored with timestamps
  - Messages linked to session_id
  - Tool calls stored as JSON metadata
  - Sources stored with assistant messages

**FR-5.3 Episodic Memory**
- **Description:** System shall extract and store important conversation facts
- **Memory Types:**
  - Conversation summaries
  - Extracted facts
  - User preferences
  - Completed tasks
- **Importance Scoring:** 0.0 to 1.0
- **Acceptance Criteria:**
  - High-importance memories stored with embeddings
  - Memories retrievable via similarity search
  - Memories linked to sessions

### FR-6: User Interface

**FR-6.1 Streamlit Web App**
- **Description:** System shall provide web-based UI
- **Pages:**
  - Main chat interface
  - Document upload sidebar
  - Session history
  - Settings panel
- **Acceptance Criteria:**
  - Responsive design for desktop and tablet
  - Real-time chat updates
  - File upload with drag-and-drop
  - Session switching without page reload

**FR-6.2 Chat Interface**
- **Description:** Users shall interact via chat interface
- **Features:**
  - Message input box with send button
  - Message history display
  - Source citations expandable
  - Streaming responses (optional)
- **Acceptance Criteria:**
  - Messages display with role labels (User/Assistant)
  - Timestamps shown for each message
  - Sources displayed as expandable sections
  - Input box clears after send

**FR-6.3 Settings Panel**
- **Description:** Users shall configure system settings
- **Configurable Options:**
  - LLM provider (Groq/Google)
  - Top-K results (1-10)
  - Temperature (0.0-1.0)
  - Enable/disable specific tools
- **Acceptance Criteria:**
  - Settings persist across sessions
  - Changes apply immediately
  - Invalid values rejected with error message

---

## 3. Non-Functional Requirements

### NFR-1: Performance

**NFR-1.1 Response Time**
- Document upload processing: < 30 seconds for 10MB PDF
- Vector search: < 500ms for 10K documents
- RAG answer generation: < 5 seconds
- Agent task completion: < 30 seconds (simple queries)

**NFR-1.2 Scalability**
- Support up to 100,000 document chunks in vector store
- Support up to 1,000 concurrent sessions
- Database handles 10,000 messages per day

**NFR-1.3 Resource Usage**
- Memory usage: < 2GB for local FAISS store
- Disk space: < 500MB for 1,000 documents
- CPU usage: < 50% during idle state

### NFR-2: Reliability

**NFR-2.1 Availability**
- System uptime: 99% (excluding maintenance)
- Graceful degradation if external APIs unavailable
- Auto-recovery from transient errors

**NFR-2.2 Data Integrity**
- No data loss during indexing
- Atomic database transactions
- Vector store consistency checks

### NFR-3: Security

**NFR-3.1 API Key Management**
- API keys stored in .env file (not committed)
- Keys loaded via environment variables
- No keys logged or displayed in UI

**NFR-3.2 Code Execution Sandbox**
- Restricted Python execution environment
- No access to file system or network
- Timeout limits (30 seconds)
- Whitelist of allowed modules

**NFR-3.3 Input Validation**
- File upload validation (type, size, content)
- SQL injection prevention (parameterized queries)
- XSS prevention (input sanitization)

### NFR-4: Maintainability

**NFR-4.1 Code Quality**
- Type hints for all functions
- Docstrings for all classes and methods
- Configuration centralized in config.py
- Error handling with specific exceptions

**NFR-4.2 Monitoring**
- OpenTelemetry instrumentation
- Metrics for all operations (retrieval, generation, tool usage)
- Tracing for RAG pipeline
- Logs for debugging

---

## 4. User Stories

### US-1: Document Upload and Query
**As a** user
**I want to** upload my research papers
**So that** I can ask questions about their content

**Acceptance Criteria:**
- User can upload PDF files
- System indexes the content
- User can ask questions and get answers with citations

### US-2: Multi-Document Context
**As a** researcher
**I want** answers that synthesize information from multiple documents
**So that** I can understand topics across different sources

**Acceptance Criteria:**
- System retrieves chunks from different documents
- Answer cites multiple sources
- Answer integrates information coherently

### US-3: Web Search Fallback
**As a** user
**I want** the system to search the web when documents don't have answers
**So that** I can get information beyond my uploaded files

**Acceptance Criteria:**
- System detects when no relevant docs found
- Agent automatically uses web search tool
- Answer distinguishes between doc sources and web sources

### US-4: Code Execution for Data Analysis
**As a** data analyst
**I want** to ask the system to perform calculations on data
**So that** I can get insights without writing code myself

**Acceptance Criteria:**
- User asks "calculate the average of [data]"
- Agent uses code executor tool
- Result displayed with explanation

### US-5: Session History
**As a** user
**I want** to see my previous conversations
**So that** I can continue where I left off

**Acceptance Criteria:**
- User can view list of past sessions
- User can load previous session
- Messages and context preserved

---

## 5. Technical Specifications

### 5.1 Technology Stack
- **Language:** Python 3.11+
- **LLM Providers:** Groq, Google Gemini
- **Embeddings:** HuggingFace sentence-transformers
- **Vector Stores:** FAISS, Pinecone
- **Agent Framework:** LangGraph, LangChain
- **Database:** PostgreSQL (Supabase)
- **UI Framework:** Streamlit
- **Observability:** OpenTelemetry

### 5.2 System Architecture
```
User Interface (Streamlit)
    ↓
Agent Executor (LangGraph)
    ↓
Tools: [RAG | Web Search | Calculator | Code Executor | Web Agent]
    ↓
RAG Chain: [Vector Store → Embeddings → LLM]
    ↓
Data Layer: [PostgreSQL Sessions | FAISS/Pinecone Index]
```

### 5.3 Data Models
- **Session:** session_id, user_id, title, timestamps, metadata
- **Message:** message_id, session_id, role, content, timestamp, tool_calls, sources
- **EpisodicMemory:** memory_id, session_id, memory_type, content, importance, embedding
- **SessionStats:** total_messages, total_tokens, tools_used, success_rate

### 5.4 Configuration
- Environment variables in `.env`
- System config in `src/config.py`
- Default values with override capability
- Runtime configuration via UI settings

---

## 6. Assumptions and Constraints

### Assumptions
- Users have valid API keys for Groq/Google
- Documents are in English (or supported language)
- Users have stable internet connection
- PostgreSQL database accessible

### Constraints
- FAISS is in-memory (requires reload on restart)
- Free tier API rate limits apply
- Local embeddings require ~2GB disk space
- Playwright requires browser binaries

---

## 7. Future Enhancements

- Multi-user support with authentication
- Document version control
- Advanced filtering (by date, source, topic)
- Custom embedding models
- Streaming responses
- Mobile app
- API endpoint for external integrations
- Support for images and tables in PDFs
- Multi-language support
