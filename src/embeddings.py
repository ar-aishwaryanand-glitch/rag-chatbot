"""Text chunking and embedding generation for RAG Agent POC."""

from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from .config import Config

class EmbeddingManager:
    """Manages text chunking and embedding generation."""

    def __init__(self):
        """Initialize the embedding manager."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

        # Initialize embedding model based on provider
        self.embedding_model = self._initialize_embedding_model()

    def _initialize_embedding_model(self):
        """Initialize the appropriate embedding model based on configuration."""
        if Config.EMBEDDING_PROVIDER == "huggingface":
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
                print(f"📦 Loading HuggingFace embeddings: {Config.EMBEDDING_MODEL}")
                return HuggingFaceEmbeddings(
                    model_name=Config.EMBEDDING_MODEL,
                    model_kwargs={'device': 'cpu'},  # Use CPU for compatibility
                    encode_kwargs={'normalize_embeddings': True}
                )
            except ImportError as e:
                print(f"⚠️  Warning: Could not load HuggingFace embeddings: {e}")
                print("   Installing required packages...")
                import subprocess
                subprocess.run(["pip", "install", "sentence-transformers", "-q"])
                from langchain_huggingface import HuggingFaceEmbeddings
                return HuggingFaceEmbeddings(
                    model_name=Config.EMBEDDING_MODEL,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )

        elif Config.EMBEDDING_PROVIDER == "google":
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            print(f"📦 Using Google embeddings: {Config.EMBEDDING_MODEL}")
            return GoogleGenerativeAIEmbeddings(
                model=Config.EMBEDDING_MODEL,
                google_api_key=Config.GOOGLE_API_KEY
            )

        else:
            raise ValueError(
                f"Unsupported embedding provider: {Config.EMBEDDING_PROVIDER}. "
                "Supported providers: huggingface, google"
            )

    def chunk_documents(self, documents: List[dict]) -> List[Document]:
        """
        Split documents into smaller chunks.

        Args:
            documents: List of document dictionaries with 'content' and 'metadata'

        Returns:
            List of LangChain Document objects (chunks)
        """
        langchain_docs = []

        for doc in documents:
            # Create LangChain Document
            langchain_doc = Document(
                page_content=doc["content"].strip(),
                metadata=doc["metadata"]
            )
            langchain_docs.append(langchain_doc)

        # Split documents into chunks
        chunks = self.text_splitter.split_documents(langchain_docs)

        # Add chunk index to metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = i

        print(f"✂️  Split {len(documents)} documents into {len(chunks)} chunks")
        return chunks

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        embeddings = self.embedding_model.embed_documents(texts)
        print(f"🔢 Generated embeddings for {len(texts)} texts")
        return embeddings

    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a single query.

        Args:
            query: Query text

        Returns:
            Embedding vector for the query
        """
        embedding = self.embedding_model.embed_query(query)
        return embedding
