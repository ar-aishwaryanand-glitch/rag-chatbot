#!/usr/bin/env python3
"""Quick test for web search tool."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.main import initialize_system
from src.agent.agent_executor import AgentExecutor
from src.agent.tool_registry import ToolRegistry
from src.agent.tools import RAGTool, WebSearchTool

def main():
    """Test web search tool."""
    print("Testing Web Search Agent...")
    print("-" * 60)

    # Initialize system
    print("\n1. Initializing RAG system...")
    rag_chain = initialize_system(rebuild_index=False, use_documents=False)

    # Create tool registry with web search
    print("2. Registering tools...")
    tool_registry = ToolRegistry()
    tool_registry.register(RAGTool(rag_chain))
    tool_registry.register(WebSearchTool(max_results=3))

    # Initialize agent
    print("3. Initializing agent...")
    agent = AgentExecutor(rag_chain.llm, tool_registry, Config)

    # Test web search
    print("\n4. Testing web search...")
    print("-" * 60)

    test_queries = [
        "What is the current weather in New York?",
        "Who won the latest Nobel Prize in Physics?",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n[Test {i}] Query: {query}")
        print("-" * 60)

        try:
            result = agent.execute(query)

            print(f"✓ Tools used: {', '.join(result['tools_used'])}")
            print(f"⏱️  Duration: {result.get('total_duration', 0):.2f}s")
            print(f"\n💬 Answer:")
            print(f"   {result['final_answer'][:300]}...")

            if 'web_search' in result['tools_used']:
                print("\n✅ SUCCESS: Web search tool was used correctly!")
            else:
                print(f"\n⚠️  WARNING: Expected web_search, got {result['tools_used']}")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

        print("-" * 60)

    print("\n✨ Web search test complete!")

if __name__ == "__main__":
    main()
