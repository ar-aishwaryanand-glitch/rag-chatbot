"""Web search tool using DuckDuckGo for current information."""

from typing import Optional
from .base_tool import BaseTool


class WebSearchTool(BaseTool):
    """
    Tool for searching the internet using DuckDuckGo.

    Provides access to current information, recent events, and data
    not available in the document collection.
    """

    def __init__(self, max_results: int = 3):
        """
        Initialize the web search tool.

        Args:
            max_results: Maximum number of search results to return (default: 3)
        """
        super().__init__()
        self.max_results = max_results

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return """Search the internet for current information, recent events, news, or real-time data. \
Use this tool when the question is about current events, recent developments, real-time information, \
or anything not available in the document database. Do NOT use for questions about stored documents."""

    def _run(self, query: str, num_results: Optional[int] = None) -> str:
        """
        Execute web search using DuckDuckGo.

        Args:
            query: Search query
            num_results: Number of results to return (overrides default)

        Returns:
            Formatted string with search results
        """
        if num_results is None:
            num_results = self.max_results

        try:
            from duckduckgo_search import DDGS

            # Perform search
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))

            if not results:
                return f"No search results found for: {query}"

            # Format results
            formatted_results = [f"Search results for: {query}\n"]

            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                body = result.get('body', 'No description')
                href = result.get('href', 'No URL')

                formatted_results.append(f"\n{i}. {title}")
                formatted_results.append(f"   {body}")
                formatted_results.append(f"   URL: {href}")

            return "\n".join(formatted_results)

        except ImportError:
            return "Error: duckduckgo-search package not installed. Install with: pip install duckduckgo-search"
        except Exception as e:
            return f"Web search error: {str(e)}"
