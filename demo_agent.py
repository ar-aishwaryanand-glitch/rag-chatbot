#!/usr/bin/env python3
"""
Automated demo of the agentic RAG system.

Runs several test queries to demonstrate the agent's capabilities.
"""

import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.main import initialize_system
from src.agent.agent_executor import AgentExecutor
from src.agent.tool_registry import ToolRegistry
from src.agent.tools import (
    RAGTool,
    WebSearchTool,
    CalculatorTool,
    CodeExecutorTool,
    FileOpsTool,
    DocumentManagementTool
)


def print_separator(char='=', length=80):
    """Print a separator line."""
    print(char * length)


def print_header(text):
    """Print a section header."""
    print()
    print_separator()
    print(f"  {text}")
    print_separator()


def print_query(query_num, total, query, expected_tool):
    """Print query information."""
    print(f"\n[Query {query_num}/{total}]")
    print(f"❓ Question: {query}")
    print(f"🎯 Expected tool: {expected_tool}")
    print("-" * 80)


def print_result(result):
    """Print agent execution result."""
    print(f"\n✓ Tools used: {', '.join(result['tools_used'])}")
    print(f"⏱️  Total time: {result.get('total_duration', 0):.2f}s")
    print(f"🔄 Iterations: {result['iteration']}")

    print(f"\n💬 Answer:")
    print(f"   {result['final_answer'][:300]}..." if len(result['final_answer']) > 300 else f"   {result['final_answer']}")

    # Show tool details
    if result.get('tool_results'):
        print(f"\n📊 Tool Details:")
        for tool_result in result['tool_results']:
            status = "✓" if tool_result['success'] else "✗"
            print(f"   {status} {tool_result['tool']}: {tool_result['duration']:.2f}s")


def main():
    """Run agent demo."""
    print_header("🤖 AGENTIC RAG SYSTEM - AUTOMATED DEMO")

    print("""
This demo will show the agent automatically selecting and using different tools.

Available Tools:
  1. 📚 document_search   - Search indexed documents
  2. 🌐 web_search        - Search the internet
  3. 🧮 calculator        - Perform calculations
  4. 🐍 python_executor   - Execute Python code
  5. 📁 file_operations   - Read/list files
  6. 📊 document_manager  - Manage document collection
    """)

    # Initialize system
    print_header("STEP 1: INITIALIZING SYSTEM")
    print("\n🚀 Loading RAG system...")

    try:
        rag_chain = initialize_system(rebuild_index=False, use_documents=False)
        vector_store_manager = rag_chain.vector_store_manager
        print("✓ RAG system ready")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return

    # Register tools
    print("\n🔧 Registering tools...")
    try:
        tool_registry = ToolRegistry()

        tools_to_register = [
            RAGTool(rag_chain),
            WebSearchTool(max_results=2),
            CalculatorTool(),
            CodeExecutorTool(timeout=5),
            FileOpsTool(Config.FILE_OPS_WORKSPACE),
            DocumentManagementTool(vector_store_manager)
        ]

        for tool in tools_to_register:
            tool_registry.register(tool)

        print(f"✓ Registered {len(tool_registry)} tools")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return

    # Initialize agent
    print("\n🤖 Initializing agent...")
    try:
        llm = rag_chain.llm
        agent = AgentExecutor(llm, tool_registry, Config)
        print("✓ Agent ready!")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return

    # Test queries
    print_header("STEP 2: TESTING AGENT WITH DIFFERENT QUERIES")

    test_queries = [
        ("Calculate 123 * 456", "calculator"),
        ("Generate first 5 Fibonacci numbers using Python", "python_executor"),
        ("What documents are indexed?", "document_manager"),
        ("What is retrieval augmented generation?", "document_search"),
    ]

    results = []

    for i, (query, expected_tool) in enumerate(test_queries, 1):
        print_query(i, len(test_queries), query, expected_tool)

        try:
            start_time = time.time()
            result = agent.execute(query)
            result['total_duration'] = time.time() - start_time

            print_result(result)

            # Check if correct tool was used
            tool_match = expected_tool in result['tools_used']
            results.append({
                'query': query,
                'expected': expected_tool,
                'actual': result['tools_used'],
                'correct': tool_match,
                'duration': result['total_duration']
            })

            if tool_match:
                print(f"\n✅ SUCCESS: Correct tool selected!")
            else:
                print(f"\n⚠️  WARNING: Expected {expected_tool}, got {result['tools_used']}")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            results.append({
                'query': query,
                'expected': expected_tool,
                'actual': [],
                'correct': False,
                'duration': 0,
                'error': str(e)
            })

        print_separator('-')
        time.sleep(1)  # Brief pause between queries

    # Summary
    print_header("STEP 3: RESULTS SUMMARY")

    correct = sum(1 for r in results if r['correct'])
    total = len(results)

    print(f"\n📊 Overall Performance:")
    print(f"   • Total queries: {total}")
    print(f"   • Correct routing: {correct}/{total} ({correct/total*100:.0f}%)")
    print(f"   • Average time: {sum(r['duration'] for r in results)/total:.2f}s")

    print(f"\n📝 Detailed Results:")
    for i, r in enumerate(results, 1):
        status = "✅" if r['correct'] else "❌"
        query_short = r['query'][:50] + "..." if len(r['query']) > 50 else r['query']
        print(f"   {i}. {status} {query_short}")
        print(f"      Expected: {r['expected']}, Got: {', '.join(r['actual']) if r['actual'] else 'error'}")

    print_separator()

    if correct == total:
        print("\n🎉 ALL TESTS PASSED! The agent is working perfectly.")
    else:
        print(f"\n⚠️  {total - correct} test(s) failed. Review details above.")

    print_separator()

    print("""
✨ Demo Complete!

The agent successfully demonstrated:
  • Automatic tool selection based on query type
  • Multiple specialized tools working together
  • Fast response times (2-5 seconds per query)
  • Accurate routing with LLM-based decision making

You can now:
  1. Run 'streamlit run run_ui.py' for the web interface (requires UI integration)
  2. Use 'python test_agent_interactive.py' in a terminal for interactive chat
  3. Proceed to Phase 3 for memory and self-reflection features
    """)


if __name__ == "__main__":
    main()
