# Adding Your Own Documents to the RAG System

## Quick Start

### Step 1: Add Your Documents

Place your documents in the `data/documents/` directory:

```bash
# Your documents go here:
data/documents/
├── your-file-1.txt
├── your-file-2.md
├── company-policy.txt
└── technical-docs.md
```

**Supported formats:**
- ✅ Text files (`.txt`)
- ✅ Markdown files (`.md`)
- ✅ PDF files (`.pdf`) - requires: `pip install pypdf`

### Step 2: Run with Your Documents

```bash
# Use your documents instead of sample data
python -m src.main --use-documents

# Or rebuild the index with your documents
python -m src.main --use-documents --rebuild
```

### Step 3: Ask Questions

The system will automatically load all `.txt` and `.md` files from `data/documents/` and let you ask questions about them!

## Example Documents Provided

I've created 2 example documents to show you the format:

1. **[example-company-policy.txt](data/documents/example-company-policy.txt)**
   - Sample remote work policy
   - Shows how to format policy documents
   - Good example of structured business content

2. **[product-api-docs.md](data/documents/product-api-docs.md)**
   - Sample API documentation
   - Shows markdown formatting
   - Good example of technical documentation

You can:
- ✅ Keep these as examples and add your own alongside
- ✅ Delete them and use only your documents
- ✅ Modify them to fit your needs

## What Documents Should You Add?

### Great Choices:
- **Company documents**: Policies, procedures, handbooks
- **Technical docs**: API docs, architecture guides, README files
- **Knowledge base**: FAQs, troubleshooting guides, how-tos
- **Research notes**: Your personal notes, meeting summaries
- **Project docs**: Requirements, specifications, design docs

### Document Guidelines:
- **Length**: 500-5000 words per document (optimal)
- **Format**: Plain text or markdown preferred
- **Structure**: Use clear headings and sections
- **Language**: English works best (but not required)

### Avoid:
- Very short files (<100 words) - not enough context
- Very long files (>10,000 words) - consider splitting
- Binary files without text (images, spreadsheets)
- Sensitive data (passwords, personal info) - security risk!

## File Organization

### Simple (Flat Structure):
```
data/documents/
├── document-1.txt
├── document-2.txt
└── document-3.md
```

### Organized (Subdirectories):
```
data/documents/
├── policies/
│   ├── remote-work.txt
│   └── time-off.txt
├── technical/
│   ├── api-docs.md
│   └── setup-guide.md
└── faqs/
    └── common-questions.txt
```

Both work! The system searches all subdirectories automatically.

## Command Reference

### Basic Usage
```bash
# Use sample data (AI/ML topics)
python -m src.main

# Use your documents
python -m src.main --use-documents

# Rebuild index (when documents change)
python -m src.main --use-documents --rebuild
```

### When to Rebuild
Rebuild the vector store when:
- ✅ You add new documents
- ✅ You modify existing documents
- ✅ You delete documents
- ❌ NOT needed: Just asking questions (uses cached index)

## Testing Your Documents

### Start Small
```bash
# 1. Add just 2-3 documents first
cp your-doc-1.txt data/documents/
cp your-doc-2.txt data/documents/

# 2. Run the system
python -m src.main --use-documents

# 3. Ask a question you know the answer to
❓ Your question: What is our remote work policy?

# 4. Verify the answer is correct and cites sources
```

### Scale Up
Once working with 2-3 documents:
1. Add more documents gradually
2. Rebuild index: `python -m src.main --use-documents --rebuild`
3. Test with questions covering different topics
4. Check retrieval quality

## Example Session

```bash
$ python -m src.main --use-documents

================================================================================
🤖  RAG AGENT POC - Retrieval-Augmented Generation System
================================================================================
Using: Google Gemini (gemini-2.0-flash-exp)
Embedding Model: models/embedding-001
Vector Store: FAISS
================================================================================

🚀 Initializing RAG system...

📦 No existing vector store found. Creating new one...

⚠️  NOTE: This will call Google's Embedding API.
   Using rate limiting to stay within free tier limits (1,500 requests/day)
   Once created, the vector store will be cached and won't need API calls.

📚 Loading documents from data/documents/ directory...
📂 Found 2 document(s)
  ✓ Loaded: example-company-policy.txt
  ✓ Loaded: product-api-docs.md

📊 Total documents loaded: 2

✂️  Chunking documents...
Split 2 documents into 3 chunks

🔢 Creating embeddings and building vector store...
Creating vector store with 3 chunks...
Processing in batches of 3 with 2.0s delay to avoid rate limits...

[Batch 1/1] Processing 3 chunks...
✓ Batch 1 completed

✅ Vector store created successfully
✅ Vector store created and saved!

💬 Interactive Mode
--------------------------------------------------------------------------------
Ask questions about your documents.
Commands:
  - Type 'exit' or 'quit' to stop
  - Type 'rebuild' to rebuild the vector store
--------------------------------------------------------------------------------

❓ Your question: What is the home office stipend amount?

🔍 Processing question: What is the home office stipend amount?
📚 Retrieving relevant context...
🤖 Generating answer with Gemini...

================================================================================
❓ Question: What is the home office stipend amount?
================================================================================

💡 Answer:
According to the remote work policy (Source 1: example-company-policy.txt),
employees working remotely 3 or more days per week are eligible for a $500
annual stipend for home office equipment and supplies.

📖 Sources Used (1):

  1. Source: example-company-policy.txt (Topic: example_company_policy)
     Preview: COMPANY REMOTE WORK POLICY

Effective Date: January 1, 2024

Overview:
This document outlines the remote work policy for all employees. Our company supports flexible work...

================================================================================

❓ Your question: exit

👋 Goodbye!
```

## Troubleshooting

### "No documents found"
**Problem**: System says no documents in `data/documents/`

**Solutions**:
- Check files are in correct directory: `ls data/documents/`
- Ensure files have `.txt` or `.md` extension
- Check file permissions: `chmod 644 data/documents/*.txt`

### "Poor answers"
**Problem**: Answers don't match your documents

**Solutions**:
- Check retrieved sources - are they relevant?
- Documents might be too short (add more content)
- Documents might be too long (split into smaller files)
- Try rebuilding index: `--rebuild`

### "Rate limit errors"
**Problem**: Hitting API quota

**Solutions**:
- Start with fewer documents (2-3 first)
- System processes in batches automatically
- Wait 24 hours for quota reset
- Once created, index is cached (no more API calls!)

## Advanced: Loading PDFs

### Install PDF Support
```bash
pip install pypdf
```

### Add PDFs
```bash
# Create PDFs subdirectory
mkdir -p data/documents/pdfs

# Add your PDFs
cp your-document.pdf data/documents/pdfs/
```

### Modify main.py
Edit the document loading section to include PDFs:
```python
# In initialize_system():
documents = load_all_documents(include_pdfs=True)
```

## Next Steps

1. ✅ Add 2-3 of your own documents to `data/documents/`
2. ✅ Run: `python -m src.main --use-documents`
3. ✅ Ask questions about your documents
4. ✅ Check if answers are accurate and cite sources
5. ✅ Add more documents and rebuild

## Need Help?

Refer to:
- **[COMPLETE_RAG_TUTORIAL.txt](COMPLETE_RAG_TUTORIAL.txt)** - Complete system documentation
- **[data/documents/README.md](data/documents/README.md)** - Detailed document guidelines
- **[src/document_loader.py](src/document_loader.py)** - Code for loading documents

Happy building! 🚀
