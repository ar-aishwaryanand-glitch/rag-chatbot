"""URL content fetching and processing for Streamlit UI.

This module handles fetching content from URLs using the web agent,
saving it to the upload directory, and integrating it with the vector store.
"""

import os
from pathlib import Path
from typing import Tuple
import streamlit as st
import re
from urllib.parse import urlparse


# Upload directory (same as document uploads)
PROJECT_ROOT = Path(__file__).parent.parent.parent
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploaded"


def ensure_upload_dir():
    """Ensure upload directory exists."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate URL format.

    Args:
        url: URL string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"

    url = url.strip()

    # Basic URL pattern check
    url_pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
    if not re.match(url_pattern, url):
        return False, "Invalid URL format. Must start with http:// or https://"

    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return False, "Invalid URL: No domain found"
        return True, ""
    except Exception as e:
        return False, f"Invalid URL: {str(e)}"


def sanitize_url_for_filename(url: str) -> str:
    """
    Convert URL to a safe filename.

    Args:
        url: URL to convert

    Returns:
        Safe filename derived from URL
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        path = parsed.path.strip('/').replace('/', '_')

        # Create filename from domain + path
        if path:
            filename = f"{domain}_{path}"
        else:
            filename = domain

        # Remove special characters
        filename = re.sub(r'[^\w\s.-]', '_', filename)

        # Limit length
        if len(filename) > 100:
            filename = filename[:100]

        # Add extension
        filename = f"{filename}.txt"

        return filename

    except Exception:
        return "web_content.txt"


def fetch_url_content(url: str) -> Tuple[bool, str, str]:
    """
    Fetch content from URL using web agent.

    Args:
        url: URL to fetch

    Returns:
        Tuple of (success, content, error_message)
    """
    try:
        from src.agent.tools.web_agent_tool import WebAgentTool

        web_agent = WebAgentTool(timeout=30)
        result = web_agent.run_tool(url=url)

        if result.success:
            return True, result.output, ""
        else:
            return False, "", result.error or "Failed to fetch URL content"

    except ImportError as e:
        return False, "", "Web agent not available. Please install playwright: pip install playwright && playwright install chromium"
    except Exception as e:
        return False, "", f"Error fetching URL: {str(e)}"


def save_url_content(url: str) -> Tuple[bool, str]:
    """
    Fetch URL content and save to upload directory.

    Args:
        url: URL to fetch and save

    Returns:
        Tuple of (success, message)
    """
    ensure_upload_dir()

    # Validate URL
    is_valid, error_msg = validate_url(url)
    if not is_valid:
        return False, error_msg

    # Fetch content
    success, content, error_msg = fetch_url_content(url)
    if not success:
        return False, error_msg

    # Generate filename
    filename = sanitize_url_for_filename(url)
    file_path = UPLOAD_DIR / filename

    # Handle duplicates
    if file_path.exists():
        stem = file_path.stem
        counter = 1
        while file_path.exists():
            file_path = UPLOAD_DIR / f"{stem}_{counter}.txt"
            counter += 1

    # Save content with metadata header
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Source URL: {url}\n")
            f.write(f"=" * 80 + "\n\n")
            f.write(content)

        return True, f"Successfully saved content from {url} as {file_path.name}"

    except Exception as e:
        return False, f"Error saving file: {str(e)}"


def handle_url_submission(url: str) -> bool:
    """
    Handle URL submission from UI.

    Fetches content and triggers rebuild if successful.

    Args:
        url: URL submitted by user

    Returns:
        True if successful, False otherwise
    """
    success, message = save_url_content(url)

    if success:
        st.success(f"✅ {message}")
        st.info("💡 Rebuild vector store to index new content")

        # Update session state
        if 'url_sources' not in st.session_state:
            st.session_state.url_sources = []
        st.session_state.url_sources.append(url)

        # Mark rebuild as pending
        st.session_state.rebuild_pending = True

        return True
    else:
        st.error(f"❌ {message}")
        return False
