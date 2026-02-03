# RAG Chatbot

A powerful Retrieval-Augmented Generation (RAG) chatbot powered by Groq API, HuggingFace embeddings, and Streamlit UI.

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/Groq-API-orange?style=for-the-badge)](https://groq.com)

## Features

### Core RAG Features
- **Ultra-Fast LLM**: Powered by Groq API with Llama 3.3 70B (10-100x faster than traditional APIs)
- **Free Local Embeddings**: HuggingFace sentence-transformers (no API costs)
- **Modern Web UI**: Streamlit-based chat interface with document upload
- **Document Upload**: Support for PDF, TXT, and MD files
- **Source Attribution**: View retrieved context and sources for each answer
- **Configurable Settings**: Adjust temperature, top-k results, and chunking parameters
- **FAISS Vector Store**: Fast similarity search with local caching

### 🆕 Phase 3: Agent Features
- **🧠 Memory System**: Conversation memory + episodic memory across sessions
- **🔍 Multi-Tool Agent**: 7 specialized tools with intelligent routing
- **📊 Self-Reflection**: Agent evaluates its own decisions and learns from mistakes
- **🎯 Intelligent Routing**: Automatically selects the best tool for each query
- **📈 Performance Tracking**: Success rates, tool rankings, and quality metrics
- **💡 Context-Aware**: Remembers conversation history and builds on previous interactions

### 🌟 Phase 4: Web Agent & Document Upload (NEW!)
- **🌐 Autonomous Web Browsing**: Visit websites and extract clean content
- **📄 Article Extraction**: Get main content without ads/navigation/clutter
- **🔗 Multi-Source Synthesis**: Research across multiple URLs with proper citations
- **⚡ JavaScript Support**: Handle modern dynamic websites via Playwright
- **📊 Structured Summaries**: Markdown output with proper source attribution
- **🔄 Auto-Chaining**: Automatically chains web_search → web_agent for seamless research
- **📤 Document Upload**: Upload PDF, DOCX, TXT, MD files directly in UI with auto-indexing
- **🌐 URL Content Indexing**: Paste any URL to fetch, extract, and index web content directly
- **🗂️ Multi-Format Support**: Parse and index documents in multiple formats

## 🎉 What's New

### Latest Updates (Phase 4)

**🌐 Web Agent Tool** (Feb 2026)
- Autonomous web browsing with Playwright
- Clean content extraction from any website
- Multi-source synthesis with proper citations
- Auto-chaining: Ask for "latest news" and agent automatically searches → extracts → summarizes

**📤 Document Upload** (Feb 2026)
- Upload PDF, DOCX, TXT, MD files directly in UI
- Automatic parsing and indexing
- Multi-format support with unified loader
- No manual file copying needed

**🌐 URL Content Indexing** (Feb 2026)
- Paste any URL in the sidebar to fetch and index its content
- Automatically extracts clean article content using web agent
- Saves content to vector store for future queries
- Perfect for adding blog posts, documentation, or research articles to your knowledge base

**🔄 Intelligent Auto-Chaining** (Feb 2026)
- Agent automatically chains tools when needed
- Example: "Tell me latest AI news" → web_search (finds URLs) → web_agent (extracts content)
- Seamless user experience with no manual tool selection

**🛠️ Tool Improvements** (Feb 2026)
- Enhanced tool descriptions for better LLM routing
- Improved error handling across all tools
- Better tool selection accuracy
- Performance metrics and tracking

See [PHASE4_WEBAGENT.md](PHASE4_WEBAGENT.md) for detailed documentation.

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/ar-aishwaryanand-glitch/rag-chatbot.git
cd rag-chatbot
```

### 2. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers (for web agent)
playwright install chromium
```

**Note**: If you encounter certificate issues during Playwright installation:
```bash
export NODE_TLS_REJECT_UNAUTHORIZED=0
playwright install chromium
```

### 3. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Get your free API key from https://console.groq.com
GROQ_API_KEY=your_groq_api_key_here

# LLM Configuration
LLM_PROVIDER=groq
GROQ_MODEL=llama-3.3-70b-versatile

# Embedding Configuration (free local embeddings)
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### 4. Choose Your Interface

#### Option A: Basic RAG UI (Simple Document Q&A)

```bash
streamlit run run_ui.py
```

Or use launcher scripts:
```bash
./launch_ui.sh           # Mac/Linux
launch_ui.bat            # Windows
```

#### Option B: 🆕 **Agent UI with Phase 3 Features** (Recommended)

Enhanced interface with memory, self-reflection, and multi-tool capabilities:

```bash
streamlit run run_agent_ui.py
```

Or use launcher scripts:
```bash
./launch_agent_ui.sh     # Mac/Linux
launch_agent_ui.bat      # Windows
```

**New in Agent UI:**
- 🧠 Memory system (remembers conversations)
- 🔍 **7 specialized tools:**
  1. **document_search** - Search through uploaded documents (RAG)
  2. **web_search** - Quick web search with DuckDuckGo (returns links)
  3. **web_agent** - Visit URLs and extract full content with citations
  4. **calculator** - Perform mathematical calculations
  5. **python_executor** - Execute Python code safely
  6. **file_operations** - File system operations (list, read, write)
  7. **document_manager** - Manage uploaded documents
- 🌐 **Autonomous web browsing** - visits URLs and extracts content
- 🔄 **Auto-chaining** - automatically chains web_search → web_agent
- 📤 **Document upload** - upload PDF, DOCX, TXT, MD files with auto-indexing
- 🌐 **URL content indexing** - paste URLs to fetch and index web content
- 📊 Self-reflection and learning
- 🎯 Intelligent tool routing
- 📈 Performance tracking

See [Agent UI Guide](AGENT_UI_GUIDE.md) for detailed features.

The app will open at [http://localhost:8501](http://localhost:8501)

## Usage

### Two Interfaces Available

#### Basic RAG UI (`run_ui.py`)
- Simple document Q&A interface
- Best for: Quick document queries, simple RAG usage
- Features: Document search only

#### 🆕 Agent UI (`run_agent_ui.py`) - **Recommended**
- Intelligent multi-tool agent with memory and web browsing
- Best for: Complex queries, multi-turn conversations, web research, document management
- Features: 7 tools + memory + self-reflection + web agent + document upload

### Agent UI Usage

1. **Upload documents** (optional) - Upload PDF, DOCX, TXT, or MD files in the sidebar
2. **Add web content** (optional) - Paste URLs to fetch and index web content directly
3. **Start a conversation** - The agent will remember context
4. **Ask anything:**
   - **Document questions**: "What is RAG?" or "Summarize the uploaded document"
   - **Web research (latest info)**: "Tell me the latest AI news" (auto-chains search → extract)
   - **Direct URL extraction**: "Visit https://openai.com/research and extract the main content"
   - **Multi-source research**: "Research AI safety from OpenAI, Anthropic, and DeepMind websites"
   - **Calculations**: "Calculate 15% of $2500"
   - **Code execution**: "Write and run Python code to sort a list"
   - **File operations**: "List files in current directory"
5. **Enable/Disable features** in sidebar:
   - Memory (conversation + episodic)
   - Self-Reflection (learning & improvement)
6. **View insights:**
   - Agent reasoning (tool selection)
   - Memory context
   - Performance stats
   - Web agent extraction results

See [Agent UI Guide](AGENT_UI_GUIDE.md) for comprehensive usage instructions.

### Basic UI Usage

1. Select **Sample Documents** mode to try with example documents
2. Ask questions like:
   - "What is Python?"
   - "Explain the API documentation"
   - "What are the company policies?"

### Upload Custom Documents

#### In Agent UI (Recommended - Easier!)
1. Click **📁 Upload Documents** in the sidebar
2. Select files (PDF, DOCX, TXT, MD) - multiple files supported
3. Click **📤 Process & Index**
4. Files are automatically saved and indexed - ready to query!

#### In Basic UI
1. Switch to **Custom Documents** mode in the sidebar
2. Upload your documents (PDF, TXT, MD)
3. Click **Process Uploads**
4. Click **Rebuild Vector Store**
5. Start asking questions about your documents

### Add Content from URLs

In Agent UI (Custom Documents mode):
1. Find the **🌐 Add from URL** section in the sidebar
2. Paste any URL (e.g., `https://example.com/article`)
3. Click **✅ Fetch & Index**
4. The agent will:
   - Fetch the web page using the web agent tool
   - Extract clean article content (no ads/navigation)
   - Save it to your document collection
   - Mark it for indexing
5. Click **🔄 Rebuild** to index the new content
6. Query the web content like any other document!

**Perfect for:**
- Adding blog posts to your knowledge base
- Indexing documentation pages
- Saving research articles
- Building a personal knowledge repository from web sources

### Settings

Adjust RAG parameters in the sidebar:
- **Temperature** (0.0-1.0): Controls response creativity
- **Top-K Results** (1-10): Number of context chunks to retrieve
- **Chunk Size** (400-1200): Text chunk size for processing

## Project Structure

```
rag-chatbot/
├── src/
│   ├── main.py              # CLI interface
│   ├── rag_chain.py         # RAG pipeline
│   ├── config.py            # Configuration management
│   ├── embeddings.py        # Embedding generation
│   ├── vector_store.py      # FAISS vector store
│   ├── document_loader.py   # Multi-format document processing (TXT, MD, PDF, DOCX)
│   ├── agent/               # Phase 3 & 4: Agent system
│   │   ├── agent_executor_v3.py  # Multi-tool agent with auto-chaining
│   │   ├── memory.py        # Conversation & episodic memory
│   │   ├── self_reflection.py    # Agent self-reflection
│   │   └── tools/           # Agent tools
│   │       ├── base_tool.py      # Base tool class
│   │       ├── rag_tool.py       # Document search
│   │       ├── web_search_tool.py # Web search (DuckDuckGo)
│   │       ├── web_agent_tool.py # Autonomous web browsing (Phase 4)
│   │       ├── calculator_tool.py
│   │       ├── code_executor_tool.py
│   │       ├── file_ops_tool.py
│   │       └── doc_management_tool.py
│   └── ui/                  # Streamlit UI modules
│       ├── streamlit_app.py      # Basic RAG UI
│       ├── streamlit_app_agent.py # Agent UI (Phase 3 & 4)
│       ├── components.py
│       ├── state_manager.py
│       └── document_handler.py
├── data/
│   ├── documents/           # Sample & uploaded documents
│   ├── vector_store/        # FAISS index (generated)
│   └── episodic_memory/     # Agent memory (generated)
├── run_ui.py                # Basic RAG UI launcher
├── run_agent_ui.py          # Agent UI launcher (recommended)
├── test_web_agent.py        # Web agent test suite
├── requirements.txt         # Python dependencies
└── .env                     # Environment variables (create this)
```

## CLI Usage

For command-line usage without the UI:

```bash
# Use sample documents
python -m src.main

# Use your custom documents
python -m src.main --use-documents
```

## Configuration

### LLM Models

Change the model in `.env`:

```bash
# Fast, balanced (default)
GROQ_MODEL=llama-3.3-70b-versatile

# Smaller, faster
GROQ_MODEL=llama-3.1-8b-instant

# Mixtral (multilingual)
GROQ_MODEL=mixtral-8x7b-32768

# High quality
GROQ_MODEL=llama-3.1-70b-versatile
```

See all models: [Groq Models](https://console.groq.com/docs/models)

### Embedding Models

Try different HuggingFace models:

```bash
# Default (fast, good quality)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Larger, more accurate
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2

# Multilingual
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

## Performance

- **LLM Inference**: 10-100x faster than traditional APIs (via Groq)
- **Embeddings**: 100% local, no API calls after first run
- **Vector Search**: FAISS-based, optimized for speed
- **Caching**: Vector store cached locally for instant retrieval

## Documentation

### User Guides
- [Agent UI Guide](AGENT_UI_GUIDE.md) - **NEW!** Phase 3 agent features and usage
- [UI Guide](UI_GUIDE.md) - Basic UI feature guide
- [Adding Documents](ADDING_YOUR_DOCUMENTS.md) - Document processing guide

### Technical Documentation
- [Phase 4: Web Agent](PHASE4_WEBAGENT.md) - **NEW!** Autonomous web browsing
- [Phase 3 Complete](PHASE3_COMPLETE.md) - Phase 3 implementation summary
- [Phase 3 Design](PHASE3_DESIGN.md) - Phase 3 architecture and design
- [Project Overview](PROJECT_OVERVIEW.md) - Technical architecture
- [Groq Migration](GROQ_MIGRATION_SUMMARY.md) - Groq API setup details

## Deployment

### Streamlit Cloud

1. Push to GitHub (already done!)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click **New app**
5. Select your repository: `ar-aishwaryanand-glitch/rag-chatbot`
6. Set main file: `run_ui.py`
7. Add secrets in **Advanced settings**:
   ```toml
   GROQ_API_KEY = "your_groq_api_key"
   LLM_PROVIDER = "groq"
   GROQ_MODEL = "llama-3.3-70b-versatile"
   EMBEDDING_PROVIDER = "huggingface"
   EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
   ```
8. Click **Deploy**

Your app will be live at: `https://<your-app-name>.streamlit.app`

## Testing

### Test Web Agent

Verify the web agent is working correctly:

```bash
python test_web_agent.py
```

This will test:
- Single URL extraction
- Multiple URL synthesis
- Error handling
- Dependency availability

Expected output: All tests pass (100%)

## Requirements

- Python 3.11+
- 4GB RAM minimum (for embeddings)
- Internet connection (for Groq API and first-run model downloads)
- Playwright browsers (for web agent) - installed via `playwright install chromium`

## License

MIT License - feel free to use and modify for your projects!

## Credits

Built with:
- [Groq](https://groq.com) - Ultra-fast LLM inference
- [LangChain](https://python.langchain.com) - RAG framework
- [Streamlit](https://streamlit.io) - Web UI framework
- [HuggingFace](https://huggingface.co) - Embedding models
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search

Developed with assistance from [Claude Code](https://claude.ai/code)

## Support

For issues or questions:
- Open an issue on GitHub
- Check the documentation files in the repo
- Review [Groq Documentation](https://console.groq.com/docs)

---

**Happy chatting!** 🚀
