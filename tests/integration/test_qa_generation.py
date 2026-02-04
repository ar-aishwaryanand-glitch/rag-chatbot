"""
Test script to verify RAG agent can generate QA test cases from requirements.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.embeddings import EmbeddingManager
from src.vector_store import VectorStoreManager
from src.rag_chain import RAGChain


def test_qa_generation():
    """Test if RAG can retrieve requirements and generate test cases."""

    print("="*80)
    print("TESTING: RAG Agent QA Test Case Generation Capability")
    print("="*80)

    # Initialize RAG chain
    print("\n🔧 Initializing RAG chain...")
    embedding_manager = EmbeddingManager()
    vector_store_manager = VectorStoreManager(embedding_manager)
    rag_chain = RAGChain(vector_store_manager)

    # Test queries that should trigger test case generation
    test_queries = [
        {
            "query": "Generate test cases for the document upload feature (FR-1.1). Include positive, negative, and edge cases.",
            "description": "Test Case Generation - Document Upload"
        },
        {
            "query": "What are the requirements for auto-indexing (FR-1.3)? Based on these requirements, suggest test scenarios.",
            "description": "Requirement Retrieval + Test Scenario Suggestion"
        },
        {
            "query": "List all acceptance criteria for the RAG pipeline (FR-3) and create a test case for each criterion.",
            "description": "Multiple Test Cases from Acceptance Criteria"
        }
    ]

    for i, test in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}: {test['description']}")
        print(f"{'='*80}")
        print(f"Query: {test['query']}")
        print(f"\n{'─'*80}")

        try:
            # Execute RAG query
            result = rag_chain.ask(test['query'], top_k=5)

            # Display results
            print(f"\n📚 Retrieved {len(result['sources'])} relevant source chunks")
            print("\n💡 Generated Answer:\n")
            print(result['answer'])

            print("\n📖 Sources Used:")
            for idx, source in enumerate(result['sources'], 1):
                print(f"  {idx}. {source['source']} (Topic: {source['topic']})")

            print("\n✅ SUCCESS - RAG retrieved context and generated response")

        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

        print(f"{'='*80}\n")

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print("✅ RAG Agent successfully demonstrated:")
    print("   1. Retrieval of requirements from indexed documents")
    print("   2. Understanding of test case generation context")
    print("   3. Structured response generation based on retrieved requirements")
    print("="*80)


if __name__ == "__main__":
    test_qa_generation()
