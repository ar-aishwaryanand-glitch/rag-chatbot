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

    # Vector Store Backend Selection
    USE_PINECONE = os.getenv("USE_PINECONE", "false").lower() == "true"

    # Pinecone Configuration (Optional - for production vector database)
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")  # Deprecated, use cloud/region
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "rag-agent")
    PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "")  # Empty string = default namespace
    PINECONE_METRIC = os.getenv("PINECONE_METRIC", "cosine")  # cosine, euclidean, dotproduct
    PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")  # aws, gcp, azure
    PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")  # Region for serverless

    # LLM Configuration
    LLM_MODEL = GROQ_MODEL if LLM_PROVIDER == "groq" else GEMINI_MODEL
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

    # ===== AGENT CONFIGURATION =====

    # Agent Mode
    AGENT_ENABLED = os.getenv("AGENT_ENABLED", "true").lower() == "true"
    AGENT_MODE = os.getenv("AGENT_MODE", "hybrid")  # react, plan-execute, hybrid
    AGENT_MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "10"))
    AGENT_TIMEOUT = int(os.getenv("AGENT_TIMEOUT", "120"))  # seconds
    AGENT_VERBOSE = os.getenv("AGENT_VERBOSE", "true").lower() == "true"

    # Memory Configuration
    MEMORY_ENABLED = os.getenv("MEMORY_ENABLED", "true").lower() == "true"
    MEMORY_WINDOW_SIZE = int(os.getenv("MEMORY_WINDOW_SIZE", "10"))
    MEMORY_SUMMARY_FREQUENCY = int(os.getenv("MEMORY_SUMMARY_FREQUENCY", "5"))
    MEMORY_STORE_PATH = Path(__file__).parent.parent / "data" / "memory_store"

    # Tool Configuration
    WEB_SEARCH_ENABLED = os.getenv("WEB_SEARCH_ENABLED", "true").lower() == "true"
    WEB_SEARCH_PROVIDER = os.getenv("WEB_SEARCH_PROVIDER", "duckduckgo")  # duckduckgo or tavily
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")  # Optional

    CALCULATOR_ENABLED = os.getenv("CALCULATOR_ENABLED", "true").lower() == "true"
    CODE_EXECUTOR_ENABLED = os.getenv("CODE_EXECUTOR_ENABLED", "false").lower() == "true"  # Disabled by default for safety
    FILE_OPS_ENABLED = os.getenv("FILE_OPS_ENABLED", "true").lower() == "true"

    # Safety Settings
    CODE_EXECUTION_TIMEOUT = int(os.getenv("CODE_EXECUTION_TIMEOUT", "5"))
    FILE_OPS_WORKSPACE = Path(__file__).parent.parent / "data" / "workspace"

    # Reflection & Self-Correction
    REFLECTION_ENABLED = os.getenv("REFLECTION_ENABLED", "true").lower() == "true"
    HALLUCINATION_DETECTION = os.getenv("HALLUCINATION_DETECTION", "false").lower() == "true"

    # Streaming
    ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "true").lower() == "true"

    # ===== ADVANCED FEATURES =====

    # PostgreSQL Database (Optional - for persistent session storage)
    USE_POSTGRES = os.getenv("USE_POSTGRES", "false").lower() == "true"
    USE_CHECKPOINTS = os.getenv("USE_CHECKPOINTS", "true").lower() == "true"
    DATABASE_URL = os.getenv("DATABASE_URL")  # Full connection string
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB = os.getenv("POSTGRES_DB", "rag_chatbot")

    # Policy Engine (Optional - for agent behavior control and governance)
    USE_POLICY_ENGINE = os.getenv("USE_POLICY_ENGINE", "true").lower() == "true"

    # Redis Message Queue (Optional - for distributed agent coordination)
    USE_REDIS_QUEUE = os.getenv("USE_REDIS_QUEUE", "false").lower() == "true"
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

    # ===== OBSERVABILITY CONFIGURATION =====

    # OpenTelemetry Settings
    ENABLE_OBSERVABILITY = os.getenv("ENABLE_OBSERVABILITY", "false").lower() == "true"
    OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "rag-agent")
    OTEL_ENVIRONMENT = os.getenv("OTEL_ENVIRONMENT", "development")  # development, staging, production

    # Exporter Configuration
    OTEL_EXPORTER_TYPE = os.getenv("OTEL_EXPORTER_TYPE", "console")  # console, otlp, jaeger
    OTEL_EXPORTER_ENDPOINT = os.getenv("OTEL_EXPORTER_ENDPOINT", "http://localhost:4317")  # OTLP gRPC endpoint
    OTEL_EXPORTER_HEADERS = os.getenv("OTEL_EXPORTER_HEADERS", "")  # Optional headers (e.g., API keys)

    # Jaeger Configuration (if using Jaeger exporter)
    JAEGER_HOST = os.getenv("JAEGER_HOST", "localhost")
    JAEGER_PORT = int(os.getenv("JAEGER_PORT", "6831"))

    # Tracing Configuration
    TRACE_RAG_OPERATIONS = os.getenv("TRACE_RAG_OPERATIONS", "true").lower() == "true"
    TRACE_AGENT_OPERATIONS = os.getenv("TRACE_AGENT_OPERATIONS", "true").lower() == "true"
    TRACE_TOOL_CALLS = os.getenv("TRACE_TOOL_CALLS", "true").lower() == "true"
    TRACE_LLM_CALLS = os.getenv("TRACE_LLM_CALLS", "true").lower() == "true"

    # Metrics Configuration
    COLLECT_METRICS = os.getenv("COLLECT_METRICS", "true").lower() == "true"
    METRIC_EXPORT_INTERVAL = int(os.getenv("METRIC_EXPORT_INTERVAL", "60"))  # seconds

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

    @classmethod
    def get_vector_store_display_name(cls):
        """Get a human-readable name for the current vector store."""
        if cls.USE_PINECONE:
            return f"Pinecone ({cls.PINECONE_INDEX_NAME})"
        return "FAISS (Local)"

# Validate configuration on import
Config.validate()
