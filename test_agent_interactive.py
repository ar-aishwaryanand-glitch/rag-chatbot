#!/usr/bin/env python3
"""
Interactive test script for the agentic RAG system.

Run this to chat with the agent and see it use different tools.
"""

import sys
from pathlib import Path

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


def print_separator(char='=', length=70):
    """Print a separator line."""
    print(char * length)


def print_header(text):
    """Print a section header."""
    print_separator()
    print(f"  {text}")
    print_separator()


def print_tool_call(tool_name, duration, success):
    """Print tool call information."""
    status = "✓" if success else "✗"
    print(f"\n  🔧 Tool Used: {tool_name}")
    print(f"  {status} Status: {'Success' if success else 'Failed'}")
    print(f"  ⏱️  Duration: {duration:.2f}s")


def print_result(result):
    """Print agent execution result."""
    print_separator('-')
    print(f"🤖 AGENT RESPONSE:")
    print_separator('-')
    print(f"\n{result['final_answer']}\n")

    if result['tools_used']:
        print_separator('-')
        print(f"📊 EXECUTION DETAILS:")
        print(f"  • Tools used: {', '.join(result['tools_used'])}")
        print(f"  • Iterations: {result['iteration']}")
        print(f"  • Total time: {result.get('total_duration', 0):.2f}s")

        # Show individual tool results
        if result.get('tool_results'):
            print(f"\n  Tool Breakdown:")
            for tool_result in result['tool_results']:
                print_tool_call(
                    tool_result['tool'],
                    tool_result['duration'],
                    tool_result['success']
                )
    print_separator()


def print_welcome():
    """Print welcome message."""
    print_header("🤖 AGENTIC RAG SYSTEM - INTERACTIVE TEST")
    print("""
Welcome to the Agentic RAG System!

This agent has 6 tools at its disposal:
  1. 📚 document_search   - Search indexed documents
  2. 🌐 web_search        - Search the internet
  3. 🧮 calculator        - Perform calculations
  4. 🐍 python_executor   - Execute Python code
  5. 📁 file_operations   - Read/list files
  6. 📊 document_manager  - Manage document collection

The agent will automatically choose the right tool(s) for your query!

Example queries to try:
  • "What is RAG?"                    → document_search
  • "Calculate 45 * 67 + 890"         → calculator
  • "Generate first 10 Fibonacci"     → python_executor
  • "What documents are indexed?"     → document_manager
  • "What's the weather today?"       → web_search

Type 'quit' or 'exit' to stop.
    """)
    print_separator()


def main():
    """Run interactive agent test."""
    print_welcome()

    # Step 1: Initialize RAG system
    print("\n🚀 Initializing RAG system...")
    try:
        rag_chain = initialize_system(rebuild_index=False, use_documents=False)
        vector_store_manager = rag_chain.vector_store_manager
        print("✓ RAG system initialized")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return

    # Step 2: Create and register tools
    print("🔧 Registering tools...")
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
        print(f"✗ Failed to register tools: {e}")
        return

    # Step 3: Initialize agent
    print("🤖 Initializing agent...")
    try:
        llm = rag_chain.llm
        agent = AgentExecutor(llm, tool_registry, Config)
        print("✓ Agent ready!\n")
    except Exception as e:
        print(f"✗ Failed to initialize agent: {e}")
        return

    # Step 4: Interactive loop
    print_separator()
    print("💬 Ready for your questions!\n")

    while True:
        try:
            # Get user input
            query = input("\n🧑 You: ").strip()

            if not query:
                continue

            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break

            # Execute agent
            print(f"\n🤔 Agent thinking...\n")
            result = agent.execute(query)

            # Print result
            print_result(result)

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print()


if __name__ == "__main__":
    main()
