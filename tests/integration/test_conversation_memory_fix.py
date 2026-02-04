"""
Test script to verify conversation memory persistence with thread_id.

This tests that conversation context is restored from checkpoints when using the same thread_id.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.embeddings import EmbeddingManager
from src.vector_store import VectorStoreManager
from src.agent.tool_registry import ToolRegistry
from src.agent.tools.rag_tool import RAGTool
from src.agent.tools.calculator_tool import CalculatorTool
from src.agent.agent_executor_v3 import AgentExecutorV3
from src.rag_chain import RAGChain
import time


def test_conversation_memory_persistence():
    """Test that conversation memory persists across queries with same thread_id."""

    print("="*80)
    print("TEST: CONVERSATION MEMORY PERSISTENCE WITH THREAD_ID")
    print("="*80)

    # Initialize system
    print("\n🔧 Initializing agent system...")

    # Setup RAG system
    embedding_manager = EmbeddingManager()
    vector_store_manager = VectorStoreManager(embedding_manager)
    rag_chain = RAGChain(vector_store_manager)

    # Get LLM from RAG chain
    llm = rag_chain.llm

    # Create tool registry
    tool_registry = ToolRegistry()
    tool_registry.register(RAGTool(rag_chain))
    tool_registry.register(CalculatorTool())

    # Create agent with memory enabled
    agent = AgentExecutorV3(
        llm=llm,
        tool_registry=tool_registry,
        config=Config,
        enable_memory=True,
        enable_reflection=False,
        enable_checkpoints=True
    )

    # Test with a unique thread_id
    thread_id = f"test_{int(time.time())}"
    print(f"📝 Using thread_id: {thread_id}")

    # Query 1: Initial query
    print("\n" + "="*80)
    print("QUERY 1: Setting context")
    print("="*80)

    query1 = "My name is Alice and I like machine learning."
    print(f"\nUser: {query1}")

    result1 = agent.execute(query1, thread_id=thread_id)
    print(f"\nAssistant: {result1['final_answer']}")
    print(f"Memory context: {result1.get('memory_context', 'None')[:200]}...")

    # Query 2: Reference previous conversation
    print("\n" + "="*80)
    print("QUERY 2: Testing memory recall")
    print("="*80)

    time.sleep(1)  # Small delay to ensure checkpoint is written

    query2 = "What is my name and what do I like?"
    print(f"\nUser: {query2}")

    result2 = agent.execute(query2, thread_id=thread_id)
    print(f"\nAssistant: {result2['final_answer']}")
    print(f"Memory context: {result2.get('memory_context', 'None')[:500]}...")

    # Verify conversation was restored
    if result2.get('conversation_messages'):
        print(f"\n✅ Conversation messages restored: {len(result2['conversation_messages'])} messages")
        for i, msg in enumerate(result2['conversation_messages'], 1):
            print(f"   {i}. [{msg['role']}] {msg['content'][:80]}...")
    else:
        print("\n❌ No conversation messages found in state!")

    # Query 3: More complex reference
    print("\n" + "="*80)
    print("QUERY 3: Testing deeper memory")
    print("="*80)

    time.sleep(1)

    query3 = "Based on our conversation, recommend a topic I should study"
    print(f"\nUser: {query3}")

    result3 = agent.execute(query3, thread_id=thread_id)
    print(f"\nAssistant: {result3['final_answer']}")

    # Check if response references previous context
    answer_lower = result3['final_answer'].lower()
    memory_works = any(keyword in answer_lower for keyword in ['alice', 'machine learning', 'ml', 'your name'])

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    if result2.get('conversation_messages') and len(result2['conversation_messages']) >= 2:
        print("✅ Conversation messages restored from checkpoint")
    else:
        print("❌ Conversation messages NOT restored")

    if memory_works:
        print("✅ Agent remembers previous conversation context")
    else:
        print("⚠️  Agent may not be using previous context (check answer)")

    print(f"\nTotal messages in conversation: {len(result3.get('conversation_messages', []))}")

    return result2.get('conversation_messages') and len(result2['conversation_messages']) >= 2


if __name__ == "__main__":
    try:
        success = test_conversation_memory_persistence()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
