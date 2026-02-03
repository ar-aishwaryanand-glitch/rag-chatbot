"""Web search tool using DuckDuckGo for current information."""

import time
from typing import Optional
from collections import deque
from .base_tool import BaseTool


class WebSearchTool(BaseTool):
    """
    Tool for searching the internet using DuckDuckGo.

    Provides access to current information, recent events, and data
    not available in the document collection.
    """

    def __init__(self, max_results: int = 3, rate_limit_per_minute: int = 10):
        """
        Initialize the web search tool.

        Args:
            max_results: Maximum number of search results to return (default: 3)
            rate_limit_per_minute: Maximum number of searches per minute (default: 10)
        """
        super().__init__()
        self.max_results = max_results
        self.rate_limit = rate_limit_per_minute
        self.request_times = deque(maxlen=rate_limit_per_minute)

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return """Quick web search that returns links and short snippets from search engines. \
Use this tool to find URLs or get quick overviews. Returns links only, not full content. \
For detailed content from websites, use web_agent instead. Best for finding what's available online."""

    def _check_rate_limit(self) -> tuple[bool, Optional[str]]:
        """Check if rate limit is exceeded."""
        current_time = time.time()

        # Remove timestamps older than 1 minute
        cutoff_time = current_time - 60
        while self.request_times and self.request_times[0] < cutoff_time:
            self.request_times.popleft()

        # Check if we've hit the rate limit
        if len(self.request_times) >= self.rate_limit:
            return False, f"Rate limit exceeded: maximum {self.rate_limit} searches per minute"

        # Add current request time
        self.request_times.append(current_time)
        return True, None

    def _run(self, query: str, num_results: Optional[int] = None) -> str:
        """
        Execute web search using DuckDuckGo.

        Args:
            query: Search query
            num_results: Number of results to return (overrides default)

        Returns:
            Formatted string with search results
        """
        # Validate query
        if not query or not query.strip():
            return "Error: Search query cannot be empty"

        query = query.strip()

        # Validate query length
        if len(query) > 500:
            return "Error: Search query too long (max 500 characters)"

        # Check rate limit
        allowed, error = self._check_rate_limit()
        if not allowed:
            return f"Error: {error}"

        if num_results is None:
            num_results = self.max_results

        # Validate num_results
        if num_results < 1 or num_results > 20:
            return "Error: num_results must be between 1 and 20"

        try:
            from ddgs import DDGS

            # Perform search with timeout
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
            return "Error: ddgs package not installed. Install with: pip install ddgs"
        except Exception as e:
            return f"Web search error: {str(e)}"
