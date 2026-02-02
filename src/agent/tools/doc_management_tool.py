"""Document management tool for RAG system."""

from typing import TYPE_CHECKING
from .base_tool import BaseTool

if TYPE_CHECKING:
    from src.vector_store import VectorStoreManager


class DocumentManagementTool(BaseTool):
    """
    Tool for managing and inspecting the document collection.

    Provides information about indexed documents, vector store statistics,
    and document metadata.
    """

    def __init__(self, vector_store_manager: 'VectorStoreManager'):
        """
        Initialize document management tool.

        Args:
            vector_store_manager: Vector store manager instance
        """
        super().__init__()
        self.vector_store = vector_store_manager

    @property
    def name(self) -> str:
        return "document_manager"

    @property
    def description(self) -> str:
        return """Manage and inspect the document collection. \
Available actions: 'stats' (get vector store statistics), 'list' (list indexed documents), \
'info' (get information about the document collection). \
Use for understanding what documents are available or checking indexing status."""

    def _run(self, action: str, doc_name: str = None) -> str:
        """
        Execute document management action.

        Args:
            action: Action to perform (stats, list, info)
            doc_name: Optional document name for specific queries

        Returns:
            Result of action or error message
        """
        action = action.lower().strip()

        try:
            if action == "stats":
                return self._get_stats()
            elif action == "list":
                return self._list_documents()
            elif action == "info":
                return self._get_info()
            else:
                return f"Error: Unknown action '{action}'. Use: stats, list, or info"

        except Exception as e:
            return f"Document management error: {str(e)}"

    def _get_stats(self) -> str:
        """Get vector store statistics."""
        try:
            # Get vector store
            vectorstore = self.vector_store.vectorstore

            if not vectorstore:
                return "Vector store not initialized"

            # Get FAISS index info
            index = vectorstore.index
            num_vectors = index.ntotal

            return f"""Vector Store Statistics:
- Total vectors: {num_vectors}
- Index type: FAISS
- Status: Active
- Embedding dimension: {index.d if hasattr(index, 'd') else 'Unknown'}"""

        except AttributeError:
            return "Vector store statistics not available"

    def _list_documents(self) -> str:
        """List indexed documents (approximation)."""
        try:
            # Get all documents from vector store
            # Note: FAISS doesn't store metadata easily, so this is a workaround
            vectorstore = self.vector_store.vectorstore

            if not vectorstore:
                return "Vector store not initialized"

            # Get a sample to infer document sources
            # This is an approximation - real implementation would need metadata tracking
            sample_docs = vectorstore.similarity_search("", k=100)

            # Extract unique sources
            sources = set()
            for doc in sample_docs:
                source = doc.metadata.get('source', 'unknown')
                sources.add(source)

            if not sources:
                return "No documents found"

            lines = ["Indexed documents:\n"]
            for i, source in enumerate(sorted(sources), 1):
                lines.append(f"  {i}. {source}")

            return "\n".join(lines)

        except Exception as e:
            return f"Cannot list documents: {str(e)}"

    def _get_info(self) -> str:
        """Get general information about document collection."""
        stats = self._get_stats()
        docs = self._list_documents()

        return f"""{stats}

{docs}

Note: Use 'document_search' tool to query the actual content of these documents."""
