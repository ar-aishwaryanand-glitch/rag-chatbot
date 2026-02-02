# RAG Chatbot

A powerful Retrieval-Augmented Generation (RAG) chatbot powered by Groq API, HuggingFace embeddings, and Streamlit UI.

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/Groq-API-orange?style=for-the-badge)](https://groq.com)

## Features

- **Ultra-Fast LLM**: Powered by Groq API with Llama 3.3 70B (10-100x faster than traditional APIs)
- **Free Local Embeddings**: HuggingFace sentence-transformers (no API costs)
- **Modern Web UI**: Streamlit-based chat interface with document upload
- **Document Upload**: Support for PDF, TXT, and MD files
- **Source Attribution**: View retrieved context and sources for each answer
- **Configurable Settings**: Adjust temperature, top-k results, and chunking parameters
- **FAISS Vector Store**: Fast similarity search with local caching

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/ar-aishwaryanand-glitch/rag-chatbot.git
cd rag-chatbot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
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

### 4. Launch the UI

```bash
streamlit run run_ui.py
```

Or use the launcher scripts:

**Mac/Linux:**
```bash
./launch_ui.sh
```

**Windows:**
```bash
launch_ui.bat
```

The app will open at [http://localhost:8501](http://localhost:8501)

## Usage

### Chat Interface

1. Select **Sample Documents** mode to try with example documents
2. Ask questions like:
   - "What is Python?"
   - "Explain the API documentation"
   - "What are the company policies?"

### Upload Custom Documents

1. Switch to **Custom Documents** mode in the sidebar
2. Upload your documents (PDF, TXT, MD)
3. Click **Process Uploads**
4. Click **Rebuild Vector Store**
5. Start asking questions about your documents

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
│   ├── document_loader.py   # Document processing
│   └── ui/                  # Streamlit UI module
│       ├── streamlit_app.py
│       ├── components.py
│       ├── state_manager.py
│       └── document_handler.py
├── data/
│   ├── documents/           # Sample documents
│   └── uploaded/            # User uploads
├── run_ui.py                # Streamlit launcher
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

- [UI Guide](UI_GUIDE.md) - Comprehensive UI feature guide
- [Project Overview](PROJECT_OVERVIEW.md) - Technical architecture
- [Groq Migration](GROQ_MIGRATION_SUMMARY.md) - Groq API setup details
- [Adding Documents](ADDING_YOUR_DOCUMENTS.md) - Document processing guide

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

## Requirements

- Python 3.11+
- 4GB RAM minimum (for embeddings)
- Internet connection (for Groq API and first-run model downloads)

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
