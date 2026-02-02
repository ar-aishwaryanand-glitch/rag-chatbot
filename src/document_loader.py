"""Document loader for reading files from the documents directory."""

from pathlib import Path
from typing import List, Dict
import os

def load_text_files(directory: str = None) -> List[Dict[str, str]]:
    """
    Load all .txt and .md files from a directory.

    Args:
        directory: Path to documents directory.
                   Defaults to data/documents/

    Returns:
        List of document dictionaries with content and metadata
    """
    if directory is None:
        # Default to data/documents/
        directory = Path(__file__).parent.parent / "data" / "documents"
    else:
        directory = Path(directory)

    if not directory.exists():
        print(f"⚠️  Warning: Directory {directory} does not exist")
        return []

    documents = []

    # Find all text and markdown files
    text_files = list(directory.glob("**/*.txt")) + list(directory.glob("**/*.md"))

    if not text_files:
        print(f"⚠️  Warning: No .txt or .md files found in {directory}")
        return []

    print(f"📂 Found {len(text_files)} document(s)")

    for file_path in text_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract topic from filename or parent directory
            topic = file_path.stem.lower().replace('-', '_').replace(' ', '_')

            documents.append({
                "content": content,
                "metadata": {
                    "source": file_path.name,
                    "topic": topic,
                    "file_path": str(file_path),
                    "file_type": file_path.suffix
                }
            })

            print(f"  ✓ Loaded: {file_path.name}")

        except Exception as e:
            print(f"  ✗ Error loading {file_path.name}: {e}")

    return documents


def load_pdfs(directory: str = None) -> List[Dict[str, str]]:
    """
    Load all PDF files from a directory.

    Requires: pip install pypdf

    Args:
        directory: Path to PDF directory

    Returns:
        List of document dictionaries
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        print("⚠️  pypdf not installed. Run: pip install pypdf")
        return []

    if directory is None:
        directory = Path(__file__).parent.parent / "data" / "documents" / "pdfs"
    else:
        directory = Path(directory)

    if not directory.exists():
        print(f"⚠️  Warning: Directory {directory} does not exist")
        return []

    documents = []
    pdf_files = list(directory.glob("**/*.pdf"))

    if not pdf_files:
        print(f"⚠️  Warning: No PDF files found in {directory}")
        return []

    print(f"📂 Found {len(pdf_files)} PDF(s)")

    for pdf_path in pdf_files:
        try:
            reader = PdfReader(str(pdf_path))

            # Extract text from all pages
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"

            documents.append({
                "content": text.strip(),
                "metadata": {
                    "source": pdf_path.name,
                    "topic": pdf_path.stem.lower().replace('-', '_').replace(' ', '_'),
                    "file_path": str(pdf_path),
                    "file_type": ".pdf",
                    "num_pages": len(reader.pages)
                }
            })

            print(f"  ✓ Loaded: {pdf_path.name} ({len(reader.pages)} pages)")

        except Exception as e:
            print(f"  ✗ Error loading {pdf_path.name}: {e}")

    return documents


def get_document_count(directory: str = None) -> int:
    """Return the number of documents in the directory."""
    documents = load_text_files(directory)
    return len(documents)


def load_all_documents(directory: str = None, include_pdfs: bool = False) -> List[Dict[str, str]]:
    """
    Load all supported documents from a directory.

    Args:
        directory: Path to documents directory
        include_pdfs: Whether to load PDF files (requires pypdf)

    Returns:
        List of all documents
    """
    all_docs = []

    # Load text files
    text_docs = load_text_files(directory)
    all_docs.extend(text_docs)

    # Load PDFs if requested
    if include_pdfs:
        pdf_docs = load_pdfs(directory)
        all_docs.extend(pdf_docs)

    print(f"\n📊 Total documents loaded: {len(all_docs)}")
    return all_docs
