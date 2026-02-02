# RAG Agent POC - Project Overview

## Quick Start

### Option 1: Streamlit Web UI (Recommended)
```bash
# Launch modern web interface
streamlit run run_ui.py

# Opens at http://localhost:8501
```

**Features:**
- 💬 ChatGPT-style interface
- 📤 Document upload (PDF/TXT/MD)
- 📖 Source viewer
- ⚙️ Live settings adjustment

See [UI_GUIDE.md](UI_GUIDE.md) for complete UI documentation.

### Option 2: Command Line Interface (CLI)

**With Sample Data (AI/ML Topics)**
```bash
python -m src.main
```

**With Your Own Documents**
```bash
# 1. Add documents to data/documents/
# 2. Run:
python -m src.main --use-documents
```

## Project Structure

```
rag-agent-poc/
├── src/                              # Source code
│   ├── __init__.py                   # Package marker
│   ├── config.py                     # Configuration & environment variables
│   ├── data_loader.py                # Sample documents (AI/ML topics)
│   ├── document_loader.py            # Load user documents from data/documents/
│   ├── embeddings.py                 # Text chunking & embedding generation
│   ├── vector_store.py               # FAISS vector database with rate limiting
│   ├── rag_chain.py                  # RAG pipeline (retrieve + generate)
│   ├── main.py                       # CLI interface & entry point
│   │
│   └── ui/                           # ⭐ Streamlit Web UI
│       ├── __init__.py               # UI package marker
│       ├── streamlit_app.py          # Main Streamlit application
│       ├── components.py             # Reusable UI widgets
│       ├── state_manager.py          # Session state & caching
│       └── document_handler.py       # File upload handling
│
├── data/                             # Data directory
│   ├── documents/                    # ← PUT YOUR DOCUMENTS HERE
│   │   ├── README.md                 # Guidelines for adding documents
│   │   ├── example-company-policy.txt     # Example document
│   │   └── product-api-docs.md       # Example document
│   ├── uploaded/                     # ⭐ Streamlit UI uploads (temporary)
│   └── vector_store/                 # Cached FAISS index (auto-generated)
│
├── venv/                             # Python virtual environment
│
├── .env                              # API keys (KEEP SECRET, not in git)
├── .env.example                      # Template for .env file
├── requirements.txt                  # Python dependencies
│
├── run_ui.py                         # ⭐ Streamlit UI launcher
│
├── COMPLETE_RAG_TUTORIAL.txt         # ⭐ Main tutorial (comprehensive)
├── ADDING_YOUR_DOCUMENTS.md          # Guide for adding your documents
├── UI_GUIDE.md                       # ⭐ Streamlit UI guide
├── PROJECT_OVERVIEW.md               # This file
└── RAG_IMPLEMENTATION_GUIDE.txt      # (Superseded, see COMPLETE_RAG_TUTORIAL.txt)
```

## Documentation Guide

### 🌐 Streamlit Web UI
**[UI_GUIDE.md](UI_GUIDE.md)** - Complete UI documentation
- Quick start and installation
- Interface layout and features
- Document modes (Sample vs Custom)
- File upload and management
- Chat interface usage
- Settings panel configuration
- Source viewer
- Troubleshooting UI issues

### 📘 RAG System Tutorial
**[COMPLETE_RAG_TUTORIAL.txt](COMPLETE_RAG_TUTORIAL.txt)** - Comprehensive tutorial
- What is RAG and why use it
- System architecture explained
- Component-by-component implementation
- Rate limiting strategy
- Complete system flow
- Extending the system
- Troubleshooting & best practices

### 📄 Adding Your Documents
**[ADDING_YOUR_DOCUMENTS.md](ADDING_YOUR_DOCUMENTS.md)** - Quick guide for custom documents
- How to add your own documents
- Supported file types
- Command reference
- Example usage
- Troubleshooting

### 📁 Document Guidelines
**[data/documents/README.md](data/documents/README.md)** - Detailed document guidelines
- File naming conventions
- Content guidelines
- Document organization
- What makes good documents for RAG

## Command Reference

### Streamlit Web UI Commands
```bash
# Launch web interface (default port 8501)
streamlit run run_ui.py

# Launch on custom port
streamlit run run_ui.py --server.port 8502

# Launch accessible from network
streamlit run run_ui.py --server.address 0.0.0.0

# Launch with dark theme
streamlit run run_ui.py --theme.base dark
```

### CLI Commands
```bash
# Interactive mode with sample AI/ML data
python -m src.main

# Use your own documents from data/documents/
python -m src.main --use-documents

# Rebuild vector store (when documents change)
python -m src.main --rebuild

# Rebuild with your documents
python -m src.main --use-documents --rebuild

# Run demo questions
python -m src.main --demo
```

### When to Use Each Mode

**Default (no flags):**
- Uses 5 sample documents about AI/ML topics
- Good for testing the system
- Good for learning how RAG works

**--use-documents:**
- Loads documents from data/documents/
- Use this for your real use case
- Requires documents in data/documents/

**--rebuild:**
- Forces recreation of vector store
- Use when you add/modify/delete documents
- Use when changing embedding model
- NOT needed for just asking questions

**--demo:**
- Runs 3 predefined questions
- Shows system capabilities
- Good for demos and presentations

## Key Features

### 1. Rate Limiting
- Processes documents in small batches (3 at a time)
- 2-second delays between batches
- Stays under Google's free tier (1,500 requests/day)
- Smart caching to avoid repeated API calls

### 2. Vector Store Caching
- Saves FAISS index to disk after creation
- Future runs load from cache (no API calls!)
- Only rebuilds when you explicitly request it

### 3. Document Flexibility
- Built-in sample documents (AI/ML topics)
- Easy to add your own documents
- Automatic detection of .txt and .md files
- Recursive directory scanning

### 4. Source Attribution
- Every answer cites its sources
- Shows which documents were used
- Preview of retrieved content
- Full transparency

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python 3.14 | Implementation |
| LLM | Google Gemini (gemini-2.0-flash-exp) | Answer generation |
| Embeddings | Google embedding-001 | Convert text to vectors |
| Vector DB | FAISS | Fast similarity search |
| Framework | LangChain | Orchestration |
| CLI | Python argparse | Command line interface |

## Configuration

### Environment Variables (.env file)
```bash
# Required
GOOGLE_API_KEY=your_api_key_here

# Optional (defaults provided)
EMBEDDING_MODEL=models/embedding-001
CHUNK_SIZE=800
CHUNK_OVERLAP=100
```

### Config Constants (src/config.py)
- `LLM_MODEL`: gemini-2.0-flash-exp
- `LLM_TEMPERATURE`: 0.7 (balanced creativity)
- `LLM_MAX_TOKENS`: 1024 (response length)
- `TOP_K_RESULTS`: 3 (chunks to retrieve)
- `CHUNK_SIZE`: 800 chars (document chunk size)
- `CHUNK_OVERLAP`: 100 chars (context preservation)

## Workflow

### First Time Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env`
3. Add Google API key to `.env`
4. Test with sample data: `python -m src.main`

### Using Your Own Documents
1. Add documents to `data/documents/`
2. Run: `python -m src.main --use-documents`
3. Wait for indexing (happens once)
4. Ask questions about your documents

### Daily Usage
```bash
# Start the system (loads from cache, fast!)
python -m src.main --use-documents

# Ask questions interactively
❓ Your question: What is our refund policy?

# System retrieves relevant chunks and generates answer
```

### Updating Documents
```bash
# 1. Add/modify/delete documents in data/documents/
# 2. Rebuild:
python -m src.main --use-documents --rebuild
```

## API Usage & Costs

### Free Tier Limits (Google AI Studio)
- Embedding API: 1,500 requests/day
- LLM API: Generous free tier

### Typical Usage
**Initial Setup (5 documents):**
- Embedding calls: 2 (batched)
- Time: ~4 seconds
- Cost: FREE

**Each Question:**
- Embedding calls: 1 (query embedding)
- LLM calls: 1 (answer generation)
- Cost: FREE (within limits)

**Subsequent Runs:**
- Embedding calls: 0 (loads from cache!)
- Only LLM calls for answering questions

## Common Tasks

### Task: Add New Documents
```bash
# 1. Add files
cp new-doc.txt data/documents/

# 2. Rebuild
python -m src.main --use-documents --rebuild
```

### Task: Test Retrieval Quality
```bash
# 1. Start system
python -m src.main --use-documents

# 2. Ask question
❓ Your question: [your question]

# 3. Check "📖 Sources Used" section
# Are the retrieved chunks relevant?
```

### Task: Adjust Retrieval Settings
Edit `src/config.py`:
```python
TOP_K_RESULTS = 5  # Retrieve more chunks
CHUNK_SIZE = 1000  # Larger chunks
```

Then rebuild:
```bash
python -m src.main --use-documents --rebuild
```

### Task: Change LLM Temperature
Edit `src/config.py`:
```python
LLM_TEMPERATURE = 0.3  # More deterministic
# or
LLM_TEMPERATURE = 0.9  # More creative
```

No rebuild needed! Just restart the system.

## Troubleshooting

### Issue: "API key not valid"
**Solution:** Check `.env` file has correct Google API key from https://aistudio.google.com/app/apikey

### Issue: "Quota exceeded"
**Solution:** Wait 24 hours for reset, or reduce documents, or use cached index (don't rebuild)

### Issue: "No documents found"
**Solution:** Ensure files are in `data/documents/` with `.txt` or `.md` extension

### Issue: "Poor retrieval quality"
**Solutions:**
- Check retrieved chunks (are they relevant?)
- Adjust `CHUNK_SIZE` and `TOP_K_RESULTS` in config
- Ensure documents are well-structured
- Try rebuilding index

### Issue: "Hallucinated answers"
**Solutions:**
- Strengthen prompt (already done in code)
- Lower temperature in config
- Check if retrieved chunks are relevant
- Ensure documents contain the needed information

## Getting Help

1. **Read the docs:**
   - [COMPLETE_RAG_TUTORIAL.txt](COMPLETE_RAG_TUTORIAL.txt) - Comprehensive guide
   - [ADDING_YOUR_DOCUMENTS.md](ADDING_YOUR_DOCUMENTS.md) - Document guide

2. **Check examples:**
   - Example documents in `data/documents/`
   - Sample questions in the tutorial

3. **Review code:**
   - All code is well-commented
   - Each component is explained in tutorial

## Next Steps

### For Learning:
1. ✅ Read [COMPLETE_RAG_TUTORIAL.txt](COMPLETE_RAG_TUTORIAL.txt)
2. ✅ Run with sample data: `python -m src.main`
3. ✅ Ask sample questions
4. ✅ Read the code with tutorial as reference

### For Building:
1. ✅ Add 2-3 of your documents to `data/documents/`
2. ✅ Run: `python -m src.main --use-documents`
3. ✅ Test with questions about your documents
4. ✅ Iterate: adjust settings, add more documents

### For Production:
1. ✅ Set up billing for higher API limits
2. ✅ Add authentication to API endpoints
3. ✅ Implement logging and monitoring
4. ✅ Add error handling and retry logic
5. ✅ Consider FastAPI or Streamlit for UI

## License & Credits

Created as a proof-of-concept RAG system using:
- Google Gemini LLM
- Google Embeddings
- FAISS (Facebook AI)
- LangChain Framework

For educational and commercial use.

## Version

**Current Version:** 1.0.0
**Last Updated:** February 2026
**Python Version:** 3.14+

---

**Happy Building! 🚀**

For questions about implementation, see the comprehensive tutorial.
For questions about adding documents, see the document guide.
For questions about specific components, see the inline code comments.
