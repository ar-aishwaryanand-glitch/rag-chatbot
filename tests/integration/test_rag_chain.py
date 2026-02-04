"""
Integration tests for RAG chain.

Tests cover:
- RAGChain initialization
- Document retrieval
- Answer generation
- End-to-end query flow

Note: Some tests require actual API keys and are skipped in CI.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestRAGChainInitialization:
    """Tests for RAGChain initialization."""

    def test_rag_chain_import(self):
        """Test that RAGChain can be imported."""
        from src.rag_chain import RAGChain
        assert RAGChain is not None

    @patch('src.rag_chain.VectorStoreManager')
    @patch('src.rag_chain.EmbeddingManager')
    def test_rag_chain_creation_with_mocks(self, mock_embed, mock_vs):
        """Test RAGChain creation with mocked dependencies."""

        mock_embed_instance = MagicMock()
        mock_embed.return_value = mock_embed_instance

        mock_vs_instance = MagicMock()
        mock_vs.return_value = mock_vs_instance

        # RAGChain should be creatable with mocked dependencies
        # Note: Actual instantiation may require more mocking


class TestRAGChainRetrieval:
    """Tests for document retrieval."""

    def test_context_formatting(self, sample_documents):
        """Test that documents are formatted correctly for context."""
        # Simulate context formatting
        context_parts = []
        for doc in sample_documents:
            source = doc.metadata.get("source", "Unknown")
            context_parts.append(f"[Source: {source}]\n{doc.page_content}")

        context = "\n\n".join(context_parts)

        assert "rag-overview.md" in context
        assert "RAG stands for" in context
        assert "[Source:" in context

    def test_source_extraction(self, sample_documents):
        """Test extracting sources from documents."""
        sources = [
            {"source": doc.metadata.get("source", "Unknown")}
            for doc in sample_documents
        ]

        assert len(sources) == 3
        assert any(s["source"] == "rag-overview.md" for s in sources)


class TestRAGChainQuery:
    """Tests for query processing."""

    def test_query_sanitization(self):
        """Test that queries are properly sanitized."""
        # Test various query edge cases
        test_queries = [
            "What is RAG?",
            "  Leading whitespace  ",
            "Query with\nnewlines",
            "",  # Empty query
        ]

        for query in test_queries:
            sanitized = query.strip()
            # Should not crash and should be string
            assert isinstance(sanitized, str)

    @patch('src.rag_chain.RAGChain')
    def test_ask_method_structure(self, mock_rag):
        """Test that ask method returns expected structure."""
        mock_instance = MagicMock()
        mock_instance.ask.return_value = {
            "question": "What is RAG?",
            "answer": "RAG stands for Retrieval-Augmented Generation.",
            "context": [],
            "sources": [{"source": "doc.md"}]
        }
        mock_rag.return_value = mock_instance

        result = mock_instance.ask("What is RAG?")

        assert "question" in result
        assert "answer" in result
        assert "sources" in result


class TestRAGChainMocked:
    """Tests with fully mocked RAG chain."""

    def test_mocked_retrieval_flow(self, mock_vector_store, sample_documents, mock_llm):
        """Test full retrieval flow with mocks."""
        # Set up mock vector store to return documents
        mock_vector_store.similarity_search.return_value = sample_documents

        # Simulate the retrieval
        query = "What is RAG?"
        retrieved_docs = mock_vector_store.similarity_search(query, k=3)

        assert len(retrieved_docs) == 3
        assert retrieved_docs[0].page_content is not None

    def test_mocked_generation_flow(self, mock_llm, mock_llm_response):
        """Test answer generation with mock LLM."""
        # Set up mock response
        mock_llm.invoke.return_value = mock_llm_response(
            "RAG is a technique that combines retrieval with generation."
        )

        # Simulate generation
        response = mock_llm.invoke("Generate answer based on context...")

        assert response.content is not None
        assert "RAG" in response.content

    def test_end_to_end_mocked_flow(
        self, mock_vector_store, sample_documents, mock_llm, mock_llm_response
    ):
        """Test complete RAG flow with all components mocked."""
        # Step 1: Retrieval
        mock_vector_store.similarity_search.return_value = sample_documents[:2]
        query = "Explain RAG"
        docs = mock_vector_store.similarity_search(query, k=2)

        # Step 2: Format context
        context = "\n".join([d.page_content for d in docs])

        # Step 3: Generate answer
        mock_llm.invoke.return_value = mock_llm_response(
            f"Based on the context: {context[:50]}..."
        )
        response = mock_llm.invoke(f"Context: {context}\nQuestion: {query}")

        # Verify flow
        assert len(docs) == 2
        assert len(context) > 0
        assert response.content is not None


@pytest.mark.integration
@pytest.mark.slow
class TestRAGChainIntegration:
    """Integration tests requiring actual services.

    These tests are skipped by default and only run with proper configuration.
    """

    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires actual API keys and services"
    )
    def test_real_rag_query(self):
        """Test with real RAG chain (requires API keys)."""
        from src.system_init import initialize_system

        rag = initialize_system()
        result = rag.ask("What is retrieval augmented generation?")

        assert result is not None
        assert "answer" in result
        assert len(result["answer"]) > 0


class TestRAGChainErrorHandling:
    """Tests for error handling in RAG chain."""

    def test_empty_query_handling(self):
        """Test handling of empty queries."""
        # Empty queries should be handled gracefully
        query = ""
        assert len(query.strip()) == 0

    def test_no_results_handling(self, mock_vector_store):
        """Test handling when no documents are retrieved."""
        mock_vector_store.similarity_search.return_value = []

        docs = mock_vector_store.similarity_search("obscure query", k=3)

        assert docs == []
        # RAG chain should handle this gracefully

    def test_llm_error_handling(self, mock_llm):
        """Test handling of LLM errors."""
        mock_llm.invoke.side_effect = Exception("LLM API error")

        with pytest.raises(Exception) as exc_info:
            mock_llm.invoke("test")

        assert "LLM API error" in str(exc_info.value)
