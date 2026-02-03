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
        return """Search through indexed documents to find relevant information. \
Use this tool when the question is about specific content in documents, \
knowledge bases, or requires factual information from stored documents. \
This tool searches the document collection and returns answers with source citations."""

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
            sources = result.get('sources', [])

            # Build formatted output
            output_parts = [f"Answer: {answer}", "", "Sources:"]

            for i, source in enumerate(sources, 1):
                # Safely extract source fields with defaults
                source_name = source.get('source', 'Unknown')
                topic = source.get('topic', 'No topic')
                content = source.get('content', '')
                preview = content[:150] + "..." if len(content) > 150 else content

                output_parts.append(f"{i}. Source: {source_name} (Topic: {topic})")
                output_parts.append(f"   Preview: {preview}")

            return "\n".join(output_parts)

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
