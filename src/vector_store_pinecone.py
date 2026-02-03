"""Pinecone vector store management for RAG Agent POC."""

import time
from typing import List, Optional, Dict, Any
from pathlib import Path
from langchain_core.documents import Document

from .config import Config
from .embeddings import EmbeddingManager


class PineconeVectorStoreManager:
    """Manages Pinecone vector store operations."""

    def __init__(
        self,
        embedding_manager: EmbeddingManager,
        index_name: Optional[str] = None,
        namespace: Optional[str] = None
    ):
        """
        Initialize the Pinecone vector store manager.

        Args:
            embedding_manager: Instance of EmbeddingManager
            index_name: Name of the Pinecone index (from config if not provided)
            namespace: Optional namespace for organizing vectors
        """
        self.embedding_manager = embedding_manager
        self.index_name = index_name or Config.PINECONE_INDEX_NAME
        self.namespace = namespace or Config.PINECONE_NAMESPACE
        self.vector_store = None
        self._index = None

        # Initialize Pinecone
        self._initialize_pinecone()

    def _initialize_pinecone(self):
        """Initialize Pinecone client and check/create index."""
        try:
            from pinecone import Pinecone, ServerlessSpec
            from langchain_pinecone import PineconeVectorStore

            # Initialize Pinecone
            pc = Pinecone(api_key=Config.PINECONE_API_KEY)

            # Get embedding dimension
            sample_embedding = self.embedding_manager.embedding_model.embed_query("test")
            dimension = len(sample_embedding)

            # Check if index exists
            existing_indexes = [index.name for index in pc.list_indexes()]

            if self.index_name not in existing_indexes:
                print(f"📦 Creating new Pinecone index: {self.index_name}")
                print(f"   Dimension: {dimension}")
                print(f"   This may take 30-60 seconds...")

                # Create index with serverless spec
                pc.create_index(
                    name=self.index_name,
                    dimension=dimension,
                    metric=Config.PINECONE_METRIC,
                    spec=ServerlessSpec(
                        cloud=Config.PINECONE_CLOUD,
                        region=Config.PINECONE_REGION
                    )
                )

                # Wait for index to be ready
                import time
                while not pc.describe_index(self.index_name).status['ready']:
                    time.sleep(1)

                print(f"✅ Index {self.index_name} created successfully")
            else:
                print(f"📦 Using existing Pinecone index: {self.index_name}")

            # Get index
            self._index = pc.Index(self.index_name)

            # Initialize vector store
            self.vector_store = PineconeVectorStore(
                index=self._index,
                embedding=self.embedding_manager.embedding_model,
                namespace=self.namespace
            )

            print(f"✅ Pinecone vector store initialized")

        except ImportError:
            print("❌ Pinecone package not installed. Run: pip install pinecone-client langchain-pinecone")
            raise
        except Exception as e:
            print(f"❌ Failed to initialize Pinecone: {e}")
            raise

    def add_documents(
        self,
        documents: List[Document],
        batch_size: int = 100,
        show_progress: bool = True
    ) -> List[str]:
        """
        Add documents to Pinecone vector store.

        Args:
            documents: List of LangChain Document objects
            batch_size: Number of documents to process at once
            show_progress: Whether to show progress updates

        Returns:
            List of document IDs
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized")

        print(f"📤 Adding {len(documents)} documents to Pinecone...")

        all_ids = []

        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(documents) - 1) // batch_size + 1

            if show_progress:
                print(f"   Batch {batch_num}/{total_batches}: Processing {len(batch)} documents...")

            # Add to Pinecone
            ids = self.vector_store.add_documents(batch)
            all_ids.extend(ids)

            if show_progress:
                print(f"   ✓ Batch {batch_num} completed")

        print(f"✅ Added {len(all_ids)} documents to Pinecone")
        return all_ids

    def similarity_search(
        self,
        query: str,
        k: int = None,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Search for similar documents using the query.

        Args:
            query: Search query
            k: Number of results to return (uses Config.TOP_K_RESULTS if not specified)
            filter: Optional metadata filter

        Returns:
            List of similar Document objects
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized")

        k = k or Config.TOP_K_RESULTS

        results = self.vector_store.similarity_search(
            query,
            k=k,
            filter=filter,
            namespace=self.namespace
        )
        return results

    def similarity_search_with_score(
        self,
        query: str,
        k: int = None,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple]:
        """
        Search for similar documents with similarity scores.

        Args:
            query: Search query
            k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of (Document, score) tuples
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized")

        k = k or Config.TOP_K_RESULTS

        results = self.vector_store.similarity_search_with_score(
            query,
            k=k,
            filter=filter,
            namespace=self.namespace
        )
        return results

    def delete_by_filter(self, filter: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete vectors by metadata filter.

        Args:
            filter: Metadata filter (e.g., {"source": "document.pdf"})

        Returns:
            Delete operation response
        """
        if not self._index:
            raise ValueError("Index not initialized")

        print(f"🗑️  Deleting vectors with filter: {filter}")

        response = self._index.delete(
            filter=filter,
            namespace=self.namespace
        )

        print(f"✅ Vectors deleted")
        return response

    def delete_all(self) -> Dict[str, Any]:
        """
        Delete all vectors in the namespace.

        Returns:
            Delete operation response
        """
        if not self._index:
            raise ValueError("Index not initialized")

        print(f"🗑️  Deleting all vectors in namespace: {self.namespace or 'default'}")

        response = self._index.delete(
            delete_all=True,
            namespace=self.namespace
        )

        print(f"✅ All vectors deleted")
        return response

    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Pinecone index.

        Returns:
            Index statistics including vector count, dimension, etc.
        """
        if not self._index:
            raise ValueError("Index not initialized")

        stats = self._index.describe_index_stats()
        return stats

    def list_namespaces(self) -> List[str]:
        """
        List all namespaces in the index.

        Returns:
            List of namespace names
        """
        if not self._index:
            raise ValueError("Index not initialized")

        stats = self._index.describe_index_stats()
        namespaces = list(stats.get('namespaces', {}).keys())
        return namespaces

    def get_retriever(self, k: int = None, filter: Optional[Dict[str, Any]] = None):
        """
        Get a retriever interface for the vector store.

        Args:
            k: Number of results to return
            filter: Optional metadata filter

        Returns:
            LangChain retriever
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized")

        k = k or Config.TOP_K_RESULTS

        search_kwargs = {
            "k": k,
            "namespace": self.namespace
        }

        if filter:
            search_kwargs["filter"] = filter

        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

    def upsert_documents(
        self,
        documents: List[Document],
        batch_size: int = 100
    ) -> List[str]:
        """
        Upsert documents (update if exists, insert if not).

        Args:
            documents: List of LangChain Document objects
            batch_size: Batch size for processing

        Returns:
            List of document IDs
        """
        # For Pinecone, add_documents does upsert by default
        return self.add_documents(documents, batch_size=batch_size)

    def hybrid_search(
        self,
        query: str,
        k: int = None,
        alpha: float = 0.5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Perform hybrid search (dense + sparse vectors).
        Note: Requires Pinecone to be configured with hybrid search support.

        Args:
            query: Search query
            k: Number of results
            alpha: Balance between dense (1.0) and sparse (0.0) search
            filter: Optional metadata filter

        Returns:
            List of documents
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized")

        k = k or Config.TOP_K_RESULTS

        # This is a placeholder - full hybrid search requires additional setup
        # For now, fall back to similarity search
        print("⚠️  Hybrid search not fully implemented, using similarity search")
        return self.similarity_search(query, k=k, filter=filter)

    def is_available(self) -> bool:
        """Check if Pinecone is properly configured and available."""
        return self.vector_store is not None and self._index is not None
