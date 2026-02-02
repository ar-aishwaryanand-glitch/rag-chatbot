"""Configuration management for RAG Agent POC."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Config:
    """Configuration settings for the RAG system."""

    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Optional, for embeddings

    # LLM Provider Configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

    # Groq Configuration
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Google Gemini Configuration (fallback)
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

    # Embedding Configuration
    EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "huggingface").lower()
    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    # Chunking Configuration
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

    # Retrieval Configuration
    TOP_K_RESULTS = 3  # Number of chunks to retrieve

    # Vector Store Configuration
    VECTOR_STORE_PATH = Path(__file__).parent.parent / "data" / "vector_store"

    # LLM Configuration
    LLM_MODEL = GROQ_MODEL if LLM_PROVIDER == "groq" else GEMINI_MODEL
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        if cls.LLM_PROVIDER == "groq":
            if not cls.GROQ_API_KEY:
                raise ValueError(
                    "GROQ_API_KEY not found in environment variables. "
                    "Please set it in your .env file or get one from https://console.groq.com"
                )
        elif cls.LLM_PROVIDER == "google":
            if not cls.GOOGLE_API_KEY:
                raise ValueError(
                    "GOOGLE_API_KEY not found in environment variables. "
                    "Please set it in your .env file."
                )

        # Validate embedding provider
        if cls.EMBEDDING_PROVIDER == "google" and not cls.GOOGLE_API_KEY:
            print("⚠️  Warning: Google embeddings selected but no GOOGLE_API_KEY found.")
            print("   Falling back to HuggingFace embeddings.")
            cls.EMBEDDING_PROVIDER = "huggingface"
            cls.EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

        return True

    @classmethod
    def get_llm_display_name(cls):
        """Get a human-readable name for the current LLM."""
        if cls.LLM_PROVIDER == "groq":
            return f"Groq ({cls.GROQ_MODEL})"
        elif cls.LLM_PROVIDER == "google":
            return f"Google Gemini ({cls.GEMINI_MODEL})"
        return cls.LLM_PROVIDER

    @classmethod
    def get_embedding_display_name(cls):
        """Get a human-readable name for the current embedding provider."""
        if cls.EMBEDDING_PROVIDER == "huggingface":
            return f"HuggingFace ({cls.EMBEDDING_MODEL})"
        elif cls.EMBEDDING_PROVIDER == "google":
            return f"Google ({cls.EMBEDDING_MODEL})"
        return cls.EMBEDDING_PROVIDER

# Validate configuration on import
Config.validate()
