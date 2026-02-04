"""
Unit tests for RAG chain module.

Tests cover:
- RAGChain initialization
- Context retrieval
- Context formatting
- Answer generation
- Full RAG pipeline
"""

import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document


class TestRAGChainImport:
    """Tests for RAGChain imports."""

    def test_rag_chain_import(self):
        """Test that RAGChain can be imported."""
        from src.rag_chain import RAGChain
        assert RAGChain is not None


class TestRAGChainInit:
    """Tests for RAGChain initialization."""

    @patch('src.rag_chain.get_observability')
    @patch('src.rag_chain.ChatPromptTemplate')
    @patch('src.rag_chain.Config')
    def test_init_with_groq_provider(self, mock_config, mock_prompt, mock_obs):
        """Test initialization with Groq provider."""
        from src.rag_chain import RAGChain

        mock_config.LLM_PROVIDER = "groq"
        mock_config.GROQ_MODEL = "llama-3.1-70b-versatile"
        mock_config.LLM_TEMPERATURE = 0.7
        mock_config.LLM_MAX_TOKENS = 1024
        mock_config.GROQ_API_KEY = "test_key"

        mock_obs.return_value = MagicMock()
        mock_prompt.from_messages.return_value = MagicMock()

        mock_vs_manager = MagicMock()

        # ChatGroq is imported inside _initialize_llm, patch at import location
        mock_groq = MagicMock()
        with patch.dict('sys.modules', {'langchain_groq': MagicMock(ChatGroq=mock_groq)}):
            with patch('langchain_groq.ChatGroq', mock_groq):
                mock_groq.return_value = MagicMock()
                chain = RAGChain(mock_vs_manager)

                assert chain.vector_store_manager == mock_vs_manager
                mock_groq.assert_called_once()

    @patch('src.rag_chain.get_observability')
    @patch('src.rag_chain.ChatPromptTemplate')
    @patch('src.rag_chain.Config')
    def test_init_unsupported_provider_raises(self, mock_config, mock_prompt, mock_obs):
        """Test that unsupported provider raises ValueError."""
        from src.rag_chain import RAGChain

        mock_config.LLM_PROVIDER = "unsupported"
        mock_obs.return_value = MagicMock()
        mock_prompt.from_messages.return_value = MagicMock()

        mock_vs_manager = MagicMock()

        with pytest.raises(ValueError) as exc_info:
            RAGChain(mock_vs_manager)

        assert "Unsupported LLM provider" in str(exc_info.value)


class TestContextFormatting:
    """Tests for context formatting."""

    def test_format_context_basic(self, sample_documents):
        """Test basic context formatting."""
        from src.rag_chain import RAGChain

        # Create a minimal RAGChain with mocked dependencies
        with patch.object(RAGChain, '__init__', lambda self, x: None):
            chain = RAGChain.__new__(RAGChain)

            context = chain.format_context(sample_documents)

            assert "[Source 1:" in context
            assert "rag-overview.md" in context
            assert "RAG stands for" in context
            assert "---" in context  # Separator

    def test_format_context_empty_list(self):
        """Test formatting empty document list."""
        from src.rag_chain import RAGChain

        with patch.object(RAGChain, '__init__', lambda self, x: None):
            chain = RAGChain.__new__(RAGChain)

            context = chain.format_context([])

            assert context == ""

    def test_format_context_with_topic(self):
        """Test that topic metadata is included."""
        from src.rag_chain import RAGChain

        docs = [
            Document(
                page_content="Test content",
                metadata={"source": "test.md", "topic": "testing"}
            )
        ]

        with patch.object(RAGChain, '__init__', lambda self, x: None):
            chain = RAGChain.__new__(RAGChain)

            context = chain.format_context(docs)

            assert "Topic: testing" in context

    def test_format_context_strips_whitespace(self):
        """Test that content whitespace is stripped."""
        from src.rag_chain import RAGChain

        docs = [
            Document(
                page_content="  content with spaces  \n\n",
                metadata={"source": "test.md"}
            )
        ]

        with patch.object(RAGChain, '__init__', lambda self, x: None):
            chain = RAGChain.__new__(RAGChain)

            context = chain.format_context(docs)

            assert "  content with spaces  " not in context
            assert "content with spaces" in context


class TestContextRetrieval:
    """Tests for context retrieval."""

    @patch('src.rag_chain.time')
    @patch('src.rag_chain.Config')
    def test_retrieve_context(self, mock_config, mock_time):
        """Test context retrieval from vector store."""
        from src.rag_chain import RAGChain

        mock_config.TOP_K_RESULTS = 3
        mock_config.get_vector_store_display_name.return_value = "FAISS"
        mock_time.time.return_value = 0

        mock_docs = [
            (Document(page_content="doc1", metadata={}), 0.9),
            (Document(page_content="doc2", metadata={}), 0.8),
        ]

        with patch.object(RAGChain, '__init__', lambda self, x: None):
            chain = RAGChain.__new__(RAGChain)
            chain.vector_store_manager = MagicMock()
            chain.vector_store_manager.similarity_search_with_score.return_value = mock_docs
            chain.observability = MagicMock()
            chain.observability.trace_operation.return_value.__enter__ = MagicMock(return_value=MagicMock())
            chain.observability.trace_operation.return_value.__exit__ = MagicMock(return_value=False)

            results = chain.retrieve_context("test query", k=2)

            assert len(results) == 2
            assert results[0].page_content == "doc1"


class TestAnswerGeneration:
    """Tests for answer generation."""

    @patch('src.rag_chain.time')
    @patch('src.rag_chain.Config')
    def test_generate_answer(self, mock_config, mock_time):
        """Test answer generation with LLM."""
        from src.rag_chain import RAGChain

        mock_config.LLM_PROVIDER = "groq"
        mock_config.get_llm_display_name.return_value = "Groq Llama"
        mock_time.time.return_value = 0

        with patch.object(RAGChain, '__init__', lambda self, x: None):
            chain = RAGChain.__new__(RAGChain)

            mock_response = MagicMock()
            mock_response.content = "This is the generated answer."

            chain.llm = MagicMock()
            chain.llm.invoke.return_value = mock_response
            chain.prompt_template = MagicMock()
            chain.prompt_template.format_messages.return_value = ["messages"]
            chain.observability = MagicMock()
            chain.observability.trace_operation.return_value.__enter__ = MagicMock(return_value=MagicMock())
            chain.observability.trace_operation.return_value.__exit__ = MagicMock(return_value=False)

            answer = chain.generate_answer("What is RAG?", "Some context...")

            assert answer == "This is the generated answer."
            chain.llm.invoke.assert_called_once()


class TestRAGPipeline:
    """Tests for the full RAG pipeline."""

    @patch('src.rag_chain.time')
    @patch('src.rag_chain.Config')
    def test_ask_returns_expected_structure(self, mock_config, mock_time):
        """Test that ask() returns expected result structure."""
        from src.rag_chain import RAGChain

        mock_config.TOP_K_RESULTS = 3
        mock_config.LLM_PROVIDER = "groq"
        mock_config.USE_PINECONE = False
        mock_config.get_llm_display_name.return_value = "Groq"
        mock_config.get_vector_store_display_name.return_value = "FAISS"
        mock_time.time.return_value = 0

        mock_docs = [
            (Document(page_content="content", metadata={"source": "test.md", "topic": "test"}), 0.9)
        ]

        with patch.object(RAGChain, '__init__', lambda self, x: None):
            chain = RAGChain.__new__(RAGChain)
            chain.vector_store_manager = MagicMock()
            chain.vector_store_manager.similarity_search_with_score.return_value = mock_docs

            mock_response = MagicMock()
            mock_response.content = "The answer is..."
            chain.llm = MagicMock()
            chain.llm.invoke.return_value = mock_response
            chain.prompt_template = MagicMock()
            chain.prompt_template.format_messages.return_value = ["messages"]
            chain.observability = MagicMock()
            chain.observability.trace_operation.return_value.__enter__ = MagicMock(return_value=MagicMock())
            chain.observability.trace_operation.return_value.__exit__ = MagicMock(return_value=False)

            result = chain.ask("What is RAG?")

            assert "question" in result
            assert "answer" in result
            assert "context" in result
            assert "sources" in result
            assert result["question"] == "What is RAG?"
            assert result["answer"] == "The answer is..."

    @patch('src.rag_chain.time')
    @patch('src.rag_chain.Config')
    def test_ask_with_no_results(self, mock_config, mock_time):
        """Test ask() when no documents are retrieved."""
        from src.rag_chain import RAGChain

        mock_config.TOP_K_RESULTS = 3
        mock_config.get_llm_display_name.return_value = "Groq"
        mock_config.get_vector_store_display_name.return_value = "FAISS"
        mock_time.time.return_value = 0

        with patch.object(RAGChain, '__init__', lambda self, x: None):
            chain = RAGChain.__new__(RAGChain)
            chain.vector_store_manager = MagicMock()
            chain.vector_store_manager.similarity_search_with_score.return_value = []
            chain.observability = MagicMock()
            chain.observability.trace_operation.return_value.__enter__ = MagicMock(return_value=MagicMock())
            chain.observability.trace_operation.return_value.__exit__ = MagicMock(return_value=False)

            result = chain.ask("obscure question")

            assert "No relevant context found" in result["answer"]
            assert result["sources"] == []

    @patch('src.rag_chain.time')
    @patch('src.rag_chain.Config')
    def test_ask_with_custom_top_k(self, mock_config, mock_time):
        """Test ask() with custom top_k parameter."""
        from src.rag_chain import RAGChain

        mock_config.TOP_K_RESULTS = 5
        mock_config.LLM_PROVIDER = "groq"
        mock_config.USE_PINECONE = False
        mock_config.get_llm_display_name.return_value = "Groq"
        mock_config.get_vector_store_display_name.return_value = "FAISS"
        mock_time.time.return_value = 0

        mock_docs = [
            (Document(page_content="content", metadata={"source": "a.md", "topic": "t"}), 0.9),
            (Document(page_content="content2", metadata={"source": "b.md", "topic": "t"}), 0.8),
        ]

        with patch.object(RAGChain, '__init__', lambda self, x: None):
            chain = RAGChain.__new__(RAGChain)
            chain.vector_store_manager = MagicMock()
            chain.vector_store_manager.similarity_search_with_score.return_value = mock_docs

            mock_response = MagicMock()
            mock_response.content = "Answer"
            chain.llm = MagicMock()
            chain.llm.invoke.return_value = mock_response
            chain.prompt_template = MagicMock()
            chain.prompt_template.format_messages.return_value = ["messages"]
            chain.observability = MagicMock()
            chain.observability.trace_operation.return_value.__enter__ = MagicMock(return_value=MagicMock())
            chain.observability.trace_operation.return_value.__exit__ = MagicMock(return_value=False)

            chain.ask("question", top_k=2)  # result intentionally unused

            # Verify custom top_k was used
            chain.vector_store_manager.similarity_search_with_score.assert_called_with("question", k=2)


class TestSourceExtraction:
    """Tests for source extraction in RAG results."""

    def test_sources_include_metadata(self):
        """Test that sources include source and topic metadata."""

        docs = [
            Document(
                page_content="This is the content of the document.",
                metadata={"source": "guide.md", "topic": "RAG"}
            )
        ]

        # Simulate source extraction logic from ask()
        sources = [
            {
                "source": doc.metadata.get("source", "unknown"),
                "topic": doc.metadata.get("topic", "unknown"),
                "content": doc.page_content.strip()[:200] + "..."
            }
            for doc in docs
        ]

        assert len(sources) == 1
        assert sources[0]["source"] == "guide.md"
        assert sources[0]["topic"] == "RAG"
        assert "content of the document" in sources[0]["content"]


class TestDisplayResult:
    """Tests for result display formatting."""

    def test_display_result_does_not_raise(self):
        """Test that display_result doesn't raise errors."""
        from src.rag_chain import RAGChain

        with patch.object(RAGChain, '__init__', lambda self, x: None):
            chain = RAGChain.__new__(RAGChain)

            result = {
                "question": "What is RAG?",
                "answer": "RAG is a technique...",
                "sources": [
                    {"source": "doc.md", "topic": "RAG", "content": "preview..."}
                ]
            }

            # Should not raise
            chain.display_result(result)
