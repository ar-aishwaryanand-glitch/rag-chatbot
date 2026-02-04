"""
Unit tests for vector store module.

Tests cover:
- VectorStoreManager initialization
- Vector store creation
- Similarity search
- Save/load operations
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from langchain_core.documents import Document


class TestVectorStoreManagerImport:
    """Tests for VectorStoreManager imports."""

    def test_vector_store_manager_import(self):
        """Test that VectorStoreManager can be imported."""
        from src.vector_store import VectorStoreManager
        assert VectorStoreManager is not None


class TestVectorStoreManagerInit:
    """Tests for VectorStoreManager initialization."""

    @patch('src.vector_store.Config')
    def test_init_with_no_existing_store(self, mock_config):
        """Test initialization when no vector store exists."""
        from src.vector_store import VectorStoreManager

        mock_config.VECTOR_STORE_PATH = Path("/nonexistent/path")

        mock_embedding_manager = MagicMock()

        manager = VectorStoreManager(mock_embedding_manager)

        assert manager.embedding_manager == mock_embedding_manager
        assert manager.vector_store is None

    @patch('src.vector_store.FAISS')
    @patch('src.vector_store.Config')
    def test_init_loads_existing_store(self, mock_config, mock_faiss):
        """Test that existing vector store is loaded on init."""
        from src.vector_store import VectorStoreManager

        # Create a temporary path that "exists"
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_config.VECTOR_STORE_PATH = mock_path

        mock_embedding_manager = MagicMock()
        mock_faiss.load_local.return_value = MagicMock()

        manager = VectorStoreManager(mock_embedding_manager)

        mock_faiss.load_local.assert_called_once()
        assert manager.vector_store is not None

    @patch('src.vector_store.FAISS')
    @patch('src.vector_store.Config')
    def test_init_handles_load_error(self, mock_config, mock_faiss):
        """Test that load errors are handled gracefully."""
        from src.vector_store import VectorStoreManager

        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_config.VECTOR_STORE_PATH = mock_path

        mock_embedding_manager = MagicMock()
        mock_faiss.load_local.side_effect = Exception("Load error")

        # Should not raise, just print warning
        manager = VectorStoreManager(mock_embedding_manager)
        assert manager.vector_store is None


class TestVectorStoreCreation:
    """Tests for vector store creation."""

    @patch('src.vector_store.time.sleep')  # Mock sleep to speed up tests
    @patch('src.vector_store.FAISS')
    @patch('src.vector_store.Config')
    def test_create_vector_store_basic(self, mock_config, mock_faiss, mock_sleep):
        """Test basic vector store creation."""
        from src.vector_store import VectorStoreManager

        mock_config.VECTOR_STORE_PATH = Path("/nonexistent/path")

        mock_embedding_manager = MagicMock()
        mock_vs = MagicMock()
        mock_faiss.from_documents.return_value = mock_vs

        manager = VectorStoreManager(mock_embedding_manager)

        chunks = [
            Document(page_content="chunk1", metadata={"source": "test.md"}),
            Document(page_content="chunk2", metadata={"source": "test.md"}),
        ]

        result = manager.create_vector_store(chunks, batch_size=2, delay=0)

        mock_faiss.from_documents.assert_called_once()
        assert result == mock_vs
        assert manager.vector_store == mock_vs

    @patch('src.vector_store.time.sleep')
    @patch('src.vector_store.FAISS')
    @patch('src.vector_store.Config')
    def test_create_vector_store_batched(self, mock_config, mock_faiss, mock_sleep):
        """Test vector store creation with batching."""
        from src.vector_store import VectorStoreManager

        mock_config.VECTOR_STORE_PATH = Path("/nonexistent/path")

        mock_embedding_manager = MagicMock()
        mock_vs = MagicMock()
        mock_faiss.from_documents.return_value = mock_vs

        manager = VectorStoreManager(mock_embedding_manager)

        # Create 5 chunks with batch_size=2
        chunks = [
            Document(page_content=f"chunk{i}", metadata={"source": "test.md"})
            for i in range(5)
        ]

        manager.create_vector_store(chunks, batch_size=2, delay=0.1)  # result intentionally unused

        # First batch creates the store
        mock_faiss.from_documents.assert_called_once()
        # Remaining batches are added
        assert mock_vs.add_documents.call_count == 2  # 2 more batches


class TestVectorStoreSaveLoad:
    """Tests for save/load operations."""

    @patch('src.vector_store.Config')
    def test_save_without_vector_store_raises(self, mock_config):
        """Test that saving without a vector store raises error."""
        from src.vector_store import VectorStoreManager

        mock_config.VECTOR_STORE_PATH = Path("/nonexistent/path")

        mock_embedding_manager = MagicMock()
        manager = VectorStoreManager(mock_embedding_manager)

        with pytest.raises(ValueError) as exc_info:
            manager.save_vector_store()

        assert "No vector store to save" in str(exc_info.value)

    @patch('src.vector_store.Config')
    def test_load_nonexistent_store_raises(self, mock_config):
        """Test that loading nonexistent store raises error."""
        from src.vector_store import VectorStoreManager

        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False
        mock_config.VECTOR_STORE_PATH = mock_path

        mock_embedding_manager = MagicMock()
        manager = VectorStoreManager(mock_embedding_manager)

        with pytest.raises(FileNotFoundError):
            manager.load_vector_store()

    @patch('src.vector_store.FAISS')
    @patch('src.vector_store.Config')
    def test_save_vector_store(self, mock_config, mock_faiss):
        """Test saving vector store to disk."""
        from src.vector_store import VectorStoreManager

        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False
        mock_config.VECTOR_STORE_PATH = mock_path

        mock_embedding_manager = MagicMock()
        manager = VectorStoreManager(mock_embedding_manager)

        # Set up a mock vector store
        manager.vector_store = MagicMock()

        manager.save_vector_store()

        mock_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        manager.vector_store.save_local.assert_called_once()


class TestSimilaritySearch:
    """Tests for similarity search operations."""

    @patch('src.vector_store.Config')
    def test_search_without_store_raises(self, mock_config):
        """Test that search without initialized store raises error."""
        from src.vector_store import VectorStoreManager

        mock_config.VECTOR_STORE_PATH = Path("/nonexistent/path")
        mock_config.TOP_K_RESULTS = 5

        mock_embedding_manager = MagicMock()
        manager = VectorStoreManager(mock_embedding_manager)

        with pytest.raises(ValueError) as exc_info:
            manager.similarity_search("test query")

        assert "not initialized" in str(exc_info.value)

    @patch('src.vector_store.Config')
    def test_similarity_search(self, mock_config):
        """Test similarity search returns documents."""
        from src.vector_store import VectorStoreManager

        mock_config.VECTOR_STORE_PATH = Path("/nonexistent/path")
        mock_config.TOP_K_RESULTS = 3

        mock_embedding_manager = MagicMock()
        manager = VectorStoreManager(mock_embedding_manager)

        # Set up mock vector store with results
        mock_docs = [
            Document(page_content="result1", metadata={"source": "a.md"}),
            Document(page_content="result2", metadata={"source": "b.md"}),
        ]
        manager.vector_store = MagicMock()
        manager.vector_store.similarity_search.return_value = mock_docs

        results = manager.similarity_search("test query", k=2)

        assert len(results) == 2
        assert results[0].page_content == "result1"
        manager.vector_store.similarity_search.assert_called_once_with("test query", k=2)

    @patch('src.vector_store.Config')
    def test_similarity_search_with_score(self, mock_config):
        """Test similarity search with scores."""
        from src.vector_store import VectorStoreManager

        mock_config.VECTOR_STORE_PATH = Path("/nonexistent/path")
        mock_config.TOP_K_RESULTS = 3

        mock_embedding_manager = MagicMock()
        manager = VectorStoreManager(mock_embedding_manager)

        # Set up mock results with scores
        mock_results = [
            (Document(page_content="result1", metadata={}), 0.9),
            (Document(page_content="result2", metadata={}), 0.8),
        ]
        manager.vector_store = MagicMock()
        manager.vector_store.similarity_search_with_score.return_value = mock_results

        results = manager.similarity_search_with_score("test query", k=2)

        assert len(results) == 2
        assert results[0][1] == 0.9  # Score
        manager.vector_store.similarity_search_with_score.assert_called_once()


class TestRetriever:
    """Tests for retriever interface."""

    @patch('src.vector_store.Config')
    def test_get_retriever_without_store_raises(self, mock_config):
        """Test that getting retriever without store raises error."""
        from src.vector_store import VectorStoreManager

        mock_config.VECTOR_STORE_PATH = Path("/nonexistent/path")
        mock_config.TOP_K_RESULTS = 5

        mock_embedding_manager = MagicMock()
        manager = VectorStoreManager(mock_embedding_manager)

        with pytest.raises(ValueError) as exc_info:
            manager.get_retriever()

        assert "not initialized" in str(exc_info.value)

    @patch('src.vector_store.Config')
    def test_get_retriever(self, mock_config):
        """Test getting retriever from vector store."""
        from src.vector_store import VectorStoreManager

        mock_config.VECTOR_STORE_PATH = Path("/nonexistent/path")
        mock_config.TOP_K_RESULTS = 5

        mock_embedding_manager = MagicMock()
        manager = VectorStoreManager(mock_embedding_manager)

        # Set up mock vector store
        mock_retriever = MagicMock()
        manager.vector_store = MagicMock()
        manager.vector_store.as_retriever.return_value = mock_retriever

        retriever = manager.get_retriever(k=3)

        assert retriever == mock_retriever
        manager.vector_store.as_retriever.assert_called_once_with(search_kwargs={"k": 3})
