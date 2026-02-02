# Documents Directory

This directory is where you place your own documents for the RAG system to index.

## Supported File Types

### Currently Supported (Built-in)
- **Text files** (`.txt`) - Plain text documents
- **Markdown files** (`.md`) - Formatted documentation

### Supported with Additional Setup
- **PDF files** (`.pdf`) - Requires: `pip install pypdf`
- **Word documents** (`.docx`) - Requires: `pip install python-docx`

## How to Add Documents

1. **Place files in this directory**
   ```
   data/documents/
   ├── your-document-1.txt
   ├── your-document-2.md
   ├── company-policy.txt
   └── api-documentation.md
   ```

2. **Organize by subdirectories (optional)**
   ```
   data/documents/
   ├── policies/
   │   ├── remote-work.txt
   │   └── vacation.txt
   ├── technical/
   │   ├── api-docs.md
   │   └── architecture.md
   └── faqs/
       └── common-questions.txt
   ```

3. **Use the document loader**
   The system will automatically load all `.txt` and `.md` files from this directory and its subdirectories.

## Example Documents

Two example documents are provided:
- `example-company-policy.txt` - Sample company policy document
- `product-api-docs.md` - Sample API documentation

You can:
- Keep these as examples
- Delete them and add your own
- Add more documents alongside them

## Document Guidelines

### File Naming
- Use descriptive names: `remote-work-policy.txt` instead of `doc1.txt`
- Avoid special characters: Use hyphens or underscores
- Keep names concise but meaningful

### Content Guidelines
- **Length**: 500-5000 words per document works best
- **Structure**: Use clear headings and paragraphs
- **Format**: Plain text or markdown preferred
- **Language**: English recommended (but not required)

### Good Document Types for RAG
- Company policies and procedures
- Product documentation
- Technical guides and manuals
- FAQs and knowledge bases
- Research notes
- Meeting notes
- Project documentation
- API documentation
- User guides

### Documents to Avoid
- Very short documents (<100 words) - not enough context
- Very long documents (>10,000 words) - consider splitting
- Binary files without text extractors
- Images without OCR
- Spreadsheets (unless converting to text first)

## Using Your Documents

### Option 1: Command Line Flag (Recommended)
```bash
# Use your documents instead of sample data
python -m src.main --use-documents

# Rebuild with your documents
python -m src.main --use-documents --rebuild
```

### Option 2: Modify data_loader.py
Edit `src/data_loader.py` to call `load_text_files()` instead of `get_sample_documents()`

## Testing Your Documents

1. Start small: Add 2-3 documents first
2. Run the system: `python -m src.main --use-documents`
3. Ask questions related to your documents
4. Check if retrieved chunks are relevant
5. Add more documents once working

## Troubleshooting

### "No files found"
- Check files are in `data/documents/`
- Ensure files have `.txt` or `.md` extension
- Check file permissions (should be readable)

### "Poor retrieval quality"
- Documents might be too short or too long
- Try breaking long documents into smaller files
- Ensure documents are well-structured with clear sections

### "Rate limit errors"
- Start with fewer documents (2-3)
- System will process in batches automatically
- Wait for quota to reset if needed

## Next Steps

1. Delete or keep the example documents
2. Add your own documents (start with 2-3)
3. Run: `python -m src.main --use-documents`
4. Ask questions about your documents
5. Iterate and improve!
