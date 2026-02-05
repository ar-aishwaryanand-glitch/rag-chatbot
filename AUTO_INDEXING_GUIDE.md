# Automated Document Indexing

**Created:** 2026-02-03
**Status:** Ready to integrate

---

## 🎯 Overview

Automated indexing eliminates the need to manually click "Process & Index" after uploading documents. The system now:

1. **Auto-detects** new and modified documents
2. **Tracks** file changes using hashes and modification times
3. **Auto-indexes** on app startup and file upload
4. **Incremental updates** - only processes changed files

---

## 🚀 Features

### 1. Change Detection
- Tracks file hashes to detect modifications
- Identifies new, modified, and deleted files
- Stores metadata in `data/.index_metadata.json`

### 2. Smart Indexing
- **Incremental**: Adds only new files to existing index
- **Full rebuild**: Triggers when files are modified or deleted
- **Efficient**: Uses batching to avoid rate limits

### 3. Zero Manual Intervention
- Auto-indexes on app startup
- Auto-indexes when files are uploaded
- Shows status in sidebar

---

## 📦 Files Created

1. **[src/auto_indexer.py](src/auto_indexer.py)** - Core auto-indexing logic
   - `AutoIndexer` class
   - Change detection
   - Automatic indexing
   - Metadata tracking

2. **[src/ui/auto_index_integration.py](src/ui/auto_index_integration.py)** - Streamlit integration helpers
   - `check_and_index_on_startup()` - Auto-index on startup
   - `handle_file_upload()` - Upload with auto-indexing
   - `show_index_status_sidebar()` - Display index status
   - `auto_index_uploaded_files_widget()` - Complete upload widget

---

## 🔧 Integration Steps

### Option 1: Quick Integration (Recommended)

Modify `src/ui/streamlit_app_agent.py`:

```python
# At the top, add import
from src.ui.auto_index_integration import (
    check_and_index_on_startup,
    auto_index_uploaded_files_widget,
    show_index_status_sidebar
)

# In the main() function, after agent initialization:
def main():
    # ... existing code ...

    # Auto-index on startup (add this near the top, after imports)
    if 'startup_index_done' not in st.session_state:
        check_and_index_on_startup(force=False)
        st.session_state.startup_index_done = True

    # ... existing code ...

    # In sidebar, REPLACE the existing upload section (lines 260-306) with:
    auto_index_uploaded_files_widget()

    # Add index status display
    show_index_status_sidebar()

    # ... rest of the code ...
```

### Option 2: Manual Integration

If you want more control, use the individual functions:

```python
from src.auto_indexer import get_auto_indexer

# Check if indexing is needed
auto_indexer = get_auto_indexer()
if auto_indexer.needs_indexing():
    result = auto_indexer.index_documents(force_rebuild=False, verbose=True)
    print(f"Indexed: {result['new']} new, {result['modified']} modified")
```

---

## 💡 Usage Examples

### Example 1: Auto-index on Startup

```python
import streamlit as st
from src.ui.auto_index_integration import check_and_index_on_startup

# Run once per session
if 'indexed_on_startup' not in st.session_state:
    result = check_and_index_on_startup()

    if result['status'] == 'success':
        st.success(f"✅ Auto-indexed: {result['new']} new, {result['modified']} modified")

    st.session_state.indexed_on_startup = True
```

### Example 2: Manual Upload Handler

```python
from src.ui.auto_index_integration import handle_file_upload

uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True)

if uploaded_files:
    success, message, result = handle_file_upload(uploaded_files, auto_index=True)

    if success:
        st.success(message)
        st.rerun()  # Refresh to show new documents
    else:
        st.error(message)
```

### Example 3: Show Index Status

```python
from src.auto_indexer import get_auto_indexer

auto_indexer = get_auto_indexer()
status = auto_indexer.get_status()

st.write(f"Documents indexed: {status['total_indexed']}")
st.write(f"Pending changes: {status['pending_changes']['new']} new")

if status['needs_indexing']:
    if st.button("Re-index Now"):
        result = auto_indexer.index_documents(force_rebuild=True)
        st.success("Done!")
```

---

## 🔍 How It Works

### Change Detection Algorithm

1. **Calculate file hash** using MD5 of file contents
2. **Compare with stored metadata** from previous indexing
3. **Detect changes**:
   - **New**: File exists but not in metadata
   - **Modified**: File hash differs from stored hash
   - **Deleted**: File in metadata but doesn't exist

### Indexing Strategy

```
IF (deleted files OR modified files):
    → Full rebuild (delete vector store, re-index all)
ELSE IF (only new files):
    → Incremental add (append to existing index)
ELSE:
    → No action (all up to date)
```

### Metadata Tracking

Stored in `data/.index_metadata.json`:

```json
{
  "files": {
    "data/documents/example.pdf": {
      "size": 231300,
      "modified": 1706971200.0,
      "hash": "5d41402abc4b2a76b9719d911017c592",
      "indexed_at": "2026-02-03T16:53:00"
    }
  },
  "last_index": "2026-02-03T16:53:00"
}
```

---

## 📊 Benefits

### Before (Manual Indexing)
```
1. Upload files
2. Click "Process & Index" button
3. Wait for indexing
4. Check if it worked
```

### After (Auto Indexing)
```
1. Upload files → Auto-indexes automatically
   OR
1. Add files to data/documents/ → Auto-indexes on app startup
```

**Time saved:** ~5-10 seconds per upload
**User friction:** Eliminated
**Error prevention:** No forgetting to index

---

## 🛠️ Advanced Features

### Force Rebuild

```python
from src.auto_indexer import get_auto_indexer

# Force complete re-indexing
auto_indexer = get_auto_indexer()
result = auto_indexer.index_documents(force_rebuild=True)
```

### Check Status Without Indexing

```python
from src.auto_indexer import get_auto_indexer

auto_indexer = get_auto_indexer()
changes = auto_indexer.detect_changes()

print(f"New files: {len(changes['new'])}")
print(f"Modified files: {len(changes['modified'])}")
print(f"Deleted files: {len(changes['deleted'])}")
```

### Verbose Logging

```python
# Enable verbose output for debugging
result = auto_indexer.index_documents(force_rebuild=False, verbose=True)
```

Output:
```
🔍 Checking for document changes...
🔄 Full rebuild needed:
   - New files: 1
   - Modified files: 0
   - Deleted files: 0

📚 Re-indexing all documents...
   [1/7] Processing: example.pdf
      ✓ Extracted 11 pages
      ✓ Created 54 chunks

✅ Indexing complete!
```

---

## 🧪 Testing

### Test Auto-Indexing

```bash
# 1. Start with clean slate
rm -rf data/vector_store data/.index_metadata.json

# 2. Run your Streamlit app
streamlit run src/ui/streamlit_app_agent.py

# → Should auto-index all documents in data/documents/ on startup

# 3. Add a new document
cp ~/new_file.pdf data/documents/

# 4. Restart app
# → Should detect and index only the new file

# 5. Modify an existing document
echo "new content" >> data/documents/example.txt

# 6. Restart app
# → Should detect modification and trigger full rebuild
```

### Test Upload Auto-Indexing

1. Go to app sidebar
2. Upload a PDF file
3. ✅ Should automatically save and index (no button needed)
4. Query the PDF content immediately

---

## 🔧 Configuration

### Change Documents Directory

```python
from src.auto_indexer import AutoIndexer

# Custom documents directory
auto_indexer = AutoIndexer(
    documents_dir=Path("my_custom_docs"),
    metadata_file=Path("my_custom_metadata.json")
)
```

### Adjust Batching

In `src/auto_indexer.py`, line 205:

```python
# Current: batch_size=5, delay=1.0
self.vector_store_manager.create_vector_store(chunks=all_chunks, batch_size=5, delay=1.0)

# Faster (risk rate limits):
self.vector_store_manager.create_vector_store(chunks=all_chunks, batch_size=10, delay=0.5)

# Safer (slower):
self.vector_store_manager.create_vector_store(chunks=all_chunks, batch_size=3, delay=2.0)
```

---

## 🐛 Troubleshooting

### Issue: Documents not auto-indexing

**Check:**
1. Is `data/documents/` directory accessible?
2. Are files in supported formats (.txt, .md, .pdf)?
3. Check `data/.index_metadata.json` exists and is valid

**Fix:**
```python
# Force rebuild
from src.auto_indexer import get_auto_indexer
auto_indexer = get_auto_indexer()
result = auto_indexer.index_documents(force_rebuild=True, verbose=True)
```

### Issue: "File hash mismatch" errors

**Cause:** File was modified while being read

**Fix:** Ignore and let it retry on next startup

### Issue: Vector store corruption

**Fix:**
```bash
# Delete vector store and metadata, restart app
rm -rf data/vector_store data/.index_metadata.json
streamlit run src/ui/streamlit_app_agent.py
```

---

## 📝 Next Steps

1. **Integrate** into Streamlit app using Option 1 above
2. **Test** by uploading a file and verifying auto-indexing
3. **Monitor** the index status in the sidebar
4. **Enjoy** hands-free document management!

---

## 🎯 Quick Start Command

Use the standalone auto-indexing script:

```bash
# Check status
python -c "from src.auto_indexer import get_auto_indexer; print(get_auto_indexer().get_status())"

# Force re-index all documents
python -c "from src.auto_indexer import get_auto_indexer; get_auto_indexer().index_documents(force_rebuild=True, verbose=True)"
```

---

**Last Updated:** 2026-02-03
**Status:** ✅ Ready for production use
