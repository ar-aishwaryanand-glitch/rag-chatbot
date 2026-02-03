"""Unified document manager that supports multiple vector store backends."""

from typing import List, Optional, Dict, Any, Literal
from pathlib import Path
from langchain_core.documents import Document

from .config import Config
from .embeddings import EmbeddingManager


VectorStoreType = Literal["faiss", "pinecone"]


class DocumentManager:
    """
    Unified document manager that abstracts vector store operations.

    Supports multiple backends:
    - FAISS (local, file-based)
    - Pinecone (cloud, production-grade)

    Automatically selects backend based on configuration.
    """

    def __init__(
        self,
        embedding_manager: Optional[EmbeddingManager] = None,
        vector_store_type: Optional[VectorStoreType] = None
    ):
        """
        Initialize the document manager.

        Args:
            embedding_manager: EmbeddingManager instance (creates new if not provided)
            vector_store_type: Type of vector store ("faiss" or "pinecone")
                               Auto-detected from config if not specified
        """
        # Initialize embedding manager
        self.embedding_manager = embedding_manager or EmbeddingManager()

        # Determine vector store type
        self.vector_store_type = vector_store_type or self._detect_vector_store_type()

        # Initialize the appropriate backend
        self.backend = self._initialize_backend()

        print(f"📦 Document Manager initialized with {self.vector_store_type.upper()} backend")

    def _detect_vector_store_type(self) -> VectorStoreType:
        """Auto-detect which vector store to use based on configuration."""
        # Check if Pinecone is configured
        if hasattr(Config, 'PINECONE_API_KEY') and Config.PINECONE_API_KEY:
            if hasattr(Config, 'USE_PINECONE') and Config.USE_PINECONE:
                return "pinecone"

        # Default to FAISS
        return "faiss"

    def _initialize_backend(self):
        """Initialize the vector store backend."""
        if self.vector_store_type == "pinecone":
            from .vector_store_pinecone import PineconeVectorStoreManager
            return PineconeVectorStoreManager(self.embedding_manager)
        else:
            from .vector_store import VectorStoreManager
            return VectorStoreManager(self.embedding_manager)

    # ===== Document Operations =====

    def add_documents(
        self,
        documents: List[Document],
        batch_size: int = None,
        show_progress: bool = True
    ) -> Optional[List[str]]:
        """
        Add documents to the vector store.

        Args:
            documents: List of LangChain Document objects
            batch_size: Batch size for processing (backend-specific defaults used if None)
            show_progress: Whether to show progress

        Returns:
            List of document IDs (Pinecone) or None (FAISS)
        """
        if self.vector_store_type == "pinecone":
            batch_size = batch_size or 100
            return self.backend.add_documents(
                documents,
                batch_size=batch_size,
                show_progress=show_progress
            )
        else:
            # FAISS create_vector_store
            batch_size = batch_size or 3
            delay = 2.0 if show_progress else 0
            self.backend.create_vector_store(
                documents,
                batch_size=batch_size,
                delay=delay
            )
            return None

    def create_from_documents(
        self,
        documents: List[Document],
        **kwargs
    ):
        """
        Create a new vector store from documents.
        Alias for add_documents for consistency.

        Args:
            documents: List of documents
            **kwargs: Additional arguments passed to add_documents
        """
        return self.add_documents(documents, **kwargs)

    # ===== Search Operations =====

    def similarity_search(
        self,
        query: str,
        k: int = None,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Search for similar documents.

        Args:
            query: Search query
            k: Number of results (uses Config.TOP_K_RESULTS if not specified)
            filter: Metadata filter (Pinecone only)

        Returns:
            List of similar documents
        """
        k = k or Config.TOP_K_RESULTS

        if self.vector_store_type == "pinecone":
            return self.backend.similarity_search(query, k=k, filter=filter)
        else:
            return self.backend.similarity_search(query, k=k)

    def similarity_search_with_score(
        self,
        query: str,
        k: int = None,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple]:
        """
        Search for similar documents with scores.

        Args:
            query: Search query
            k: Number of results
            filter: Metadata filter (Pinecone only)

        Returns:
            List of (Document, score) tuples
        """
        k = k or Config.TOP_K_RESULTS

        if self.vector_store_type == "pinecone":
            return self.backend.similarity_search_with_score(query, k=k, filter=filter)
        else:
            return self.backend.similarity_search_with_score(query, k=k)

    def get_retriever(self, k: int = None, filter: Optional[Dict[str, Any]] = None):
        """
        Get a retriever interface.

        Args:
            k: Number of results
            filter: Metadata filter (Pinecone only)

        Returns:
            LangChain retriever
        """
        k = k or Config.TOP_K_RESULTS

        if self.vector_store_type == "pinecone":
            return self.backend.get_retriever(k=k, filter=filter)
        else:
            return self.backend.get_retriever(k=k)

    # ===== Persistence Operations =====

    def save(self, path: Optional[Path] = None):
        """
        Save vector store (FAISS only).

        Args:
            path: Path to save (uses Config.VECTOR_STORE_PATH if not specified)
        """
        if self.vector_store_type == "faiss":
            if path:
                original_path = self.backend.store_path
                self.backend.store_path = path
                self.backend.save_vector_store()
                self.backend.store_path = original_path
            else:
                self.backend.save_vector_store()
        else:
            print("⚠️  Save not applicable for Pinecone (data is persisted automatically)")

    def load(self, path: Optional[Path] = None):
        """
        Load vector store (FAISS only).

        Args:
            path: Path to load from (uses Config.VECTOR_STORE_PATH if not specified)
        """
        if self.vector_store_type == "faiss":
            if path:
                original_path = self.backend.store_path
                self.backend.store_path = path
                self.backend.load_vector_store()
                self.backend.store_path = original_path
            else:
                self.backend.load_vector_store()
        else:
            print("⚠️  Load not applicable for Pinecone (data is always available)")

    # ===== Management Operations =====

    def delete_by_filter(self, filter: Dict[str, Any]):
        """
        Delete documents by metadata filter (Pinecone only).

        Args:
            filter: Metadata filter (e.g., {"source": "document.pdf"})
        """
        if self.vector_store_type == "pinecone":
            return self.backend.delete_by_filter(filter)
        else:
            print("⚠️  Delete by filter not supported for FAISS")
            print("   Tip: Recreate the vector store without unwanted documents")

    def delete_all(self):
        """Delete all documents (Pinecone only)."""
        if self.vector_store_type == "pinecone":
            return self.backend.delete_all()
        else:
            print("⚠️  Delete all not supported for FAISS")
            print("   Tip: Delete the vector store directory to start fresh")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get vector store statistics.

        Returns:
            Dictionary with statistics
        """
        if self.vector_store_type == "pinecone":
            stats = self.backend.get_index_stats()

            # Format stats nicely
            formatted_stats = {
                "backend": "pinecone",
                "index_name": self.backend.index_name,
                "namespace": self.backend.namespace or "default",
                "total_vectors": stats.get('total_vector_count', 0),
                "dimension": stats.get('dimension', 'unknown'),
                "namespaces": stats.get('namespaces', {})
            }

            return formatted_stats
        else:
            # FAISS stats
            if self.backend.vector_store:
                index = self.backend.vector_store.index
                return {
                    "backend": "faiss",
                    "total_vectors": index.ntotal,
                    "dimension": index.d if hasattr(index, 'd') else 'unknown',
                    "index_type": "FAISS"
                }
            else:
                return {
                    "backend": "faiss",
                    "status": "not initialized"
                }

    def list_namespaces(self) -> List[str]:
        """
        List all namespaces (Pinecone only).

        Returns:
            List of namespace names
        """
        if self.vector_store_type == "pinecone":
            return self.backend.list_namespaces()
        else:
            return ["default"]

    def is_available(self) -> bool:
        """Check if vector store is available and ready."""
        if self.vector_store_type == "pinecone":
            return self.backend.is_available()
        else:
            return self.backend.vector_store is not None

    # ===== Backend Access =====

    @property
    def vector_store(self):
        """Get the underlying vector store object."""
        return self.backend.vector_store

    def get_backend_type(self) -> VectorStoreType:
        """Get the current backend type."""
        return self.vector_store_type


# ===== Factory Functions =====

def get_document_manager(
    vector_store_type: Optional[VectorStoreType] = None,
    embedding_manager: Optional[EmbeddingManager] = None
) -> DocumentManager:
    """
    Factory function to get a document manager instance.

    Args:
        vector_store_type: Type of vector store ("faiss" or "pinecone")
        embedding_manager: Optional embedding manager instance

    Returns:
        DocumentManager instance
    """
    return DocumentManager(
        embedding_manager=embedding_manager,
        vector_store_type=vector_store_type
    )
