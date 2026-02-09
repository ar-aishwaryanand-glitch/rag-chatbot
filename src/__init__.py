"""RAG Agent POC - A retrieval-augmented generation system with agentic capabilities.

This package provides:
- Document loading and management
- Vector store backends (FAISS, Pinecone)
- Embedding generation
- RAG chain for question answering
- Agentic execution with tool use
- Policy engine for access control
- Task queue for background processing
"""

__version__ = "0.1.0"

# Core configuration
from .config import Config
from .logging_config import get_logger

# Document handling
from .document_loader import load_all_documents, load_text_files, load_pdfs
from .document_manager import DocumentManager
from .embeddings import EmbeddingManager

# Vector stores
from .vector_store import VectorStoreManager

# RAG chain
from .rag_chain import RAGChain

__all__ = [
    # Version
    "__version__",
    # Config
    "Config",
    "get_logger",
    # Documents
    "load_all_documents",
    "load_text_files",
    "load_pdfs",
    "DocumentManager",
    "EmbeddingManager",
    # Vector store
    "VectorStoreManager",
    # RAG
    "RAGChain",
]
