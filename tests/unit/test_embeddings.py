"""
Unit tests for embeddings module.

Tests cover:
- EmbeddingManager initialization
- Document chunking
- Embedding generation
"""

import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document


class TestEmbeddingManagerImport:
    """Tests for EmbeddingManager imports."""

    def test_embedding_manager_import(self):
        """Test that EmbeddingManager can be imported."""
        from src.embeddings import EmbeddingManager
        assert EmbeddingManager is not None

    def test_cached_embedding_function_import(self):
        """Test that cached embedding function exists."""
        from src.embeddings import _get_cached_embedding_model
        assert _get_cached_embedding_model is not None


class TestEmbeddingManagerChunking:
    """Tests for document chunking functionality."""

    @patch('src.embeddings._get_cached_embedding_model')
    def test_chunk_documents_basic(self, mock_get_model):
        """Test basic document chunking."""
        from src.embeddings import EmbeddingManager

        mock_get_model.return_value = MagicMock()

        manager = EmbeddingManager()

        documents = [
            {"content": "This is a test document with some content.", "metadata": {"source": "test.md"}}
        ]

        chunks = manager.chunk_documents(documents)

        assert len(chunks) >= 1
        assert isinstance(chunks[0], Document)
        assert chunks[0].metadata["source"] == "test.md"

    @patch('src.embeddings._get_cached_embedding_model')
    def test_chunk_documents_preserves_metadata(self, mock_get_model):
        """Test that metadata is preserved during chunking."""
        from src.embeddings import EmbeddingManager

        mock_get_model.return_value = MagicMock()

        manager = EmbeddingManager()

        documents = [
            {
                "content": "Test content here.",
                "metadata": {"source": "file.md", "topic": "testing", "author": "test"}
            }
        ]

        chunks = manager.chunk_documents(documents)

        assert chunks[0].metadata["source"] == "file.md"
        assert chunks[0].metadata["topic"] == "testing"
        assert chunks[0].metadata["author"] == "test"

    @patch('src.embeddings._get_cached_embedding_model')
    def test_chunk_documents_adds_chunk_id(self, mock_get_model):
        """Test that chunk_id is added to metadata."""
        from src.embeddings import EmbeddingManager

        mock_get_model.return_value = MagicMock()

        manager = EmbeddingManager()

        # Create a longer document that will be split
        long_content = "This is a test. " * 500  # ~8000 chars
        documents = [
            {"content": long_content, "metadata": {"source": "long.md"}}
        ]

        chunks = manager.chunk_documents(documents)

        # Should have multiple chunks
        assert len(chunks) > 1
        # Each chunk should have a chunk_id
        for i, chunk in enumerate(chunks):
            assert "chunk_id" in chunk.metadata
            assert chunk.metadata["chunk_id"] == i

    @patch('src.embeddings._get_cached_embedding_model')
    def test_chunk_documents_empty_list(self, mock_get_model):
        """Test chunking with empty document list."""
        from src.embeddings import EmbeddingManager

        mock_get_model.return_value = MagicMock()

        manager = EmbeddingManager()
        chunks = manager.chunk_documents([])

        assert chunks == []

    @patch('src.embeddings._get_cached_embedding_model')
    def test_chunk_documents_strips_whitespace(self, mock_get_model):
        """Test that content whitespace is stripped."""
        from src.embeddings import EmbeddingManager

        mock_get_model.return_value = MagicMock()

        manager = EmbeddingManager()

        documents = [
            {"content": "   Content with whitespace   \n\n", "metadata": {"source": "test.md"}}
        ]

        chunks = manager.chunk_documents(documents)

        assert chunks[0].page_content == "Content with whitespace"


class TestEmbeddingManagerGeneration:
    """Tests for embedding generation."""

    @patch('src.embeddings._get_cached_embedding_model')
    def test_generate_embeddings(self, mock_get_model):
        """Test embedding generation for documents."""
        from src.embeddings import EmbeddingManager

        mock_model = MagicMock()
        mock_model.embed_documents.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_get_model.return_value = mock_model

        manager = EmbeddingManager()
        embeddings = manager.generate_embeddings(["text1", "text2"])

        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3]
        mock_model.embed_documents.assert_called_once_with(["text1", "text2"])

    @patch('src.embeddings._get_cached_embedding_model')
    def test_generate_query_embedding(self, mock_get_model):
        """Test query embedding generation."""
        from src.embeddings import EmbeddingManager

        mock_model = MagicMock()
        mock_model.embed_query.return_value = [0.1, 0.2, 0.3]
        mock_get_model.return_value = mock_model

        manager = EmbeddingManager()
        embedding = manager.generate_query_embedding("test query")

        assert embedding == [0.1, 0.2, 0.3]
        mock_model.embed_query.assert_called_once_with("test query")


class TestCachedEmbeddingModel:
    """Tests for cached embedding model loading."""

    def test_unsupported_provider_raises_error(self):
        """Test that unsupported provider raises ValueError."""
        from src.embeddings import _get_cached_embedding_model

        # Clear the cache first
        _get_cached_embedding_model.cache_clear()

        with pytest.raises(ValueError) as exc_info:
            _get_cached_embedding_model("unsupported_provider", "model")

        assert "Unsupported embedding provider" in str(exc_info.value)

    def test_huggingface_provider_code_path(self):
        """Test HuggingFace provider is recognized as valid."""
        from src.embeddings import _get_cached_embedding_model

        _get_cached_embedding_model.cache_clear()

        # Mock the entire langchain_huggingface module
        mock_hf_embeddings = MagicMock()
        with patch.dict('sys.modules', {'langchain_huggingface': MagicMock(HuggingFaceEmbeddings=mock_hf_embeddings)}):
            # Patch at the point where it's imported inside the function
            with patch('langchain_huggingface.HuggingFaceEmbeddings', mock_hf_embeddings):
                mock_hf_embeddings.return_value = MagicMock()
                result = _get_cached_embedding_model("huggingface", "test-model")
                assert result is not None


class TestTextSplitterConfiguration:
    """Tests for text splitter configuration."""

    @patch('src.embeddings._get_cached_embedding_model')
    @patch('src.embeddings.Config')
    def test_text_splitter_uses_config_values(self, mock_config, mock_get_model):
        """Test that text splitter uses Config values."""
        from src.embeddings import EmbeddingManager

        mock_config.CHUNK_SIZE = 500
        mock_config.CHUNK_OVERLAP = 50
        mock_config.EMBEDDING_PROVIDER = "huggingface"
        mock_config.EMBEDDING_MODEL = "test-model"

        mock_get_model.return_value = MagicMock()

        manager = EmbeddingManager()

        assert manager.text_splitter._chunk_size == 500
        assert manager.text_splitter._chunk_overlap == 50
