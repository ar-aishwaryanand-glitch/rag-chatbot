"""Main entry point for RAG Agent POC."""

import sys
from pathlib import Path

from .config import Config
from .data_loader import get_sample_documents, get_document_count
from .document_loader import load_all_documents
from .embeddings import EmbeddingManager
from .vector_store import VectorStoreManager
from .rag_chain import RAGChain

def print_banner():
    """Print welcome banner."""
    print("\n" + "="*80)
    print("🤖  RAG AGENT POC - Retrieval-Augmented Generation System")
    print("="*80)
    print(f"Using: Google Gemini ({Config.LLM_MODEL})")
    print(f"Embedding Model: {Config.EMBEDDING_MODEL}")
    print(f"Vector Store: FAISS")
    print("="*80 + "\n")

def initialize_system(rebuild_index: bool = False, use_documents: bool = False) -> RAGChain:
    """
    Initialize the RAG system.

    Args:
        rebuild_index: If True, rebuild the vector store from scratch

    Returns:
        Initialized RAGChain instance
    """
    print("🚀 Initializing RAG system...\n")

    # Initialize components
    embedding_manager = EmbeddingManager()
    vector_store_manager = VectorStoreManager(embedding_manager)

    # Check if vector store exists
    vector_store_exists = Config.VECTOR_STORE_PATH.exists()

    if rebuild_index or not vector_store_exists:
        if rebuild_index:
            print("🔄 Rebuilding vector store from scratch...")
        else:
            print("📦 No existing vector store found. Creating new one...")

        print("\n⚠️  NOTE: This will call Google's Embedding API.")
        print("   Using rate limiting to stay within free tier limits (1,500 requests/day)")
        print("   Once created, the vector store will be cached and won't need API calls.\n")

        # Load documents based on mode
        if use_documents:
            print("📚 Loading documents from data/documents/ directory...")
            documents = load_all_documents()
            if not documents:
                print("❌ No documents found in data/documents/")
                print("   Please add .txt or .md files to the data/documents/ directory")
                print("   Or run without --use-documents flag to use sample data")
                sys.exit(1)
        else:
            # Load sample documents (using 5 docs initially to minimize API calls)
            doc_limit = 5  # Start with 5 documents to minimize API usage
            print(f"📚 Loading {doc_limit} sample documents (out of {get_document_count()} available)...")
            documents = get_sample_documents(limit=doc_limit)

        # Chunk documents
        print("✂️  Chunking documents...")
        chunks = embedding_manager.chunk_documents(documents)

        # Create vector store with rate limiting (batch_size=3, delay=2s)
        print("🔢 Creating embeddings and building vector store...")
        vector_store_manager.create_vector_store(chunks, batch_size=3, delay=2.0)

        # Save vector store
        vector_store_manager.save_vector_store()
        print("✅ Vector store created and saved!\n")
    else:
        print("📂 Loading existing vector store...")
        vector_store_manager.load_vector_store()
        print("✅ Vector store loaded!\n")

    # Create RAG chain
    rag_chain = RAGChain(vector_store_manager)

    return rag_chain

def run_interactive_mode(rag_chain: RAGChain, use_documents: bool = False):
    """
    Run interactive Q&A loop.

    Args:
        rag_chain: Initialized RAGChain instance
        use_documents: Whether using custom documents or sample data
    """
    print("💬 Interactive Mode")
    print("-" * 80)
    if use_documents:
        print("Ask questions about your documents.")
    else:
        print("Ask questions about Python, AI, Machine Learning, NLP, or RAG systems.")
    print("Commands:")
    print("  - Type 'exit' or 'quit' to stop")
    print("  - Type 'rebuild' to rebuild the vector store")
    if not use_documents:
        print("  - Type 'sample' to see example questions")
    print("-" * 80 + "\n")

    while True:
        try:
            # Get user input
            question = input("❓ Your question: ").strip()

            if not question:
                continue

            # Handle commands
            if question.lower() in ['exit', 'quit']:
                print("\n👋 Goodbye!")
                break

            if question.lower() == 'rebuild':
                print("\n🔄 Rebuilding vector store...")
                # Use the same document source as current session
                import sys
                use_docs = '--use-documents' in sys.argv
                rag_chain = initialize_system(rebuild_index=True, use_documents=use_docs)
                print("✅ Vector store rebuilt! You can continue asking questions.\n")
                continue

            if question.lower() == 'sample':
                show_sample_questions()
                continue

            # Process question with RAG
            result = rag_chain.ask(question)
            rag_chain.display_result(result)

            print("\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again.\n")

def show_sample_questions():
    """Display sample questions users can ask."""
    print("\n📝 Sample Questions:")
    print("-" * 80)
    questions = [
        "What is Python and when was it created?",
        "Explain the difference between machine learning and deep learning",
        "What is RAG and how does it work?",
        "What are vector databases used for?",
        "What is LangChain?",
        "How do embeddings work in NLP?",
        "What are Large Language Models?",
        "What is prompt engineering?",
    ]
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")
    print("-" * 80 + "\n")

def run_demo_questions(rag_chain: RAGChain):
    """
    Run a few demo questions to showcase the system.

    Args:
        rag_chain: Initialized RAGChain instance
    """
    demo_questions = [
        "What is RAG?",
        "How does deep learning differ from machine learning?",
        "What is the capital of France?"  # Out of scope question
    ]

    print("\n🎬 Running Demo Questions")
    print("="*80 + "\n")

    for question in demo_questions:
        result = rag_chain.ask(question)
        rag_chain.display_result(result)
        print("\n")
        input("Press Enter to continue...")

def main():
    """Main entry point."""
    print_banner()

    # Parse command line arguments
    rebuild = '--rebuild' in sys.argv
    demo = '--demo' in sys.argv
    use_documents = '--use-documents' in sys.argv

    try:
        # Initialize system
        rag_chain = initialize_system(rebuild_index=rebuild, use_documents=use_documents)

        # Run demo or interactive mode
        if demo:
            run_demo_questions(rag_chain)
        else:
            run_interactive_mode(rag_chain, use_documents=use_documents)

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
