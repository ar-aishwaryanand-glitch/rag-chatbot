"""RAG tool that wraps the existing RAGChain for document search."""

from typing import TYPE_CHECKING
from .base_tool import BaseTool

if TYPE_CHECKING:
    from src.rag_chain import RAGChain


class RAGTool(BaseTool):
    """
    Tool for searching through indexed documents using RAG.

    This wraps the existing RAGChain.ask() method to make it available
    as a tool for the agent.
    """

    def __init__(self, rag_chain: 'RAGChain'):
        """
        Initialize the RAG tool.

        Args:
            rag_chain: Instance of RAGChain for document retrieval
        """
        super().__init__()
        self.rag_chain = rag_chain

    @property
    def name(self) -> str:
        return "document_search"

    @property
    def description(self) -> str:
        return """Search through uploaded documents (PDFs, files) in the knowledge base. \
Use for questions about technical content, research papers, or information stored in documents. \
NOT for questions about this conversation or chat history. Returns answers with document source citations."""

    def _run(self, query: str, top_k: int = 3) -> str:
        """
        Execute document search using RAG.

        Args:
            query: The question to search for in documents
            top_k: Number of document chunks to retrieve (default: 3)

        Returns:
            Formatted string with answer and sources
        """
        # Validate input
        if not query or not query.strip():
            return "Error: Query cannot be empty"

        try:
            # Call the existing RAG chain with top_k parameter
            result = self.rag_chain.ask(query, top_k=top_k)

            # Validate result structure
            if not isinstance(result, dict):
                return "Error: Invalid response from RAG chain"

            # Format the result for the agent
            answer = result.get('answer', 'No answer generated')

            # The answer already includes "Sources:" at the end from the LLM
            # Just return it directly without adding duplicate source information
            return f"Answer: {answer}"

        except Exception as e:
            return f"Error executing document search: {str(e)}"

    def get_raw_result(self, query: str) -> dict:
        """
        Get the raw result from RAG chain without formatting.

        Useful for UI display where we want the full result structure.

        Args:
            query: The question to search for

        Returns:
            dict: Raw result from RAGChain.ask()
        """
        return self.rag_chain.ask(query)
