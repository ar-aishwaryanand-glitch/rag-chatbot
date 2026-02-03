"""
Test script for article relevance filtering.

This demonstrates how the NewsApiTool filters out irrelevant articles.
"""

import os
from src.agent.tools.news_api_tool import NewsApiTool


def test_relevance_filtering():
    """Test relevance filtering with a specific query."""

    print("=" * 70)
    print("Testing News API Article Relevance Filtering")
    print("=" * 70)
    print()

    # Initialize NewsAPI tool with relevance filtering enabled
    print("Initializing NewsApiTool with relevance filtering...")
    news_api = NewsApiTool(filter_irrelevant=True)

    if not news_api.available:
        print(f"❌ NewsAPI not available: {news_api.error_msg}")
        return

    print(f"✓ Using: {news_api.service}")
    print(f"✓ Relevance filtering: {'LLM-based' if news_api.llm_client else 'Keyword-based'}")
    print()

    # Test with a specific query
    test_query = "artificial intelligence in healthcare"
    print(f"Query: '{test_query}'")
    print("-" * 70)
    print()

    # Fetch and filter articles
    result = news_api.run_tool(
        query=test_query,
        max_results=5,
        days_back=7
    )

    if result.success:
        print(result.output)
        print()
        print("=" * 70)
        print(f"✓ Query completed in {result.duration:.2f}s")
        print("=" * 70)
    else:
        print(f"❌ Error: {result.error}")


def test_without_filtering():
    """Test without relevance filtering for comparison."""

    print("\n\n")
    print("=" * 70)
    print("Testing WITHOUT Relevance Filtering (for comparison)")
    print("=" * 70)
    print()

    # Initialize without filtering
    news_api = NewsApiTool(filter_irrelevant=False)

    if not news_api.available:
        print(f"❌ NewsAPI not available: {news_api.error_msg}")
        return

    print(f"✓ Using: {news_api.service}")
    print(f"✓ Relevance filtering: Disabled")
    print()

    # Test with same query
    test_query = "artificial intelligence in healthcare"
    print(f"Query: '{test_query}'")
    print("-" * 70)
    print()

    # Fetch articles without filtering
    result = news_api.run_tool(
        query=test_query,
        max_results=5,
        days_back=7
    )

    if result.success:
        # Just show article titles
        lines = result.output.split('\n')
        for line in lines:
            if line.startswith('## '):
                print(line)
        print()
        print("=" * 70)
        print(f"✓ Query completed in {result.duration:.2f}s")
        print("=" * 70)
    else:
        print(f"❌ Error: {result.error}")


if __name__ == "__main__":
    # Test with filtering
    test_relevance_filtering()

    # Test without filtering (for comparison)
    test_without_filtering()

    print("\n")
    print("=" * 70)
    print("Summary:")
    print("- With filtering: Only shows articles relevant to the query")
    print("- Without filtering: Shows all articles returned by the API")
    print("- Filtering uses LLM if available, otherwise keyword matching")
    print("=" * 70)
