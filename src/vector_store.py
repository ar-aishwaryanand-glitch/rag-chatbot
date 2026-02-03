"""FAISS vector store management for RAG Agent POC."""

import time
from typing import List, Optional
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from .config import Config
from .embeddings import EmbeddingManager

class VectorStoreManager:
    """Manages FAISS vector store operations."""

    def __init__(self, embedding_manager: EmbeddingManager):
        """
        Initialize the vector store manager.

        Args:
            embedding_manager: Instance of EmbeddingManager
        """
        self.embedding_manager = embedding_manager
        self.vector_store: Optional[FAISS] = None
        self.store_path = Config.VECTOR_STORE_PATH

        # Automatically load vector store from disk if it exists
        if self.store_path.exists():
            try:
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

    def create_vector_store(self, chunks: List[Document], batch_size: int = 3, delay: float = 2.0) -> FAISS:
        """
        Create a new FAISS vector store from document chunks with rate limiting.

        Args:
            chunks: List of LangChain Document objects
            batch_size: Number of chunks to process at once (default: 3)
            delay: Delay in seconds between batches (default: 2.0)

        Returns:
            FAISS vector store instance
        """
        print(f"Creating vector store with {len(chunks)} chunks...")
        print(f"Processing in batches of {batch_size} with {delay}s delay to avoid rate limits...")

        # Process first batch to create initial vector store
        first_batch = chunks[:batch_size]
        print(f"\n[Batch 1/{(len(chunks)-1)//batch_size + 1}] Processing {len(first_batch)} chunks...")

        self.vector_store = FAISS.from_documents(
            documents=first_batch,
            embedding=self.embedding_manager.embedding_model
        )
        print(f"✓ Batch 1 completed")

        # Process remaining chunks in batches
        for i in range(batch_size, len(chunks), batch_size):
            batch_num = (i // batch_size) + 1
            total_batches = (len(chunks)-1)//batch_size + 1

            # Add delay before next batch
            if i > batch_size:
                print(f"⏳ Waiting {delay}s before next batch...")
                time.sleep(delay)

            batch = chunks[i:i + batch_size]
            print(f"\n[Batch {batch_num}/{total_batches}] Processing {len(batch)} chunks...")

            # Add documents to existing vector store
            self.vector_store.add_documents(batch)
            print(f"✓ Batch {batch_num} completed")

        print("\n✅ Vector store created successfully")
        return self.vector_store

    def save_vector_store(self) -> None:
        """Save the vector store to disk."""
        if self.vector_store is None:
            raise ValueError("No vector store to save. Create one first.")

        # Create directory if it doesn't exist
        self.store_path.mkdir(parents=True, exist_ok=True)

        # Save the vector store
        self.vector_store.save_local(str(self.store_path))
        print(f"Vector store saved to {self.store_path}")

    def load_vector_store(self) -> FAISS:
        """
        Load vector store from disk.

        Returns:
            Loaded FAISS vector store

        Raises:
            FileNotFoundError: If vector store doesn't exist
        """
        if not self.store_path.exists():
            raise FileNotFoundError(
                f"Vector store not found at {self.store_path}. "
                "Create one first using create_vector_store()."
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
