# Streamlit UI Guide for RAG Agent

## Overview

The Streamlit UI provides a modern, web-based interface for the RAG (Retrieval-Augmented Generation) system. It offers a ChatGPT-style chat interface, document upload capabilities, source viewing, and runtime configuration adjustments.

## Quick Start

### Installation

1. **Install Streamlit** (if not already installed):
   ```bash
   pip install streamlit
   ```

2. **Verify installation**:
   ```bash
   streamlit --version
   ```

### Launch the UI

```bash
# From project root directory
streamlit run run_ui.py
```

The UI will open automatically in your default browser at [http://localhost:8501](http://localhost:8501)

### Custom Launch Options

```bash
# Run on custom port
streamlit run run_ui.py --server.port 8502

# Run on all network interfaces (accessible from other devices)
streamlit run run_ui.py --server.address 0.0.0.0

# Run with custom theme
streamlit run run_ui.py --theme.base dark
```

## Interface Layout

```
┌─────────────────────────────────────────────────────┐
│                   RAG Chat Assistant                │
├──────────────┬──────────────────────────────────────┤
│   SIDEBAR    │         MAIN CHAT AREA               │
│              │                                       │
│ Mode         │  💬 Chat with Your Documents         │
│ ○ Sample     │  ┌────────────────────────────────┐  │
│ ● Custom     │  │ Welcome Message                │  │
│              │  │ (when chat is empty)           │  │
│ Upload       │  └────────────────────────────────┘  │
│ [Browse]     │                                       │
│              │  ┌────────────────────────────────┐  │
│ Settings     │  │ 👤 User: What is Python?      │  │
│ Temp: ▮─────│  │ 🤖 AI: Python is a...         │  │
│ Top-K: ──▮── │  │    📖 View 3 sources ▼         │  │
│              │  └────────────────────────────────┘  │
│ Vector Store │                                       │
│ ✅ Init      │  ┌────────────────────────────────┐  │
│ [Rebuild]    │  │ Ask a question...              │  │
│ [Clear]      │  └────────────────────────────────┘  │
└──────────────┴──────────────────────────────────────┘
```

## Features

### 1. Document Modes

#### Sample Documents Mode
- Uses built-in sample documents about AI/ML topics
- 5 documents covering Python, ML, Deep Learning, NLP, and LLMs
- Great for testing and learning how RAG works
- No setup required

**To use:**
1. Select "📖 Sample Documents" in sidebar
2. Wait for initialization
3. Start asking questions!

**Example questions:**
- "What is Python used for?"
- "Explain the difference between supervised and unsupervised learning"
- "What is a neural network?"

#### Custom Documents Mode
- Uses your own documents from `data/documents/` or uploaded files
- Supports PDF, TXT, and MD file formats
- Allows file upload directly through the UI
- Combines persistent documents with uploaded files

**To use:**
1. Select "📁 Custom Documents" in sidebar
2. Option A: Place files in `data/documents/` directory
3. Option B: Upload files using the file uploader
4. Click "Rebuild" to index documents
5. Start asking questions about your documents!

### 2. File Upload

**Supported formats:**
- `.txt` - Plain text files
- `.md` - Markdown files
- `.pdf` - PDF documents (requires `pypdf` library)

**Upload process:**
1. Click "Choose files" in the Upload section
2. Select one or more files (max 10MB each)
3. Click "✅ Upload" button
4. Wait for processing
5. Click "🔄 Rebuild" to index uploaded documents

**File management:**
- View list of uploaded files with sizes
- Delete individual files with 🗑️ button
- Clear all uploads with "🗑️ Clear All Uploads" button

**Limitations:**
- Maximum file size: 10MB per file
- Uploaded files are session-based (cleared when you close the app)
- For persistent documents, use the `data/documents/` directory

### 3. Chat Interface

The chat interface provides a conversational experience similar to ChatGPT.

**Features:**
- Message history preserved during session
- User messages shown on right
- AI responses shown on left
- Source attribution for each answer
- Expandable source viewer
- Automatic scrolling to latest message

**How to use:**
1. Type your question in the input box at the bottom
2. Press Enter or click send
3. Wait for the AI to retrieve documents and generate answer
4. View the answer and expand sources if needed
5. Ask follow-up questions

**Tips:**
- Ask specific questions for better results
- Check sources to verify answer accuracy
- Rephrase if the answer isn't helpful
- Clear chat history to start fresh

### 4. Source Viewer

Every AI answer includes sources showing which documents were used.

**What you'll see:**
- Number of sources retrieved (usually 3)
- Document name and topic
- Content preview (first 200 characters)
- Full context in scrollable text area

**To view sources:**
1. After receiving an answer, look for "📖 View X sources"
2. Click to expand the source panel
3. Read through each source
4. Verify the AI's answer matches the source content

**Why sources matter:**
- Transparency - see exactly what the AI used
- Verification - check if answer is grounded in documents
- Learning - understand what information was retrieved
- Debugging - identify if wrong documents were retrieved

### 5. Settings Panel

Adjust RAG system behavior without editing code.

#### LLM Settings

**Temperature** (0.0 - 1.0)
- Controls response creativity/randomness
- Lower (0.0-0.3): More deterministic, consistent, factual
- Medium (0.4-0.7): Balanced (default: 0.7)
- Higher (0.8-1.0): More creative, varied, exploratory

**When to adjust:**
- Use low temperature for factual Q&A
- Use high temperature for creative or exploratory queries
- Default (0.7) works well for most cases

#### Retrieval Settings

**Top-K Results** (1 - 10)
- Number of document chunks to retrieve per query
- More chunks = more context but slower
- Fewer chunks = faster but might miss information

**When to adjust:**
- Increase if answers seem incomplete
- Decrease if answers are too verbose or off-topic
- Default (3) balances speed and quality

#### Chunking Settings

**Chunk Size** (200 - 2000 characters)
- Size of document pieces for embedding
- Larger chunks = more context per piece
- Smaller chunks = more granular retrieval

**Chunk Overlap** (0 - 500 characters)
- Character overlap between consecutive chunks
- Prevents information loss at boundaries
- More overlap = more redundancy but better context

**⚠️ Important:**
- Changing chunking settings requires vector store rebuild
- Rebuild recreates embeddings with new settings
- Can take time depending on document count

### 6. Vector Store Management

#### Rebuild Vector Store
- Recreates the FAISS vector database
- Processes documents with current chunking settings
- Uses rate limiting (batch_size=3, 2s delay)
- Shows progress during rebuild

**When to rebuild:**
- After uploading new documents
- After changing chunking settings
- After modifying documents in `data/documents/`
- If search results seem incorrect

#### Clear Chat History
- Removes all messages from current session
- Does NOT delete documents or vector store
- Useful for starting a fresh conversation
- Settings are preserved

## Workflow Examples

### Example 1: Using Sample Documents

```
1. Launch UI: `streamlit run run_ui.py`
2. Ensure "📖 Sample Documents" is selected
3. Wait for "✅ System Initialized" in sidebar
4. Ask: "What is Python?"
5. Read answer and expand sources
6. Ask follow-up: "What frameworks does Python have?"
7. Explore different questions
```

### Example 2: Uploading Custom Documents

```
1. Launch UI
2. Select "📁 Custom Documents" mode
3. Click "Choose files" in Upload section
4. Select your PDF/TXT/MD files
5. Click "✅ Upload"
6. Wait for success message
7. Click "🔄 Rebuild" to index documents
8. Wait for rebuild to complete
9. Ask questions about your documents
10. Check sources to verify correct retrieval
```

### Example 3: Adjusting Settings for Different Use Cases

**Factual Q&A (High Precision):**
```
1. Set Temperature: 0.2
2. Set Top-K: 5
3. Ask: "What is the exact definition of X?"
4. Expect consistent, factual answers
```

**Creative Exploration (High Recall):**
```
1. Set Temperature: 0.9
2. Set Top-K: 7
3. Ask: "What are some interesting applications of X?"
4. Expect varied, creative suggestions
```

**Fast Lookups (Speed Optimized):**
```
1. Set Temperature: 0.5
2. Set Top-K: 1
3. Ask simple, specific questions
4. Get quick answers from single source
```

## Troubleshooting

### UI Won't Launch

**Problem:** `streamlit: command not found`

**Solution:**
```bash
pip install streamlit
# Or if using virtual environment:
source venv/bin/activate
pip install streamlit
```

---

**Problem:** Port 8501 already in use

**Solution:**
```bash
# Use different port
streamlit run run_ui.py --server.port 8502
```

### Initialization Errors

**Problem:** "❌ Initialization failed: API key not valid"

**Solution:**
1. Check `.env` file exists in project root
2. Verify `GOOGLE_API_KEY` is set correctly
3. Get API key from https://aistudio.google.com/app/apikey
4. Restart the UI after fixing

---

**Problem:** "No documents found"

**Solution:**
- In Sample mode: Should work automatically (built-in documents)
- In Custom mode:
  - Add files to `data/documents/` directory
  - Or upload files via UI
  - Click "🔄 Rebuild"

### Upload Issues

**Problem:** "File too large" error

**Solution:**
- Max file size is 10MB
- Split large documents into smaller files
- Or place in `data/documents/` (no size limit)

---

**Problem:** "Unsupported file type"

**Solution:**
- Only PDF, TXT, MD are supported
- Convert other formats (DOCX, HTML) to these formats
- Or add custom loaders in `document_loader.py`

### Poor Answer Quality

**Problem:** Answers don't match documents

**Solution:**
1. Check sources - are they relevant?
2. Increase Top-K to retrieve more context
3. Try rephrasing your question
4. Rebuild vector store (might be corrupted)
5. Check if documents contain the information

---

**Problem:** Answers are too generic or hallucinated

**Solution:**
1. Lower temperature (0.2-0.4) for more factual responses
2. Check sources - if irrelevant, question might be out of scope
3. Add more specific documents
4. Rephrase question to be more specific

### Performance Issues

**Problem:** Slow response times

**Solution:**
- Reduce Top-K (fewer chunks = faster)
- Use smaller chunk sizes
- Reduce document count
- Check network connection (Gemini API calls)

---

**Problem:** Rebuild takes too long

**Solution:**
- Rate limiting is intentional (prevents API quota exhaustion)
- Start with fewer documents for testing
- Once cached, subsequent runs are fast
- For production, consider paid API tier

## Keyboard Shortcuts

Streamlit provides built-in shortcuts:

- `Enter` - Send message (in chat input)
- `Ctrl + R` or `Cmd + R` - Rerun app
- `Ctrl + K` or `Cmd + K` - Clear cache and rerun

## Tips and Best Practices

### For Better Results

1. **Ask specific questions**: "What is the refund policy for digital products?" vs "Tell me about refunds"
2. **Check sources**: Always verify the AI's answer against retrieved sources
3. **Iterate**: Rephrase if first answer isn't helpful
4. **Use custom mode**: Upload your own documents for real use cases
5. **Adjust settings**: Experiment with temperature and top-k for your needs

### For Better Performance

1. **Start small**: Test with 2-3 documents first
2. **Use cache**: Don't rebuild unless necessary
3. **Optimize chunks**: Default settings (800/100) work well for most cases
4. **Clear chat**: Long chat histories slow down the UI

### For Organization

1. **Name files clearly**: Use descriptive names like `product-pricing.txt`
2. **Organize by topic**: Use subdirectories in `data/documents/`
3. **Keep updated**: Remove outdated documents and rebuild
4. **Version control**: Don't commit uploaded files to git

## CLI Alternative

The original CLI interface still works alongside the UI:

```bash
# Use CLI (no UI)
python -m src.main

# Use CLI with custom documents
python -m src.main --use-documents

# CLI with rebuild
python -m src.main --rebuild
```

Both interfaces use the same RAG system underneath.

## Next Steps

1. **Explore sample mode**: Try the built-in documents to understand RAG
2. **Upload your documents**: Add 2-3 of your own files
3. **Experiment with settings**: Adjust temperature and top-k
4. **Read the tutorial**: See `COMPLETE_RAG_TUTORIAL.txt` for deep dive
5. **Extend the system**: Add features from plan file

## Getting Help

- **Documentation**: Read `PROJECT_OVERVIEW.md` and `COMPLETE_RAG_TUTORIAL.txt`
- **Code**: All UI code is in `src/ui/` directory
- **Examples**: Check `data/documents/` for example documents
- **Issues**: Check error messages in the UI (expand "Show detailed error")

---

**Happy Chatting! 🚀**

For more information about the RAG system architecture, see [COMPLETE_RAG_TUTORIAL.txt](COMPLETE_RAG_TUTORIAL.txt).
