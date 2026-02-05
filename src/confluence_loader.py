"""Confluence document loader for RAG system.

Fetches pages from Atlassian Confluence and converts them to LangChain documents
for indexing in the vector store.
"""

import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import requests
from requests.auth import HTTPBasicAuth
from langchain_core.documents import Document

from .config import Config


@dataclass
class ConfluencePage:
    """Represents a Confluence page."""
    id: str
    title: str
    space_key: str
    content: str
    url: str
    last_modified: str
    version: int


class ConfluenceLoader:
    """
    Loads documents from Atlassian Confluence.

    Supports fetching:
    - All pages from a space
    - Specific pages by ID
    - Pages matching a search query (CQL)
    """

    def __init__(
        self,
        url: Optional[str] = None,
        username: Optional[str] = None,
        api_token: Optional[str] = None,
        space_key: Optional[str] = None
    ):
        """
        Initialize the Confluence loader.

        Args:
            url: Confluence base URL (e.g., https://your-domain.atlassian.net/wiki)
            username: Atlassian account email
            api_token: API token from Atlassian
            space_key: Default space key to use
        """
        self.url = (url or Config.CONFLUENCE_URL).rstrip('/')
        self.username = username or Config.CONFLUENCE_USERNAME
        self.api_token = api_token or Config.CONFLUENCE_API_TOKEN
        self.space_key = space_key or Config.CONFLUENCE_SPACE_KEY

        if not all([self.url, self.username, self.api_token]):
            raise ValueError(
                "Confluence credentials not configured. Please set "
                "CONFLUENCE_URL, CONFLUENCE_USERNAME, and CONFLUENCE_API_TOKEN "
                "in your .env file."
            )

        self.auth = HTTPBasicAuth(self.username, self.api_token)
        self.api_base = f"{self.url}/rest/api"

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated request to the Confluence API."""
        url = f"{self.api_base}/{endpoint}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        response = requests.get(
            url,
            auth=self.auth,
            headers=headers,
            params=params,
            timeout=30
        )

        if response.status_code == 401:
            raise ValueError(
                "Confluence authentication failed. Check your username and API token."
            )
        elif response.status_code == 403:
            raise ValueError(
                "Access denied. Ensure your API token has read access to the space."
            )
        elif response.status_code != 200:
            raise ValueError(
                f"Confluence API error: {response.status_code} - {response.text}"
            )

        return response.json()

    def _clean_html(self, html_content: str) -> str:
        """Convert HTML content to plain text."""
        # Remove script and style tags
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)

        # Convert common HTML elements to text equivalents
        html_content = re.sub(r'<br\s*/?>', '\n', html_content)
        html_content = re.sub(r'<p[^>]*>', '\n\n', html_content)
        html_content = re.sub(r'</p>', '', html_content)
        html_content = re.sub(r'<li[^>]*>', '\n- ', html_content)
        html_content = re.sub(r'<h[1-6][^>]*>', '\n\n## ', html_content)
        html_content = re.sub(r'</h[1-6]>', '\n', html_content)

        # Remove remaining HTML tags
        html_content = re.sub(r'<[^>]+>', '', html_content)

        # Decode HTML entities
        html_content = html_content.replace('&nbsp;', ' ')
        html_content = html_content.replace('&amp;', '&')
        html_content = html_content.replace('&lt;', '<')
        html_content = html_content.replace('&gt;', '>')
        html_content = html_content.replace('&quot;', '"')
        html_content = html_content.replace('&#39;', "'")

        # Clean up whitespace
        html_content = re.sub(r'\n{3,}', '\n\n', html_content)
        html_content = re.sub(r' +', ' ', html_content)

        return html_content.strip()

    def _parse_page(self, page_data: Dict[str, Any]) -> ConfluencePage:
        """Parse API response into a ConfluencePage object."""
        body = page_data.get('body', {}).get('storage', {}).get('value', '')
        clean_content = self._clean_html(body)

        # Build page URL
        page_url = f"{self.url}{page_data.get('_links', {}).get('webui', '')}"

        return ConfluencePage(
            id=page_data['id'],
            title=page_data['title'],
            space_key=page_data.get('space', {}).get('key', self.space_key),
            content=clean_content,
            url=page_url,
            last_modified=page_data.get('version', {}).get('when', ''),
            version=page_data.get('version', {}).get('number', 1)
        )

    def get_page_by_id(self, page_id: str) -> ConfluencePage:
        """
        Fetch a single page by ID.

        Args:
            page_id: Confluence page ID

        Returns:
            ConfluencePage object
        """
        data = self._make_request(
            f"content/{page_id}",
            params={
                "expand": "body.storage,space,version"
            }
        )
        return self._parse_page(data)

    def get_pages_from_space(
        self,
        space_key: Optional[str] = None,
        limit: int = 50,
        include_archived: bool = False
    ) -> List[ConfluencePage]:
        """
        Fetch all pages from a Confluence space.

        Args:
            space_key: Space key (uses default if not specified)
            limit: Maximum number of pages to fetch
            include_archived: Whether to include archived pages

        Returns:
            List of ConfluencePage objects
        """
        space_key = space_key or self.space_key
        if not space_key:
            raise ValueError("Space key must be provided")

        pages = []
        start = 0
        page_size = min(limit, 25)  # API max is 25 per request

        while len(pages) < limit:
            params = {
                "spaceKey": space_key,
                "type": "page",
                "status": "current" if not include_archived else "any",
                "expand": "body.storage,space,version",
                "start": start,
                "limit": page_size
            }

            data = self._make_request("content", params=params)
            results = data.get('results', [])

            if not results:
                break

            for page_data in results:
                pages.append(self._parse_page(page_data))
                if len(pages) >= limit:
                    break

            # Check if there are more pages
            if data.get('size', 0) < page_size:
                break

            start += page_size

        return pages

    def search_pages(
        self,
        query: str,
        space_key: Optional[str] = None,
        limit: int = 20
    ) -> List[ConfluencePage]:
        """
        Search for pages using CQL (Confluence Query Language).

        Args:
            query: Search query or CQL string
            space_key: Limit search to specific space
            limit: Maximum number of results

        Returns:
            List of ConfluencePage objects
        """
        # Build CQL query
        cql_parts = [f'text ~ "{query}"']
        if space_key or self.space_key:
            cql_parts.append(f'space = "{space_key or self.space_key}"')
        cql_parts.append('type = page')

        cql = ' AND '.join(cql_parts)

        params = {
            "cql": cql,
            "expand": "body.storage,space,version",
            "limit": min(limit, 25)
        }

        data = self._make_request("content/search", params=params)
        results = data.get('results', [])

        return [self._parse_page(page_data) for page_data in results]

    def load_documents(
        self,
        space_key: Optional[str] = None,
        page_ids: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        limit: int = 50
    ) -> List[Document]:
        """
        Load Confluence pages as LangChain Documents.

        Args:
            space_key: Fetch all pages from this space
            page_ids: Fetch specific pages by ID
            search_query: Search for pages matching query
            limit: Maximum number of pages to fetch

        Returns:
            List of LangChain Document objects
        """
        pages: List[ConfluencePage] = []

        if page_ids:
            # Fetch specific pages
            for page_id in page_ids:
                try:
                    pages.append(self.get_page_by_id(page_id))
                except Exception as e:
                    print(f"Warning: Could not fetch page {page_id}: {e}")
        elif search_query:
            # Search for pages
            pages = self.search_pages(search_query, space_key=space_key, limit=limit)
        elif space_key or self.space_key:
            # Fetch all pages from space
            pages = self.get_pages_from_space(
                space_key=space_key or self.space_key,
                limit=limit
            )
        else:
            raise ValueError(
                "Must provide space_key, page_ids, or search_query"
            )

        # Convert to LangChain documents
        documents = []
        for page in pages:
            if page.content.strip():  # Skip empty pages
                doc = Document(
                    page_content=page.content,
                    metadata={
                        "source": f"confluence:{page.space_key}/{page.id}",
                        "title": page.title,
                        "url": page.url,
                        "space_key": page.space_key,
                        "page_id": page.id,
                        "last_modified": page.last_modified,
                        "version": page.version,
                        "topic": f"Confluence - {page.space_key}",
                        "type": "confluence"
                    }
                )
                documents.append(doc)

        return documents


def is_confluence_configured() -> bool:
    """Check if Confluence integration is properly configured."""
    return (
        Config.CONFLUENCE_ENABLED and
        bool(Config.CONFLUENCE_URL) and
        bool(Config.CONFLUENCE_USERNAME) and
        bool(Config.CONFLUENCE_API_TOKEN)
    )


def get_confluence_loader() -> Optional[ConfluenceLoader]:
    """Get a ConfluenceLoader instance if configured."""
    if not is_confluence_configured():
        return None
    return ConfluenceLoader()
