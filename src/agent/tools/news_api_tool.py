"""
News API Tool - Fetch latest news from multiple sources.

Integrates with:
- NewsAPI (newsapi.org) for comprehensive news coverage
- Google News RSS feeds as fallback
"""

import os
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import json

from .base_tool import BaseTool, ToolResult
from .relevance_evaluator import RelevanceEvaluator

# Optional imports
try:
    from newsapi import NewsApiClient
    NEWSAPI_AVAILABLE = True
except ImportError:
    NEWSAPI_AVAILABLE = False

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


@dataclass
class NewsArticle:
    """Represents a news article."""
    title: str
    description: str
    url: str
    source: str
    published_at: Optional[datetime] = None
    author: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'source': self.source,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'author': self.author
        }


class NewsApiTool(BaseTool):
    """
    News API tool for fetching latest news articles.

    Features:
    - NewsAPI integration for comprehensive news coverage
    - Google News RSS feeds as fallback
    - Filtering by keyword, category, language
    - Multiple source support
    - Clean, structured output

    Examples:
        "Get latest AI news"
        "Find articles about climate change from last week"
        "Get top headlines in technology"
    """

    NEWSAPI_CATEGORIES = ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology']

    def __init__(self, api_key: Optional[str] = None, llm_client=None, filter_irrelevant: bool = True):
        """
        Initialize News API Tool.

        Args:
            api_key: NewsAPI key (optional, will use env var if not provided)
            llm_client: Optional LLM client for relevance filtering
            filter_irrelevant: Whether to filter out irrelevant articles (default: True)
        """
        super().__init__()

        # Get API key from env or parameter
        self.api_key = api_key or os.getenv('NEWSAPI_KEY')

        # Initialize NewsAPI client if available
        self.newsapi_client = None
        if NEWSAPI_AVAILABLE and self.api_key:
            try:
                self.newsapi_client = NewsApiClient(api_key=self.api_key)
            except Exception as e:
                print(f"⚠️ Failed to initialize NewsAPI client: {e}")

        # Initialize LLM client for relevance filtering
        self.llm_client = llm_client
        if not self.llm_client and ANTHROPIC_AVAILABLE and filter_irrelevant:
            # Try to initialize from environment variable
            anthropic_key = os.getenv('ANTHROPIC_API_KEY')
            if anthropic_key:
                try:
                    self.llm_client = Anthropic(api_key=anthropic_key)
                except Exception as e:
                    print(f"⚠️ Failed to initialize Anthropic client: {e}")

        # Initialize relevance evaluator
        self.filter_irrelevant = filter_irrelevant
        self.relevance_evaluator = RelevanceEvaluator(
            llm_client=self.llm_client,
            threshold=0.6  # Require 60% confidence to consider relevant
        )

        # Check dependencies
        if not FEEDPARSER_AVAILABLE:
            self.available = False
            self.error_msg = "feedparser not installed. Install with: pip install feedparser"
        elif not REQUESTS_AVAILABLE:
            self.available = False
            self.error_msg = "requests not installed. Install with: pip install requests"
        else:
            self.available = True
            self.error_msg = None

        # Determine which service to use
        if self.newsapi_client:
            self.service = "NewsAPI"
        elif FEEDPARSER_AVAILABLE:
            self.service = "Google News RSS"
        else:
            self.service = None

    @property
    def name(self) -> str:
        """Unique name for the tool."""
        return "news_api"

    @property
    def description(self) -> str:
        """Description of what the tool does."""
        filtering_status = " with LLM relevance filtering" if (self.filter_irrelevant and self.llm_client) else " with keyword filtering" if self.filter_irrelevant else ""
        return (
            "Fetch latest news articles from NewsAPI or Google News RSS feeds. "
            "Use this for finding recent news, top headlines, or articles on specific topics. "
            "Supports keyword search, category filtering, and date ranges. "
            f"Automatically filters out irrelevant articles{filtering_status}. "
            f"Currently using: {self.service or 'No service available'}"
        )

    def _run(self, *args, **kwargs) -> str:
        """Wrapper for the run_tool method to satisfy BaseTool interface."""
        result = self.run_tool(*args, **kwargs)
        if result.success:
            return result.output
        else:
            raise Exception(result.error or "News API execution failed")

    def run_tool(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        language: str = 'en',
        max_results: int = 5,
        days_back: int = 7
    ) -> ToolResult:
        """
        Fetch news articles.

        Args:
            query: Search keyword or topic
            category: News category (business, tech, science, etc.)
            language: Language code (default: en)
            max_results: Maximum number of articles to return
            days_back: How many days back to search

        Returns:
            ToolResult with formatted news articles
        """
        start_time = time.time()

        if not self.available:
            return ToolResult(
                success=False,
                output="",
                error=self.error_msg,
                duration=time.time() - start_time
            )

        try:
            articles = []

            # Try NewsAPI first if available
            if self.newsapi_client:
                articles = self._fetch_from_newsapi(query, category, language, max_results, days_back)

            # Fallback to Google News RSS
            elif FEEDPARSER_AVAILABLE:
                articles = self._fetch_from_google_news(query, max_results)

            if not articles:
                return ToolResult(
                    success=False,
                    output="",
                    error="No articles found or service unavailable",
                    duration=time.time() - start_time
                )

            # Apply relevance filtering if enabled and query is provided
            original_count = len(articles)
            if self.filter_irrelevant and query:
                print(f"🔍 Filtering {original_count} articles for relevance to: '{query}'")

                # Convert NewsArticle objects to dicts for filtering
                article_dicts = [
                    {
                        'title': a.title,
                        'description': a.description,
                        'url': a.url,
                        'source': a.source,
                        'author': a.author,
                        'published_at': a.published_at
                    }
                    for a in articles
                ]

                # Filter using relevance evaluator
                use_llm = self.llm_client is not None
                filtered_dicts = self.relevance_evaluator.filter_articles(
                    query=query,
                    articles=article_dicts,
                    use_llm=use_llm,
                    verbose=True
                )

                # Convert back to NewsArticle objects
                articles = [
                    NewsArticle(
                        title=d['title'],
                        description=d['description'],
                        url=d['url'],
                        source=d['source'],
                        author=d.get('author'),
                        published_at=d.get('published_at')
                    )
                    for d in filtered_dicts
                ]

                filtered_count = len(articles)
                print(f"✓ Kept {filtered_count}/{original_count} relevant articles")

                if not articles:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"No relevant articles found (filtered {original_count} irrelevant results)",
                        duration=time.time() - start_time
                    )

            # Format output
            output = self._format_articles(articles, query, category)

            return ToolResult(
                success=True,
                output=output,
                error=None,
                duration=time.time() - start_time
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"News API error: {str(e)}",
                duration=time.time() - start_time
            )

    def _fetch_from_newsapi(
        self,
        query: Optional[str],
        category: Optional[str],
        language: str,
        max_results: int,
        days_back: int
    ) -> List[NewsArticle]:
        """Fetch articles from NewsAPI."""
        articles = []

        try:
            # Calculate date range
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

            # Choose API endpoint
            if query:
                # Use everything endpoint for keyword search
                response = self.newsapi_client.get_everything(
                    q=query,
                    from_param=from_date,
                    language=language,
                    sort_by='relevancy',
                    page_size=max_results
                )
            elif category:
                # Use top-headlines for category
                response = self.newsapi_client.get_top_headlines(
                    category=category,
                    language=language,
                    page_size=max_results
                )
            else:
                # Default to top headlines
                response = self.newsapi_client.get_top_headlines(
                    language=language,
                    page_size=max_results
                )

            # Parse articles
            if response.get('status') == 'ok':
                for article_data in response.get('articles', []):
                    article = NewsArticle(
                        title=article_data.get('title', 'Untitled'),
                        description=article_data.get('description', ''),
                        url=article_data.get('url', ''),
                        source=article_data.get('source', {}).get('name', 'Unknown'),
                        author=article_data.get('author'),
                        content=article_data.get('content'),
                        image_url=article_data.get('urlToImage'),
                        published_at=self._parse_date(article_data.get('publishedAt'))
                    )
                    articles.append(article)

        except Exception as e:
            print(f"⚠️ NewsAPI error: {e}")

        return articles

    def _fetch_from_google_news(self, query: Optional[str], max_results: int) -> List[NewsArticle]:
        """Fetch articles from Google News RSS feed."""
        articles = []

        try:
            # Build Google News RSS URL
            if query:
                rss_url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
            else:
                rss_url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"

            # Parse RSS feed
            feed = feedparser.parse(rss_url)

            # Extract articles
            for entry in feed.entries[:max_results]:
                article = NewsArticle(
                    title=entry.get('title', 'Untitled'),
                    description=entry.get('summary', ''),
                    url=entry.get('link', ''),
                    source=entry.get('source', {}).get('title', 'Google News'),
                    published_at=self._parse_date(entry.get('published'))
                )
                articles.append(article)

        except Exception as e:
            print(f"⚠️ Google News RSS error: {e}")

        return articles

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None

        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                # Try parsing common formats
                from dateutil import parser
                return parser.parse(date_str)
            except:
                return None

    def _format_articles(
        self,
        articles: List[NewsArticle],
        query: Optional[str],
        category: Optional[str]
    ) -> str:
        """Format articles as markdown."""
        output = f"# News Articles\n\n"

        if query:
            output += f"**Search Query:** {query}\n"
        if category:
            output += f"**Category:** {category}\n"

        output += f"**Source:** {self.service}\n"
        output += f"**Articles Found:** {len(articles)}\n"
        output += f"**Retrieved:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

        output += "---\n\n"

        for i, article in enumerate(articles, 1):
            output += f"## {i}. {article.title}\n\n"
            output += f"**Source:** {article.source}\n"

            if article.author:
                output += f"**Author:** {article.author}\n"

            if article.published_at:
                output += f"**Published:** {article.published_at.strftime('%Y-%m-%d %H:%M')}\n"

            output += f"**URL:** {article.url}\n\n"

            if article.description:
                output += f"{article.description}\n\n"

            output += "---\n\n"

        return output

    def get_usage_examples(self) -> List[str]:
        """Return example usage patterns."""
        return [
            "Get latest news about artificial intelligence",
            "Find technology headlines from the last 3 days",
            "Search for articles about climate change",
            "Get top business news",
            "Find recent science articles"
        ]
