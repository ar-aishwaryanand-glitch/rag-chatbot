"""Automatic document indexing system.

This module monitors the documents directory and automatically indexes
new or modified documents without manual intervention.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from .config import Config
from .logging_config import get_logger

logger = get_logger(__name__)
from .embeddings import EmbeddingManager
from .vector_store import VectorStoreManager


class AutoIndexer:
    """Automatically indexes new and modified documents."""

    def __init__(
        self,
        documents_dir: Path = None,
        metadata_file: Path = None
    ):
        """
        Initialize the auto-indexer.

        Args:
            documents_dir: Directory containing documents to index
            metadata_file: File to store indexing metadata
        """
        self.documents_dir = documents_dir or Config.DOCUMENTS_DIR
        self.metadata_file = metadata_file or Config.INDEX_METADATA_FILE
        self.metadata = self._load_metadata()

        # Initialize managers
        self.embedding_manager = None
        self.vector_store_manager = None

    def _load_metadata(self) -> Dict:
        """Load indexing metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Could not load index metadata: {e}")
                return {"files": {}, "last_index": None}
        return {"files": {}, "last_index": None}

    def _save_metadata(self):
        """Save indexing metadata to disk."""
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate hash of file contents."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _get_file_info(self, file_path: Path) -> Dict:
        """Get file information for tracking."""
        stats = file_path.stat()
        return {
            "size": stats.st_size,
            "modified": stats.st_mtime,
            "hash": self._get_file_hash(file_path),
            "indexed_at": datetime.now().isoformat()
        }

    def detect_changes(self) -> Dict[str, List[Path]]:
        """
        Detect new, modified, and deleted documents.

        Returns:
            Dictionary with 'new', 'modified', 'deleted' file lists
        """
        if not self.documents_dir.exists():
            return {"new": [], "modified": [], "deleted": []}

        # Get current files
        current_files = set()
        for ext in ['.txt', '.md', '.pdf']:
            current_files.update(self.documents_dir.glob(f"*{ext}"))

        # Filter out hidden files
        current_files = {f for f in current_files if not f.name.startswith('.')}

        # Get previously indexed files
        indexed_files = set(Path(f) for f in self.metadata["files"].keys())

        # Detect changes
        new_files = []
        modified_files = []
        deleted_files = list(indexed_files - current_files)

        for file_path in current_files:
            file_str = str(file_path)

            if file_str not in self.metadata["files"]:
                # New file
                new_files.append(file_path)
            else:
                # Check if modified
                old_info = self.metadata["files"][file_str]
                try:
                    current_hash = self._get_file_hash(file_path)
                    if current_hash != old_info.get("hash"):
                        modified_files.append(file_path)
                except (OSError, IOError) as e:
                    # If we can't read the file, treat as modified
                    logger.debug(f"Cannot read file {file_path}, treating as modified: {e}")
                    modified_files.append(file_path)

        return {
            "new": new_files,
            "modified": modified_files,
            "deleted": deleted_files
        }

    def needs_indexing(self) -> bool:
        """Check if any files need indexing."""
        changes = self.detect_changes()
        return bool(changes["new"] or changes["modified"] or changes["deleted"])

    def index_documents(
        self,
        force_rebuild: bool = False,
        verbose: bool = True
    ) -> Dict:
        """
        Index new and modified documents.

        Args:
            force_rebuild: Force complete rebuild of vector store
            verbose: Print progress messages

        Returns:
            Dictionary with indexing results
        """
        if verbose:
            logger.info("Checking for document changes...")

        # Detect changes
        changes = self.detect_changes()

        if not force_rebuild and not any(changes.values()):
            if verbose:
                logger.info("All documents are up to date!")
            return {
                "status": "up_to_date",
                "new": 0,
                "modified": 0,
                "deleted": 0
            }

        # Initialize managers if needed
        if self.embedding_manager is None:
            self.embedding_manager = EmbeddingManager()
        if self.vector_store_manager is None:
            self.vector_store_manager = VectorStoreManager(self.embedding_manager)

        # Determine if we need full rebuild
        needs_rebuild = force_rebuild or changes["deleted"] or changes["modified"]

        if needs_rebuild:
            if verbose:
                logger.info(f"Full rebuild needed: new={len(changes['new'])}, modified={len(changes['modified'])}, deleted={len(changes['deleted'])}")
                logger.info("Re-indexing all documents...")

            # Delete old vector store
            if Config.VECTOR_STORE_PATH.exists():
                import shutil
                shutil.rmtree(Config.VECTOR_STORE_PATH)

            # Get all current documents
            all_files = list(self.documents_dir.glob("*.txt")) + \
                       list(self.documents_dir.glob("*.md")) + \
                       list(self.documents_dir.glob("*.pdf"))
            all_files = [f for f in all_files if not f.name.startswith('.')]

            # Process all documents
            all_chunks = self._process_documents(all_files, verbose)

            if not all_chunks:
                if verbose:
                    logger.warning("No documents to index!")
                return {
                    "status": "error",
                    "message": "No documents found"
                }

            # Create vector store
            if verbose:
                logger.info(f"Creating vector store with {len(all_chunks)} chunks...")
            self.vector_store_manager.create_vector_store(chunks=all_chunks, batch_size=5, delay=1.0)
            self.vector_store_manager.save_vector_store()

            # Update metadata for all files
            self.metadata["files"] = {}
            for file_path in all_files:
                self.metadata["files"][str(file_path)] = self._get_file_info(file_path)

        else:
            # Only new files, can add incrementally
            if verbose:
                logger.info(f"Adding {len(changes['new'])} new documents...")

            new_chunks = self._process_documents(changes["new"], verbose)

            if new_chunks:
                # Add to existing vector store
                self.vector_store_manager.vector_store.add_documents(new_chunks)
                self.vector_store_manager.save_vector_store()

                # Update metadata
                for file_path in changes["new"]:
                    self.metadata["files"][str(file_path)] = self._get_file_info(file_path)

        # Save metadata
        self.metadata["last_index"] = datetime.now().isoformat()
        self._save_metadata()

        if verbose:
            logger.info("Indexing complete!")

        return {
            "status": "success",
            "new": len(changes["new"]),
            "modified": len(changes["modified"]),
            "deleted": len(changes["deleted"]),
            "total_files": len(self.metadata["files"])
        }

    def _process_documents(self, file_paths: List[Path], verbose: bool = True) -> List:
        """Process document files into chunks."""
        all_chunks = []

        for i, file_path in enumerate(file_paths, 1):
            if verbose:
                logger.info(f"[{i}/{len(file_paths)}] Processing: {file_path.name}")

            try:
                suffix = file_path.suffix.lower()

                # Extract text based on file type
                if suffix == '.pdf':
                    from pypdf import PdfReader
                    reader = PdfReader(str(file_path))
                    text_content = ""
                    for page in reader.pages:
                        text_content += page.extract_text() + "\n"
                    if verbose:
                        logger.info(f"Extracted {len(reader.pages)} pages from {file_path.name}")

                elif suffix in ['.txt', '.md']:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text_content = f.read()
                    if verbose:
                        logger.info(f"Read {len(text_content)} characters from {file_path.name}")

                else:
                    if verbose:
                        logger.warning(f"Unsupported file type: {suffix}")
                    continue

                # Chunk the document
                chunks = self.embedding_manager.chunk_documents([{
                    'content': text_content,
                    'metadata': {
                        'source': file_path.name,
                        'file_type': suffix.lstrip('.'),
                        'file_size': file_path.stat().st_size
                    }
                }])

                if verbose:
                    logger.info(f"Created {len(chunks)} chunks from {file_path.name}")

                all_chunks.extend(chunks)

            except Exception as e:
                if verbose:
                    logger.error(f"Error processing {file_path.name}: {str(e)}")
                continue

        return all_chunks

    def get_status(self) -> Dict:
        """Get current indexing status."""
        changes = self.detect_changes()
        return {
            "documents_dir": str(self.documents_dir),
            "total_indexed": len(self.metadata["files"]),
            "last_index": self.metadata.get("last_index"),
            "pending_changes": {
                "new": len(changes["new"]),
                "modified": len(changes["modified"]),
                "deleted": len(changes["deleted"])
            },
            "needs_indexing": self.needs_indexing()
        }


# Singleton instance for use across the app
_auto_indexer_instance = None


def get_auto_indexer() -> AutoIndexer:
    """Get or create the singleton AutoIndexer instance."""
    global _auto_indexer_instance
    if _auto_indexer_instance is None:
        _auto_indexer_instance = AutoIndexer()
    return _auto_indexer_instance
