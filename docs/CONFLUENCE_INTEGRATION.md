# Confluence Integration Guide

This guide explains how to set up and use Confluence integration to import documentation from Atlassian Confluence into your RAG knowledge base.

## Prerequisites

- An Atlassian account with access to Confluence
- An API token from Atlassian
- Read access to the Confluence spaces you want to import

## Setup

### 1. Generate an API Token

1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token**
3. Give it a descriptive name (e.g., "RAG Chatbot")
4. Copy the generated token (you won't be able to see it again)

### 2. Configure Environment Variables

Add the following to your `.env` file:

```bash
# Enable Confluence integration
CONFLUENCE_ENABLED=true

# Your Confluence instance URL
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki

# Your Atlassian email
CONFLUENCE_USERNAME=your-email@example.com

# API token from step 1 (NEVER commit this to git!)
CONFLUENCE_API_TOKEN=your_api_token_here

# Default space key (optional)
CONFLUENCE_SPACE_KEY=DOCS
```

### 3. Find Your Space Key

The space key is the short identifier for a Confluence space:
- Look at any page URL: `https://your-domain.atlassian.net/wiki/spaces/DOCS/...`
- The space key here is `DOCS`
- You can also find it in Space Settings > Space Details

## Usage

### Via Streamlit UI

1. Start the application: `streamlit run src/ui/streamlit_app_agent.py`
2. In the sidebar, find the **Confluence Import** section
3. Choose a fetch mode:
   - **All pages from space**: Fetches all pages from a space (with limit)
   - **Search pages**: Search for pages containing specific terms
   - **Specific page ID**: Fetch a single page by its ID
4. Click **Fetch from Confluence**
5. Pages are automatically chunked and indexed into the vector store

### Via Python Code

```python
from src.confluence_loader import ConfluenceLoader, is_confluence_configured

# Check if configured
if is_confluence_configured():
    loader = ConfluenceLoader()

    # Fetch all pages from a space
    documents = loader.load_documents(space_key="DOCS", limit=50)

    # Search for specific pages
    documents = loader.load_documents(
        search_query="API documentation",
        space_key="DOCS",
        limit=20
    )

    # Fetch a specific page by ID
    documents = loader.load_documents(page_ids=["12345678"])

    # Now add to your document manager
    from src.document_manager import DocumentManager
    doc_manager = DocumentManager()
    doc_manager.add_documents(documents)
    doc_manager.save()
```

### Available Methods

The `ConfluenceLoader` class provides:

| Method | Description |
|--------|-------------|
| `get_page_by_id(page_id)` | Fetch a single page by ID |
| `get_pages_from_space(space_key, limit)` | Fetch all pages from a space |
| `search_pages(query, space_key, limit)` | Search pages using CQL |
| `load_documents(...)` | Unified method that returns LangChain Documents |

## Document Metadata

Imported Confluence documents include the following metadata:

```python
{
    "source": "confluence:SPACE/page_id",
    "title": "Page Title",
    "url": "https://your-domain.atlassian.net/wiki/...",
    "space_key": "SPACE",
    "page_id": "12345678",
    "last_modified": "2024-01-15T10:30:00.000Z",
    "version": 5,
    "topic": "Confluence - SPACE",
    "type": "confluence"
}
```

## Security Best Practices

1. **Never commit API tokens** to version control
2. **Use environment variables** for all credentials
3. **Rotate tokens periodically** (every 90 days recommended)
4. **Use read-only access** when possible
5. **Revoke tokens immediately** if exposed

## Troubleshooting

### Authentication Failed (401)

- Verify your email and API token are correct
- Ensure there are no extra spaces in credentials
- Check that the token hasn't expired or been revoked

### Access Denied (403)

- Verify you have read access to the space
- Check if the space has restricted permissions
- Ensure your token has the required scopes

### No Pages Found

- Verify the space key is correct (case-sensitive)
- Check if pages exist and aren't archived
- Try searching with broader terms

### Connection Timeout

- Check your internet connection
- Verify the Confluence URL is correct
- Ensure no firewall is blocking the connection

## Rate Limits

Atlassian imposes rate limits on API requests:

- ~100 requests per minute for standard accounts
- The loader automatically paginates large requests
- Consider using smaller batch sizes for large spaces

## Support

For issues with this integration:
1. Check the troubleshooting section above
2. Verify your `.env` configuration
3. Check Confluence API documentation: https://developer.atlassian.com/cloud/confluence/rest/
