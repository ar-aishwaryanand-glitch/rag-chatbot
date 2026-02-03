"""System initialization functions for RAG agent.

This module provides initialization functions that were previously in src/main.py
"""

from src.document_manager import get_document_manager
from src.rag_chain import RAGChain
from typing import Optional


def initialize_system(rebuild_index: bool = False, use_documents: bool = True) -> RAGChain:
    """
    Initialize the RAG system with document manager and RAG chain.

    Args:
        rebuild_index: Whether to rebuild the vector store index
        use_documents: Whether to use custom documents (True) or sample data (False)

    Returns:
        Initialized RAGChain instance
    """
    # Get document manager
    doc_manager = get_document_manager()

    # Rebuild index if requested
    if rebuild_index:
        # This will rebuild the vector store
        # The DocumentManager handles this internally when documents are loaded
        pass

    # Create and return RAG chain
    rag_chain = RAGChain(doc_manager)

    return rag_chain
