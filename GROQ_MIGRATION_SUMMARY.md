# Groq API Integration - Migration Summary

## ✅ Successfully Migrated to Groq!

Your RAG system now uses **Groq API** for ultra-fast LLM inference with the Llama 3.3 70B model.

---

## 🔄 What Changed

### 1. **API Configuration (.env)**
```bash
# NEW: Groq API Key
GROQ_API_KEY=your_groq_api_key_here

# NEW: LLM Provider
LLM_PROVIDER=groq
GROQ_MODEL=llama-3.3-70b-versatile

# NEW: Embedding Provider (Free HuggingFace)
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### 2. **Updated Dependencies (requirements.txt)**
Added:
- `groq>=0.4.0` - Groq API client
- `langchain-groq>=0.1.0` - LangChain integration for Groq
- `langchain-huggingface>=0.0.1` - HuggingFace embeddings integration
- `sentence-transformers>=2.2.0` - Local embeddings models

### 3. **Updated Core Files**

#### **src/config.py**
- Added support for multiple LLM providers (Groq, Google)
- Added Groq API key validation
- Added support for multiple embedding providers
- New methods: `get_llm_display_name()`, `get_embedding_display_name()`

#### **src/embeddings.py**
- Support for HuggingFace embeddings (free, local)
- Automatic fallback if package not installed
- Uses `sentence-transformers/all-MiniLM-L6-v2` model

#### **src/rag_chain.py**
- Support for both Groq and Google Gemini LLMs
- Automatic LLM initialization based on config
- Updated console output to show which LLM is being used

---

## 🚀 Performance Benefits

### Groq Advantages:
1. **⚡ Ultra-Fast Inference**: 10-100x faster than traditional APIs
2. **💰 Cost-Effective**: Competitive pricing
3. **🔥 Latest Models**: Llama 3.3 70B, Mixtral, and more
4. **🎯 High Quality**: State-of-the-art model performance

### Current Setup:
- **LLM**: Groq (Llama 3.3 70B Versatile)
- **Embeddings**: HuggingFace (sentence-transformers/all-MiniLM-L6-v2)
- **Vector Store**: FAISS (local, fast)

---

## 📊 Comparison

| Feature | Google Gemini (Before) | Groq (Now) |
|---------|------------------------|------------|
| **LLM** | Gemini 2.0 Flash | Llama 3.3 70B |
| **Speed** | Standard | 10-100x Faster ⚡ |
| **Embeddings** | Google API | HuggingFace (Local) 🆓 |
| **Cost** | Per-request | Per-request |
| **Rate Limiting** | Yes | Yes (generous) |
| **Local Processing** | No | Embeddings only |

---

## 🎛️ Available Models on Groq

You can change the model in `.env`:

```bash
# Fast, balanced (current)
GROQ_MODEL=llama-3.3-70b-versatile

# Smaller, faster
GROQ_MODEL=llama-3.1-8b-instant

# Mixtral (good for multilingual)
GROQ_MODEL=mixtral-8x7b-32768

# Llama 3.1 70B (high quality)
GROQ_MODEL=llama-3.1-70b-versatile

# Llama Guard (content moderation)
GROQ_MODEL=llama-guard-3-8b
```

See all models: https://console.groq.com/docs/models

---

## 🔧 How to Use

### Streamlit UI (Recommended)
```bash
streamlit run run_ui.py
# or
./launch_ui.sh
```

The UI will automatically use Groq!

### CLI
```bash
# Sample documents
python -m src.main

# Your documents
python -m src.main --use-documents
```

---

## ⚙️ Configuration Options

### Switch Between Providers

**To use Groq (current):**
```bash
# In .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_key
```

**To switch back to Google Gemini:**
```bash
# In .env
LLM_PROVIDER=google
GOOGLE_API_KEY=your_google_key
```

### Embedding Options

**HuggingFace (current, free, local):**
```bash
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

**Google (requires API key):**
```bash
EMBEDDING_PROVIDER=google
EMBEDDING_MODEL=models/embedding-001
GOOGLE_API_KEY=your_google_key
```

**Other HuggingFace models:**
```bash
# Larger, more accurate
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2

# Multilingual
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# Fastest
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

---

## 🧪 Testing the Setup

### Quick Test
```bash
python -m src.main
```

Ask: "What is Python?"

You should see:
```
🤖 Initializing Groq LLM: llama-3.3-70b-versatile
📦 Loading HuggingFace embeddings: sentence-transformers/all-MiniLM-L6-v2
...
🤖 Generating answer with Groq (llama-3.3-70b-versatile)...
```

### Streamlit Test
1. Launch: `streamlit run run_ui.py`
2. Ask a question
3. Check response speed (should be fast! ⚡)

---

## 📝 Notes

### First Run
- **HuggingFace embeddings**: ~90MB download on first run
- Models are cached locally for subsequent runs
- No API calls needed for embeddings after first run

### Vector Store
- Old vector store cleared (was using Google embeddings)
- Will rebuild automatically on first query
- New embeddings are fully local (no API cost!)

### API Keys
- **Groq API Key**: Get free key at https://console.groq.com
- **Free tier**: Very generous limits for development
- **Your key**: Already configured in `.env`

---

## 🐛 Troubleshooting

### "GROQ_API_KEY not found"
- Check `.env` file has: `GROQ_API_KEY=gsk_...`
- Restart application after changing `.env`

### "Could not import langchain_groq"
- Run: `pip install langchain-groq`
- Or: `pip install -r requirements.txt`

### "HuggingFace embeddings failed"
- Run: `pip install sentence-transformers`
- First run downloads ~90MB model (one-time)

### Slow first query
- Normal! HuggingFace downloads model on first run
- Subsequent queries use cached model (fast)
- Embeddings are generated locally (no network delay)

---

## 💡 Pro Tips

### Optimize for Speed
1. **Use smaller model**: `llama-3.1-8b-instant` for lightning-fast responses
2. **Reduce top-k**: Set `TOP_K_RESULTS=1` in config for faster retrieval
3. **Lower temperature**: `LLM_TEMPERATURE=0.3` for more consistent, faster responses

### Optimize for Quality
1. **Use larger model**: `llama-3.1-70b-versatile` for best accuracy
2. **Increase top-k**: More context = better answers
3. **Better embeddings**: Try `all-mpnet-base-v2` for improved search

### Save Costs
1. **Local embeddings**: HuggingFace = 100% free (current setup ✓)
2. **Batch queries**: Process multiple questions together
3. **Cache results**: Vector store caching already enabled

---

## 📚 Resources

- **Groq Console**: https://console.groq.com
- **Groq Docs**: https://console.groq.com/docs
- **Available Models**: https://console.groq.com/docs/models
- **HuggingFace Models**: https://huggingface.co/sentence-transformers
- **LangChain Groq**: https://python.langchain.com/docs/integrations/llms/groq

---

## ✅ Summary

You're now running:
- ⚡ **Groq API** for ultra-fast LLM inference
- 🆓 **HuggingFace** for free local embeddings
- 🚀 **Llama 3.3 70B** for high-quality responses
- 💰 **Cost-effective** setup with generous free tiers

**Everything is configured and ready to use!**

Launch the UI with:
```bash
streamlit run run_ui.py
```

Or use the CLI:
```bash
python -m src.main
```

Enjoy your supercharged RAG system! 🎉
