"""Document management tool for RAG system."""

from typing import TYPE_CHECKING, Union
from .base_tool import BaseTool

if TYPE_CHECKING:
    from src.vector_store import VectorStoreManager
    from src.document_manager import DocumentManager


class DocumentManagementTool(BaseTool):
    """
    Tool for managing and inspecting the document collection.

    Provides information about indexed documents, vector store statistics,
    and document metadata.

    Supports both FAISS (VectorStoreManager) and Pinecone (DocumentManager) backends.
    """

    def __init__(self, vector_store_manager: Union['VectorStoreManager', 'DocumentManager']):
        """
        Initialize document management tool.

        Args:
            vector_store_manager: Vector store manager or document manager instance
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
            # Check if using DocumentManager (unified interface)
            if hasattr(self.vector_store, 'get_stats'):
                # DocumentManager
                stats = self.vector_store.get_stats()

                if stats.get('backend') == 'pinecone':
                    return f"""Vector Store Statistics:
- Backend: Pinecone (Cloud)
- Total vectors: {stats['total_vectors']}
- Index: {stats['index_name']}
- Namespace: {stats['namespace']}
- Dimension: {stats['dimension']}
- Status: Active"""
                else:
                    return f"""Vector Store Statistics:
- Backend: FAISS (Local)
- Total vectors: {stats.get('total_vectors', 'unknown')}
- Dimension: {stats.get('dimension', 'unknown')}
- Status: {stats.get('status', 'active')}"""

            # Legacy VectorStoreManager (FAISS)
            vectorstore = self.vector_store.vector_store

            if not vectorstore:
                return "Vector store not initialized"

            # Get FAISS index info
            index = vectorstore.index
            num_vectors = index.ntotal

            return f"""Vector Store Statistics:
- Backend: FAISS (Local)
- Total vectors: {num_vectors}
- Status: Active
- Embedding dimension: {index.d if hasattr(index, 'd') else 'Unknown'}"""

        except Exception as e:
            return f"Vector store statistics not available: {str(e)}"

    def _list_documents(self) -> str:
        """List indexed documents."""
        try:
            # Get vector store
            vectorstore = self.vector_store.vector_store

            if not vectorstore:
                return "Vector store not initialized"

            # Get a sample to infer document sources
            # Note: This queries for empty string to get any docs
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
