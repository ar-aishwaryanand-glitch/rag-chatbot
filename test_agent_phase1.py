#!/usr/bin/env python3
"""
Test script for Phase 1 of the agentic RAG system.

Tests:
- Agent initialization
- Tool registry
- RAG tool integration
- Basic query execution
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.main import initialize_system
from src.agent.agent_executor import AgentExecutor
from src.agent.tool_registry import ToolRegistry
from src.agent.tools.rag_tool import RAGTool


def main():
    """Run Phase 1 tests."""
    print("=" * 80)
    print("PHASE 1 TEST: Basic Agent with RAG Tool")
    print("=" * 80)

    # Step 1: Initialize RAG system
    print("\n[1/5] Initializing RAG system...")
    try:
        rag_chain = initialize_system(rebuild_index=False, use_documents=False)
        print("✓ RAG system initialized")
    except Exception as e:
        print(f"✗ Failed to initialize RAG system: {e}")
        return

    # Step 2: Create tool registry
    print("\n[2/5] Creating tool registry...")
    try:
        tool_registry = ToolRegistry()
        print("✓ Tool registry created")
    except Exception as e:
        print(f"✗ Failed to create tool registry: {e}")
        return

    # Step 3: Register RAG tool
    print("\n[3/5] Registering RAG tool...")
    try:
        rag_tool = RAGTool(rag_chain)
        tool_registry.register(rag_tool)
        print(f"✓ RAG tool registered: {rag_tool.name}")
        print(f"   Description: {rag_tool.description[:80]}...")
    except Exception as e:
        print(f"✗ Failed to register RAG tool: {e}")
        return

    # Step 4: Initialize agent
    print("\n[4/5] Initializing agent executor...")
    try:
        # Get LLM from RAG chain
        llm = rag_chain.llm

        # Create agent
        agent = AgentExecutor(llm, tool_registry, Config)
        print("✓ Agent executor initialized")
        print(f"   Max iterations: {Config.AGENT_MAX_ITERATIONS}")
        print(f"   Tools available: {', '.join(tool_registry.get_tool_names())}")
    except Exception as e:
        print(f"✗ Failed to initialize agent: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 5: Test agent with sample query
    print("\n[5/5] Testing agent with sample query...")
    test_query = "What is Python?"

    print(f"\n📝 Query: \"{test_query}\"")
    print("\n🤖 Agent execution:")
    print("-" * 80)

    try:
        # Execute agent
        result = agent.execute(test_query)

        # Display results
        print(f"\n✓ Agent completed successfully!")
        print(f"\nPhase progression: {result['current_phase']}")
        print(f"Tools used: {', '.join(result['tools_used'])}")
        print(f"Iterations: {result['iteration']}/{result['max_iterations']}")
        print(f"Duration: {result['execution_metadata']['total_duration']:.2f}s")

        print(f"\n💡 Final Answer:")
        print("-" * 80)
        print(result['final_answer'])
        print("-" * 80)

        # Verify results
        print("\n📊 Verification:")
        checks = [
            ("Query processed", result['query'] == test_query),
            ("Tool executed", len(result['tools_used']) > 0),
            ("Answer generated", len(result['final_answer']) > 0),
            ("Completed successfully", result['current_phase'] == 'done'),
            ("No errors", result['last_error'] is None)
        ]

        all_passed = True
        for check_name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False

        if all_passed:
            print("\n🎉 ALL TESTS PASSED! Phase 1 is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Review the output above.")

    except Exception as e:
        print(f"\n✗ Agent execution failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
