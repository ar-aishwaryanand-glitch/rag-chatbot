"""FAISS vector store management for RAG Agent POC."""

import time
import hashlib
import os
from pathlib import Path
from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from .config import Config
from .embeddings import EmbeddingManager

class VectorStoreManager:
    """Manages FAISS vector store operations."""

    def __init__(self, embedding_manager: EmbeddingManager, verify_integrity: bool = True):
        """
        Initialize the vector store manager.

        Args:
            embedding_manager: Instance of EmbeddingManager
            verify_integrity: Verify SHA256 checksum before loading
        """
        self.embedding_manager = embedding_manager
        self.vector_store: Optional[FAISS] = None
        self.store_path = Config.VECTOR_STORE_PATH
        self.verify_integrity = verify_integrity
        self._checksum_file = Path(str(self.store_path) + ".sha256")

        # Automatically load vector store from disk if it exists
        if self.store_path.exists():
            try:
                # Verify integrity before loading
                if self.verify_integrity and not self._verify_checksum():
                    print("⚠️  Vector store integrity check failed!")
                    print("   Index may have been tampered with or corrupted")
                    print("   You may need to re-index your documents")
                    return

                print(f"📂 Loading existing vector store from {self.store_path}...")
                self.vector_store = FAISS.load_local(
                    str(self.store_path),
                    embeddings=self.embedding_manager.embedding_model,
                    allow_dangerous_deserialization=True
                )
                print("✅ Vector store loaded successfully")
            except Exception as e:
                print(f"⚠️  Warning: Could not load vector store: {e}")
                print("   You may need to re-index your documents")

    def _compute_checksum(self) -> Optional[str]:
        """Compute SHA256 checksum of the FAISS index file."""
        index_file = Path(self.store_path) / "index.faiss"
        if not index_file.exists():
            return None

        sha256 = hashlib.sha256()
        with open(index_file, 'rb') as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)

        return sha256.hexdigest()

    def _verify_checksum(self) -> bool:
        """Verify FAISS index checksum."""
        if not self._checksum_file.exists():
            print("📝 No checksum file found - skipping integrity check")
            return True

        try:
            with open(self._checksum_file, 'r') as f:
                stored_checksum = f.read().strip()

            current_checksum = self._compute_checksum()
            if current_checksum is None:
                print("⚠️  Could not compute checksum - index file missing")
                return False

            if stored_checksum != current_checksum:
                print(f"   Expected: {stored_checksum[:16]}...")
                print(f"   Got: {current_checksum[:16]}...")
                return False

            print("✅ Vector store integrity verified")
            return True

        except Exception as e:
            print(f"⚠️  Checksum verification error: {e}")
            return False

    def _save_checksum(self) -> None:
        """Save SHA256 checksum of the FAISS index."""
        try:
            checksum = self._compute_checksum()
            if checksum:
                with open(self._checksum_file, 'w') as f:
                    f.write(checksum)
                print(f"🔐 Saved integrity checksum")
        except Exception as e:
            print(f"⚠️  Could not save checksum: {e}")

    def create_vector_store(
        self,
        chunks: List[Document],
        batch_size: int = 50,
        delay: float = 0.0,
        adaptive_delay: bool = True
    ) -> FAISS:
        """
        Create a new FAISS vector store from document chunks with optimized batching.

        Args:
            chunks: List of LangChain Document objects
            batch_size: Number of chunks to process at once (default: 50)
            delay: Fixed delay in seconds between batches (default: 0 for local FAISS)
            adaptive_delay: Apply delay only on rate limit errors (default: True)

        Returns:
            FAISS vector store instance
        """
        print(f"Creating vector store with {len(chunks)} chunks...")
        print(f"Processing in batches of {batch_size}...")

        # Exponential backoff settings
        base_delay = 1.0
        max_delay = 60.0
        current_delay = base_delay

        # Process first batch to create initial vector store
        first_batch = chunks[:batch_size]
        total_batches = (len(chunks) - 1) // batch_size + 1
        print(f"\n[Batch 1/{total_batches}] Processing {len(first_batch)} chunks...")

        self.vector_store = FAISS.from_documents(
            documents=first_batch,
            embedding=self.embedding_manager.embedding_model
        )
        print("✓ Batch 1 completed")

        # Process remaining chunks in batches
        for i in range(batch_size, len(chunks), batch_size):
            batch_num = (i // batch_size) + 1

            # Apply fixed delay if specified (non-adaptive mode)
            if delay > 0 and not adaptive_delay:
                print(f"⏳ Waiting {delay}s before next batch...")
                time.sleep(delay)

            batch = chunks[i:i + batch_size]
            print(f"\n[Batch {batch_num}/{total_batches}] Processing {len(batch)} chunks...")

            # Add documents with retry logic
            retry_count = 0
            max_retries = 3

            while retry_count < max_retries:
                try:
                    self.vector_store.add_documents(batch)
                    print(f"✓ Batch {batch_num} completed")
                    # Reset delay on success
                    current_delay = base_delay
                    break

                except Exception as e:
                    error_str = str(e).lower()
                    # Check for rate limit errors (429 or similar)
                    if '429' in error_str or 'rate limit' in error_str or 'too many requests' in error_str:
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"⚠️  Rate limited. Waiting {current_delay}s before retry {retry_count}/{max_retries}...")
                            time.sleep(current_delay)
                            # Exponential backoff
                            current_delay = min(current_delay * 2, max_delay)
                        else:
                            print(f"❌ Max retries reached for batch {batch_num}")
                            raise
                    else:
                        # Non-rate-limit error, re-raise immediately
                        raise

        print("\n✅ Vector store created successfully")
        return self.vector_store

    def save_vector_store(self) -> None:
        """Save the vector store to disk with integrity checksum."""
        if self.vector_store is None:
            raise ValueError("No vector store to save. Create one first.")

        # Create directory if it doesn't exist
        self.store_path.mkdir(parents=True, exist_ok=True)

        # Save the vector store
        self.vector_store.save_local(str(self.store_path))
        print(f"Vector store saved to {self.store_path}")

        # Save integrity checksum
        self._save_checksum()

    def load_vector_store(self, skip_integrity_check: bool = False) -> FAISS:
        """
        Load vector store from disk with integrity verification.

        Args:
            skip_integrity_check: Skip checksum verification (not recommended)

        Returns:
            Loaded FAISS vector store

        Raises:
            FileNotFoundError: If vector store doesn't exist
            ValueError: If integrity check fails
        """
        if not self.store_path.exists():
            raise FileNotFoundError(
                f"Vector store not found at {self.store_path}. "
                "Create one first using create_vector_store()."
            )

        # Verify integrity before loading
        if self.verify_integrity and not skip_integrity_check:
            if not self._verify_checksum():
                raise ValueError(
                    "Vector store integrity check failed. "
                    "Index may have been tampered with or corrupted. "
                    "Re-index documents or use skip_integrity_check=True to bypass."
                )

        print(f"Loading vector store from {self.store_path}...")
        self.vector_store = FAISS.load_local(
            str(self.store_path),
            embeddings=self.embedding_manager.embedding_model,
            allow_dangerous_deserialization=True  # Required for FAISS
        )
        print("Vector store loaded successfully")
        return self.vector_store

    def similarity_search(
        self,
        query: str,
        k: int = Config.TOP_K_RESULTS
    ) -> List[Document]:
        """
        Search for similar documents using the query.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of similar Document objects
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Load or create one first.")

        results = self.vector_store.similarity_search(query, k=k)
        return results

    def similarity_search_with_score(
        self,
        query: str,
        k: int = Config.TOP_K_RESULTS
    ) -> List[tuple]:
        """
        Search for similar documents with similarity scores.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of (Document, score) tuples
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Load or create one first.")

        results = self.vector_store.similarity_search_with_score(query, k=k)
        return results

    def get_retriever(self, k: int = Config.TOP_K_RESULTS):
        """
        Get a retriever interface for the vector store.

        Args:
            k: Number of results to return

        Returns:
            LangChain retriever
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Load or create one first.")

        return self.vector_store.as_retriever(search_kwargs={"k": k})
