"""
Manually re-index all documents including PDFs.

Run this if the "Process & Index" button isn't working.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.vector_store import VectorStoreManager
from src.embeddings import EmbeddingManager
from src.config import Config

def reindex_all_documents():
    """Re-index all documents in the documents directory."""

    print("=" * 60)
    print("Re-indexing All Documents")
    print("=" * 60)

    # Initialize embedding manager and vector store manager
    print("\n1. Initializing embedding manager...")
    embedding_manager = EmbeddingManager()

    print("   Initializing vector store...")
    manager = VectorStoreManager(embedding_manager=embedding_manager)

    # Delete existing vector store if it exists
    if Config.VECTOR_STORE_PATH.exists():
        print(f"\n2. Deleting old vector store...")
        import shutil
        shutil.rmtree(Config.VECTOR_STORE_PATH)
        print("   ✓ Old vector store deleted")

    # Get document directory
    doc_dir = Path("data/documents")

    if not doc_dir.exists():
        print(f"❌ Document directory not found: {doc_dir}")
        return

    # Find all documents
    document_files = list(doc_dir.glob("*"))
    document_files = [d for d in document_files if d.is_file() and not d.name.startswith('.')]

    print(f"\n3. Found {len(document_files)} documents:")
    for doc in document_files:
        file_size = doc.stat().st_size / 1024  # KB
        print(f"   - {doc.name} ({file_size:.1f} KB)")

    # Process each document and collect all chunks
    print(f"\n4. Processing documents...")
    all_chunks = []

    for i, doc_path in enumerate(document_files, 1):
        print(f"\n   [{i}/{len(document_files)}] Processing: {doc_path.name}")

        try:
            # Determine file type
            suffix = doc_path.suffix.lower()

            if suffix == '.pdf':
                print(f"      Type: PDF")
                # Read PDF
                from pypdf import PdfReader
                reader = PdfReader(str(doc_path))

                text_content = ""
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    text_content += f"\n--- Page {page_num + 1} ---\n{text}\n"

                print(f"      ✓ Extracted {len(reader.pages)} pages")
                print(f"      ✓ Total text length: {len(text_content)} characters")

            elif suffix in ['.txt', '.md']:
                print(f"      Type: Text/Markdown")
                with open(doc_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                print(f"      ✓ Text length: {len(text_content)} characters")

            else:
                print(f"      ⚠️  Unsupported file type: {suffix}")
                continue

            # Chunk the text
            chunks = embedding_manager.chunk_documents([{
                'content': text_content,
                'metadata': {
                    'source': doc_path.name,
                    'file_type': suffix.lstrip('.'),
                    'file_size': doc_path.stat().st_size
                }
            }])

            print(f"      ✓ Created {len(chunks)} chunks")
            all_chunks.extend(chunks)

        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

    if not all_chunks:
        print("\n❌ No documents were successfully processed!")
        return

    print(f"\n5. Creating vector store with {len(all_chunks)} total chunks...")
    manager.create_vector_store(chunks=all_chunks, batch_size=3, delay=2.0)

    print(f"\n6. Saving vector store...")
    manager.save_vector_store()

    print(f"\n✅ Re-indexing complete!")
    print(f"\nVector store location: {Config.VECTOR_STORE_PATH}")
    print(f"Total documents indexed: {len(document_files)}")
    print(f"Total chunks created: {len(all_chunks)}")

    print("\n" + "=" * 60)
    print("You can now query your documents in the Streamlit app!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        reindex_all_documents()
    except Exception as e:
        print(f"\n❌ Error during re-indexing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
