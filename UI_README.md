# RAG Chat Assistant - Web UI

## Quick Start (30 seconds)

### Option 1: Using Launch Scripts

**Mac/Linux:**
```bash
./launch_ui.sh
```

**Windows:**
```cmd
launch_ui.bat
```

### Option 2: Direct Command

```bash
streamlit run run_ui.py
```

The UI will open automatically at **http://localhost:8501** 🚀

## First Time Setup

1. **Install Streamlit** (if not already installed):
   ```bash
   pip install streamlit
   ```

2. **Verify your `.env` file** has your Google API key:
   ```bash
   GOOGLE_API_KEY=your_key_here
   ```

3. **Launch the UI** using one of the methods above

## What You'll See

```
┌─────────────────────────────────────┐
│  🤖 RAG Chat Assistant              │
├──────────────┬──────────────────────┤
│  SIDEBAR     │  CHAT AREA           │
│              │                      │
│ Mode         │  Welcome Message     │
│ ○ Sample     │                      │
│ ● Custom     │  [Your questions]    │
│              │  [AI answers]        │
│ Settings     │  [Sources]          │
│ ⚙️ Temp      │                      │
│ 🔍 Top-K     │                      │
│              │                      │
│ Actions      │  [Ask a question]   │
│ 🔄 Rebuild   │                      │
│ 🗑️ Clear     │                      │
└──────────────┴──────────────────────┘
```

## Features

- **💬 Chat Interface**: ChatGPT-style conversation
- **📤 File Upload**: Drag & drop PDF, TXT, MD files
- **📖 Source Viewer**: See which documents were used
- **⚙️ Live Settings**: Adjust temperature, top-k without restart
- **🔄 Two Modes**: Sample docs (demo) or your own documents

## Try It Now

1. **Launch the UI** (see Quick Start above)
2. **Ask a question**: "What is Python?"
3. **View sources**: Click "📖 View sources" to see retrieved docs
4. **Upload documents**: Switch to Custom mode, upload files
5. **Adjust settings**: Play with temperature and top-k sliders

## Common Commands

```bash
# Launch on default port (8501)
streamlit run run_ui.py

# Launch on custom port
streamlit run run_ui.py --server.port 8502

# Launch accessible from network
streamlit run run_ui.py --server.address 0.0.0.0

# Using launch scripts
./launch_ui.sh 8502        # Mac/Linux with custom port
launch_ui.bat 8502         # Windows with custom port
```

## Troubleshooting

**"Port already in use"**
```bash
streamlit run run_ui.py --server.port 8502
```

**"Streamlit not found"**
```bash
pip install streamlit
```

**"Initialization failed"**
- Check `.env` file exists with valid `GOOGLE_API_KEY`
- Get API key: https://aistudio.google.com/app/apikey

**"No documents found"**
- Sample mode: Should work automatically
- Custom mode: Upload files or add to `data/documents/`

## Documentation

- **[UI_GUIDE.md](UI_GUIDE.md)** - Complete UI documentation
- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - Project overview
- **[COMPLETE_RAG_TUTORIAL.txt](COMPLETE_RAG_TUTORIAL.txt)** - RAG system deep dive

## CLI Alternative

Prefer command line? The original CLI still works:

```bash
# CLI with sample data
python -m src.main

# CLI with your documents
python -m src.main --use-documents
```

## Need Help?

- **UI not working**: See [UI_GUIDE.md](UI_GUIDE.md) troubleshooting section
- **RAG system questions**: See [COMPLETE_RAG_TUTORIAL.txt](COMPLETE_RAG_TUTORIAL.txt)
- **Code questions**: Check `src/ui/` directory for implementation

---

**Ready to chat?** Run `./launch_ui.sh` or `streamlit run run_ui.py` 🚀
