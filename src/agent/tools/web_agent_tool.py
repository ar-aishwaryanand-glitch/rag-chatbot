"""
Web Agent Tool - Autonomous web browsing, extraction, and synthesis.

This tool enables the agent to:
- Visit and navigate websites
- Extract clean content from web pages
- Handle JavaScript-rendered content
- Synthesize information from multiple sources
- Return structured summaries with citations
"""

import asyncio
import time
import ipaddress
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse
import re
import socket

from .base_tool import BaseTool, ToolResult

# Optional imports with fallbacks
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    from readability import Document
    READABILITY_AVAILABLE = True
except ImportError:
    READABILITY_AVAILABLE = False


@dataclass
class WebPage:
    """Represents an extracted web page."""
    url: str
    title: str
    content: str
    extracted_at: datetime = field(default_factory=datetime.now)
    author: Optional[str] = None
    publish_date: Optional[str] = None
    word_count: int = 0
    main_image: Optional[str] = None
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'url': self.url,
            'title': self.title,
            'content': self.content[:500] + '...' if len(self.content) > 500 else self.content,
            'word_count': self.word_count,
            'author': self.author,
            'publish_date': self.publish_date,
            'success': self.success
        }


class WebAgentTool(BaseTool):
    """
    Autonomous web browsing and content extraction tool.

    Capabilities:
    - Visit URLs and extract main content
    - Handle JavaScript-rendered pages
    - Clean and structure extracted content
    - Multi-source research and synthesis
    - Return markdown summaries with citations

    Examples:
        "Visit https://example.com and extract the main content"
        "Research the latest AI news from multiple sources"
        "Extract and summarize information from these 3 URLs"
    """

    # List of user agents to rotate through for retry logic
    USER_AGENTS = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
    ]

    def __init__(self, timeout: int = 30, max_pages: int = 5, max_retries: int = 2, policy_engine=None):
        """
        Initialize Web Agent Tool.

        Args:
            timeout: Page load timeout in seconds
            max_pages: Maximum number of pages to visit in one operation
            max_retries: Maximum number of retries with different user agents
            policy_engine: Optional PolicyEngine instance for URL filtering
        """
        super().__init__()
        self.timeout = timeout * 1000  # Convert to milliseconds
        self.max_pages = max_pages
        self.max_retries = max_retries
        self.policy_engine = policy_engine

        # Check dependencies
        if not PLAYWRIGHT_AVAILABLE:
            self.available = False
            self.error_msg = "Playwright not installed. Install with: pip install playwright && playwright install chromium"
        elif not BS4_AVAILABLE:
            self.available = False
            self.error_msg = "BeautifulSoup4 not installed. Install with: pip install beautifulsoup4"
        else:
            self.available = True
            self.error_msg = None

    @property
    def name(self) -> str:
        """Unique name for the tool."""
        return "web_agent"

    @property
    def description(self) -> str:
        """Description of what the tool does."""
        return (
            "Visit websites and extract full article content with detailed summaries and citations. "
            "Use this tool for comprehensive web research, latest news analysis, detailed information gathering, "
            "or when you need more than just links - actual content from web pages. "
            "Handles JavaScript-rendered pages and provides clean, structured output with proper attribution."
        )

    def _run(self, *args, **kwargs) -> str:
        """Wrapper for the async run method to satisfy BaseTool interface."""
        result = self.run_tool(*args, **kwargs)
        if result.success:
            return result.output
        else:
            raise Exception(result.error or "Web agent execution failed")

    def validate_url(self, url: str, session_id: str = "default") -> tuple[bool, Optional[str]]:
        """
        Validate URL for security (prevent SSRF attacks) and policy compliance.

        Args:
            url: URL to validate
            session_id: Session ID for policy evaluation

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in ['http', 'https']:
                return False, f"Invalid URL scheme '{parsed.scheme}'. Only http and https are allowed."

            # Check for empty or invalid hostname
            if not parsed.netloc:
                return False, "URL must include a hostname"

            # Extract hostname (remove port if present)
            hostname = parsed.netloc.split(':')[0]

            # Block localhost variations
            localhost_variants = ['localhost', '127.0.0.1', '0.0.0.0', '::1', '0:0:0:0:0:0:0:1']
            if hostname.lower() in localhost_variants:
                return False, "Access to localhost is not allowed"

            # Try to resolve hostname and check if it's a private IP
            try:
                # Get IP address
                ip_str = socket.gethostbyname(hostname)
                ip = ipaddress.ip_address(ip_str)

                # Check if it's a private/internal IP
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    return False, f"Access to private/internal IP addresses is not allowed"

                # Block AWS metadata endpoint specifically
                if ip_str == '169.254.169.254':
                    return False, "Access to cloud metadata endpoints is not allowed"

            except socket.gaierror:
                # Could not resolve - might be invalid hostname
                return False, f"Could not resolve hostname: {hostname}"
            except ValueError:
                # Invalid IP address format - but we'll allow it since gethostbyname worked
                pass

            # Check against policy engine if available
            if self.policy_engine and self.policy_engine.is_enabled():
                from ...policy.policy_definitions import PolicyEvaluationContext

                context = PolicyEvaluationContext(
                    session_id=session_id,
                    tool_name=self.name,
                    target_url=url
                )

                decision = self.policy_engine.evaluate_tool_usage(context)
                if not decision.allowed:
                    return False, f"Policy blocked: {decision.message or 'Domain not allowed'}"

            return True, None

        except Exception as e:
            return False, f"URL validation error: {str(e)}"

    def run_tool(self, url: str = None, urls: List[str] = None, query: str = None, session_id: str = "default") -> ToolResult:
        """
        Execute web agent operations.

        Args:
            url: Single URL to visit and extract
            urls: Multiple URLs to visit and synthesize
            query: Research query (will search and visit top results)
            session_id: Session ID for policy evaluation

        Returns:
            ToolResult with extracted content and structured summary
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
            # Determine operation mode
            if url:
                # Validate single URL
                is_valid, error = self.validate_url(url, session_id)
                if not is_valid:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"URL validation failed: {error}",
                        duration=time.time() - start_time
                    )

                # Single URL extraction
                result = asyncio.run(self._extract_single_url(url))
                return result

            elif urls:
                # Validate all URLs
                validated_urls = []
                for u in urls:
                    is_valid, error = self.validate_url(u, session_id)
                    if not is_valid:
                        print(f"⚠️ Skipping {u}: {error}")
                        continue  # Skip blocked URLs instead of failing entirely
                    validated_urls.append(u)

                if not validated_urls:
                    return ToolResult(
                        success=False,
                        output="",
                        error="All URLs were blocked by policy or validation",
                        duration=time.time() - start_time
                    )

                # Multi-URL synthesis
                result = asyncio.run(self._extract_multiple_urls(validated_urls))
                return result

            elif query:
                # Research mode (search + extract)
                return ToolResult(
                    success=False,
                    output="",
                    error="Research mode requires web_search tool integration. Use web_search first, then pass URLs to web_agent.",
                    duration=time.time() - start_time
                )
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error="Must provide either 'url', 'urls', or 'query' parameter",
                    duration=time.time() - start_time
                )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Web agent error: {str(e)}",
                duration=time.time() - start_time
            )

    async def _extract_single_url(self, url: str) -> ToolResult:
        """
        Extract content from a single URL.

        Args:
            url: URL to visit

        Returns:
            ToolResult with extracted content
        """
        start_time = time.time()

        try:
            # Fetch and extract
            page = await self._fetch_and_extract(url)

            if not page.success:
                return ToolResult(
                    success=False,
                    output="",
                    error=page.error,
                    duration=time.time() - start_time
                )

            # Format output
            output = self._format_single_page(page)

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
                error=f"Failed to extract from {url}: {str(e)}",
                duration=time.time() - start_time
            )

    async def _extract_multiple_urls(self, urls: List[str]) -> ToolResult:
        """
        Extract and synthesize content from multiple URLs.

        Args:
            urls: List of URLs to visit

        Returns:
            ToolResult with synthesized content
        """
        start_time = time.time()

        # Limit number of pages
        urls = urls[:self.max_pages]

        try:
            # Fetch all pages concurrently
            tasks = [self._fetch_and_extract(url) for url in urls]
            pages = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter successful extractions
            successful_pages = [
                p for p in pages
                if isinstance(p, WebPage) and p.success
            ]

            if not successful_pages:
                return ToolResult(
                    success=False,
                    output="",
                    error="Failed to extract content from any of the provided URLs",
                    duration=time.time() - start_time
                )

            # Format synthesized output
            output = self._format_multiple_pages(successful_pages)

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
                error=f"Failed to extract from multiple URLs: {str(e)}",
                duration=time.time() - start_time
            )

    async def _fetch_and_extract(self, url: str, retry_attempt: int = 0) -> WebPage:
        """
        Fetch a URL and extract its main content with retry logic.

        Args:
            url: URL to fetch
            retry_attempt: Current retry attempt number

        Returns:
            WebPage object with extracted content
        """
        user_agent = self.USER_AGENTS[retry_attempt % len(self.USER_AGENTS)]

        try:
            async with async_playwright() as p:
                # Launch browser with stealth mode
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox'
                    ]
                )

                # Create context with realistic browser fingerprint
                context = await browser.new_context(
                    user_agent=user_agent,
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US',
                    timezone_id='America/New_York',
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Cache-Control': 'max-age=0'
                    }
                )

                page = await context.new_page()

                # Add script to hide webdriver property
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)

                # Navigate to URL
                try:
                    response = await page.goto(url, timeout=self.timeout, wait_until='domcontentloaded')

                    # Check for 403 error
                    if response and response.status == 403:
                        await browser.close()

                        # Retry with different user agent if attempts remaining
                        if retry_attempt < self.max_retries:
                            print(f"⚠️ 403 Forbidden on {url}, retrying with different user agent (attempt {retry_attempt + 1}/{self.max_retries})")
                            await asyncio.sleep(1)  # Brief delay before retry
                            return await self._fetch_and_extract(url, retry_attempt + 1)
                        else:
                            return WebPage(
                                url=url,
                                title="403 - Forbidden",
                                content="Access to this page is forbidden.",
                                success=False,
                                error=f"403 Forbidden: Access denied after {self.max_retries + 1} attempts"
                            )

                except PlaywrightTimeout:
                    await browser.close()
                    return WebPage(
                        url=url,
                        title="",
                        content="",
                        success=False,
                        error=f"Timeout: Page took longer than {self.timeout/1000}s to load"
                    )

                # Wait a bit for dynamic content
                await page.wait_for_timeout(1000)

                # Get page content
                html = await page.content()

                # Close browser
                await browser.close()

            # Extract main content
            extracted = self._extract_content(html, url)

            return extracted

        except Exception as e:
            # Retry on certain exceptions if attempts remaining
            if retry_attempt < self.max_retries and ("403" in str(e) or "forbidden" in str(e).lower()):
                print(f"⚠️ Error fetching {url}: {str(e)}, retrying (attempt {retry_attempt + 1}/{self.max_retries})")
                await asyncio.sleep(1)
                return await self._fetch_and_extract(url, retry_attempt + 1)

            return WebPage(
                url=url,
                title="",
                content="",
                success=False,
                error=f"Failed to fetch: {str(e)}"
            )

    def _extract_content(self, html: str, url: str) -> WebPage:
        """
        Extract main content from HTML.

        Args:
            html: HTML content
            url: Source URL

        Returns:
            WebPage with extracted content
        """
        try:
            # Try readability first (best for articles)
            if READABILITY_AVAILABLE:
                doc = Document(html)
                title = doc.title()
                content_html = doc.summary()
            else:
                # Fallback to BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                title = soup.title.string if soup.title else "Untitled"

                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()

                content_html = str(soup.body) if soup.body else str(soup)

            # Parse with BeautifulSoup to extract text
            soup = BeautifulSoup(content_html, 'html.parser')

            # Extract text
            text = soup.get_text(separator='\n', strip=True)

            # Clean up text
            text = self._clean_text(text)

            # Extract metadata
            metadata = self._extract_metadata(soup)

            return WebPage(
                url=url,
                title=title,
                content=text,
                word_count=len(text.split()),
                author=metadata.get('author'),
                publish_date=metadata.get('date'),
                main_image=metadata.get('image'),
                success=True
            )

        except Exception as e:
            return WebPage(
                url=url,
                title="",
                content="",
                success=False,
                error=f"Content extraction failed: {str(e)}"
            )

    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        # Remove very short lines (likely navigation/UI elements)
        lines = text.split('\n')
        cleaned_lines = [line for line in lines if len(line.strip()) > 20 or line.strip() == '']
        text = '\n'.join(cleaned_lines)

        return text.strip()

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        """Extract metadata from HTML."""
        metadata = {
            'author': None,
            'date': None,
            'image': None
        }

        # Try to find author
        author_meta = soup.find('meta', attrs={'name': 'author'})
        if author_meta:
            metadata['author'] = author_meta.get('content')

        # Try to find publish date
        date_meta = soup.find('meta', attrs={'property': 'article:published_time'})
        if date_meta:
            metadata['date'] = date_meta.get('content')

        # Try to find main image
        image_meta = soup.find('meta', attrs={'property': 'og:image'})
        if image_meta:
            metadata['image'] = image_meta.get('content')

        return metadata

    def _format_single_page(self, page: WebPage) -> str:
        """Format a single page extraction."""
        output = f"""# {page.title}

**Source:** {page.url}
**Word Count:** {page.word_count}
"""
        if page.author:
            output += f"**Author:** {page.author}\n"
        if page.publish_date:
            output += f"**Published:** {page.publish_date}\n"

        output += f"\n## Content\n\n{page.content}\n"

        return output

    def _format_multiple_pages(self, pages: List[WebPage]) -> str:
        """Format multiple page extractions with synthesis."""
        output = f"# Web Research Summary\n\n"
        output += f"**Sources Analyzed:** {len(pages)}\n"
        output += f"**Extracted:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

        output += "## Key Information Across Sources\n\n"

        for i, page in enumerate(pages, 1):
            output += f"### Source {i}: {page.title}\n\n"
            output += f"**URL:** {page.url}\n"
            output += f"**Word Count:** {page.word_count}\n"
            if page.author:
                output += f"**Author:** {page.author}\n"
            output += f"\n**Content Preview:**\n\n"

            # Limit content preview for multiple pages
            preview = page.content[:800] + "..." if len(page.content) > 800 else page.content
            output += f"{preview}\n\n"
            output += "---\n\n"

        output += "## Citations\n\n"
        for i, page in enumerate(pages, 1):
            output += f"{i}. [{page.title}]({page.url})\n"

        return output

    def get_usage_examples(self) -> List[str]:
        """Return example usage patterns."""
        return [
            "Visit https://openai.com/research and extract the main content",
            "Extract and summarize information from these URLs: [url1, url2, url3]",
            "Get the article content from https://techcrunch.com/ai-news",
            "Visit the documentation page and extract all the information"
        ]
