"""Web search tool using DuckDuckGo for current information."""

import time
import re
from typing import Optional, List, Dict
from collections import deque
from .base_tool import BaseTool


class WebSearchTool(BaseTool):
    """
    Tool for searching the internet using DuckDuckGo.

    Provides access to current information, recent events, and data
    not available in the document collection.
    """

    def __init__(self, max_results: int = 5, rate_limit_per_minute: int = 10, filter_irrelevant: bool = True):
        """
        Initialize the web search tool.

        Args:
            max_results: Maximum number of search results to return (default: 5)
            rate_limit_per_minute: Maximum number of searches per minute (default: 10)
            filter_irrelevant: Whether to filter out irrelevant results (default: True)
        """
        super().__init__()
        self.max_results = max_results
        self.rate_limit = rate_limit_per_minute
        self.request_times = deque(maxlen=rate_limit_per_minute)
        self.filter_irrelevant = filter_irrelevant

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

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query for relevance matching."""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'what', 'which',
            'who', 'whom', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
            'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my',
            'your', 'his', 'its', 'our', 'their', 'tell', 'search', 'find', 'show',
            'get', 'look', 'web', 'about', 'please', 'help', 'need', 'want'
        }
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{2,}\b', query.lower())
        # Filter stop words and return unique keywords
        keywords = [w for w in words if w not in stop_words]
        return list(dict.fromkeys(keywords))  # Preserve order, remove duplicates

    def _calculate_relevance(self, result: Dict, keywords: List[str]) -> float:
        """Calculate relevance score for a search result."""
        if not keywords:
            return 0.5  # Default score if no keywords

        title = result.get('title', '').lower()
        body = result.get('body', '').lower()
        combined = f"{title} {body}"

        # Count keyword matches
        matches = sum(1 for kw in keywords if kw in combined)

        # Calculate score (0 to 1)
        score = matches / len(keywords) if keywords else 0

        # Bonus for title matches (more important)
        title_matches = sum(1 for kw in keywords if kw in title)
        if title_matches > 0:
            score += 0.2 * (title_matches / len(keywords))

        return min(score, 1.0)

    def _filter_relevant_results(self, results: List[Dict], query: str, min_relevance: float = 0.3) -> List[Dict]:
        """Filter results to only include relevant ones."""
        keywords = self._extract_keywords(query)

        if not keywords:
            return results  # Can't filter without keywords

        scored_results = []
        for result in results:
            score = self._calculate_relevance(result, keywords)
            if score >= min_relevance:
                result['_relevance_score'] = score
                scored_results.append(result)

        # Sort by relevance (highest first)
        scored_results.sort(key=lambda x: x.get('_relevance_score', 0), reverse=True)

        return scored_results

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

            # Fetch more results initially to allow for filtering
            fetch_count = num_results * 3 if self.filter_irrelevant else num_results

            # Perform search with timeout
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=fetch_count))

            if not results:
                return f"No search results found for: {query}"

            # Apply relevance filtering if enabled
            if self.filter_irrelevant:
                results = self._filter_relevant_results(results, query, min_relevance=0.2)

                if not results:
                    # Try with lower threshold
                    with DDGS() as ddgs:
                        results = list(ddgs.text(query, max_results=fetch_count))
                    results = self._filter_relevant_results(results, query, min_relevance=0.1)

                    if not results:
                        return f"No relevant search results found for: {query}. Try rephrasing your query with more specific terms."

            # Limit to requested number
            results = results[:num_results]

            # Format results - deduplicate similar content
            content_parts = []
            source_titles = []
            seen_content = set()

            for result in results:
                title = result.get('title', 'No title')
                body = result.get('body', 'No description')

                # Aggressively clean the body text - remove all search result artifacts
                # Timestamps
                body = re.sub(r'\d+\s+(second|minute|hour|day|week|month|year)s?\s+ago\s*[·\-—–]?\s*', '', body)
                body = re.sub(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s*\d{4}\s*[·\-—–]?\s*', '', body)
                body = re.sub(r'\d{1,2}/\d{1,2}/\d{2,4}\s*[·\-—–]?\s*', '', body)
                # Search UI artifacts
                body = re.sub(r'Missing:\s*[^|]+\|\s*Show results with:[^\n]*', '', body)
                body = re.sub(r'More results from\s+\S+', '', body)
                body = re.sub(r'People also ask.*', '', body)
                body = re.sub(r'Related searches.*', '', body)
                # URLs and domains
                body = re.sub(r'https?://\S+', '', body)
                body = re.sub(r'www\.\w+\.\w+', '', body)
                # Ellipsis cleanup
                body = re.sub(r'\.\.\.\s*', '. ', body)
                body = re.sub(r'\s+', ' ', body).strip()

                # Deduplicate by checking if similar content already added
                fingerprint = body[:100].lower().strip()

                if fingerprint not in seen_content and body and body != 'No description':
                    # Clean format - just the body text, no bold titles
                    content_parts.append(body)
                    source_titles.append(title)
                    seen_content.add(fingerprint)

            if not content_parts:
                return f"Search found results but content was not relevant to '{query}'. Please try a more specific query."

            # Deduplicate source titles
            unique_sources = list(dict.fromkeys(source_titles))
            sources_text = ", ".join(unique_sources[:3])  # Limit to 3 sources

            # Combine snippets into flowing paragraphs
            combined_text = " ".join(content_parts)

            # Clean up the text - remove extra spaces, fix punctuation
            combined_text = ' '.join(combined_text.split())  # Normalize whitespace

            return f"{combined_text}\n\nSources: {sources_text}"

        except ImportError:
            return "Error: ddgs package not installed. Install with: pip install ddgs"
        except Exception as e:
            return f"Web search error: {str(e)}"
