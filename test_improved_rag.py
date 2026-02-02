#!/usr/bin/env python3
"""Quick test to verify improved RAG with new documents."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.main import initialize_system

def main():
    print("Testing Improved RAG with New Documents")
    print("=" * 60)

    # Initialize system
    rag_chain = initialize_system(rebuild_index=False, use_documents=True)

    # Test queries that should now have better answers
    test_queries = [
        "What is RAG?",
        "How do AI agents work?",
        "What are LLMs?",
        "Explain retrieval augmented generation"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n[Query {i}] {query}")
        print("-" * 60)

        result = rag_chain.ask(query)

        answer = result['answer'][:400] + "..." if len(result['answer']) > 400 else result['answer']
        print(f"Answer: {answer}")
        print(f"Sources: {len(result.get('sources', []))} chunks retrieved")
        print()

    print("=" * 60)
    print("✅ RAG testing complete! Answers should be much better now.")

if __name__ == "__main__":
    main()
