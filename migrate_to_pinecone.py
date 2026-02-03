"""
Script to migrate vectors from FAISS to Pinecone.

This script helps you migrate your existing FAISS vector store to Pinecone
for production deployment.

Usage:
    python migrate_to_pinecone.py

Requirements:
    - Existing FAISS vector store in data/vector_store/
    - Pinecone API key configured in .env
    - USE_PINECONE=false (script will validate this)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import Config
from src.embeddings import EmbeddingManager
from src.vector_store import VectorStoreManager
from src.vector_store_pinecone import PineconeVectorStoreManager
from langchain_core.documents import Document


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80 + "\n")


def validate_configuration():
    """Validate that configuration is correct for migration."""
    print("🔍 Validating configuration...")

    # Check FAISS vector store exists
    faiss_path = Config.VECTOR_STORE_PATH
    if not faiss_path.exists():
        print(f"❌ FAISS vector store not found at: {faiss_path}")
        print("   Create a FAISS vector store first before migrating")
        return False

    # Check Pinecone API key
    if not Config.PINECONE_API_KEY:
        print("❌ PINECONE_API_KEY not found in .env")
        print("   Get your API key from https://app.pinecone.io")
        return False

    # Warn if USE_PINECONE is already true
    if Config.USE_PINECONE:
        print("⚠️  Warning: USE_PINECONE is already set to true")
        response = input("   Continue with migration anyway? (y/n): ")
        if response.lower() != 'y':
            return False

    print("✅ Configuration validated")
    return True


def load_faiss_documents(faiss_manager: VectorStoreManager) -> list:
    """
    Load all documents from FAISS vector store.

    Args:
        faiss_manager: FAISS vector store manager

    Returns:
        List of documents with embeddings
    """
    print("📖 Loading documents from FAISS...")

    try:
        # Load FAISS vector store
        faiss_manager.load_vector_store()

        # Get the FAISS index
        vectorstore = faiss_manager.vector_store

        # Extract all documents
        # FAISS stores documents in docstore
        docstore = vectorstore.docstore._dict

        documents = []
        for doc_id, doc in docstore.items():
            documents.append(doc)

        print(f"✅ Loaded {len(documents)} documents from FAISS")
        return documents

    except Exception as e:
        print(f"❌ Failed to load FAISS documents: {e}")
        return []


def migrate_to_pinecone(documents: list, pinecone_manager: PineconeVectorStoreManager):
    """
    Migrate documents to Pinecone.

    Args:
        documents: List of documents to migrate
        pinecone_manager: Pinecone vector store manager
    """
    print(f"📤 Migrating {len(documents)} documents to Pinecone...")

    try:
        # Add documents to Pinecone in batches
        ids = pinecone_manager.add_documents(
            documents,
            batch_size=100,
            show_progress=True
        )

        print(f"✅ Migration complete! Added {len(ids)} documents to Pinecone")
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def verify_migration(
    faiss_manager: VectorStoreManager,
    pinecone_manager: PineconeVectorStoreManager
):
    """
    Verify that migration was successful by comparing document counts.

    Args:
        faiss_manager: FAISS manager
        pinecone_manager: Pinecone manager
    """
    print("🔍 Verifying migration...")

    try:
        # Get FAISS count
        faiss_index = faiss_manager.vector_store.index
        faiss_count = faiss_index.ntotal

        # Get Pinecone count
        pinecone_stats = pinecone_manager.get_index_stats()
        pinecone_count = pinecone_stats.get('total_vector_count', 0)

        # Check namespace count if using namespace
        if pinecone_manager.namespace:
            namespace_stats = pinecone_stats.get('namespaces', {}).get(
                pinecone_manager.namespace, {}
            )
            namespace_count = namespace_stats.get('vector_count', 0)
            print(f"   FAISS vectors: {faiss_count}")
            print(f"   Pinecone vectors (namespace '{pinecone_manager.namespace}'): {namespace_count}")

            if namespace_count >= faiss_count:
                print("✅ Migration verified successfully!")
                return True
            else:
                print(f"⚠️  Warning: Pinecone has fewer vectors ({namespace_count}) than FAISS ({faiss_count})")
                return False
        else:
            print(f"   FAISS vectors: {faiss_count}")
            print(f"   Pinecone vectors (total): {pinecone_count}")

            if pinecone_count >= faiss_count:
                print("✅ Migration verified successfully!")
                return True
            else:
                print(f"⚠️  Warning: Pinecone has fewer vectors ({pinecone_count}) than FAISS ({faiss_count})")
                return False

    except Exception as e:
        print(f"⚠️  Could not verify migration: {e}")
        return False


def test_search_comparison(
    faiss_manager: VectorStoreManager,
    pinecone_manager: PineconeVectorStoreManager
):
    """
    Test search on both FAISS and Pinecone to compare results.

    Args:
        faiss_manager: FAISS manager
        pinecone_manager: Pinecone manager
    """
    print("\n🔍 Testing search comparison...")

    test_query = "What is machine learning?"

    try:
        # Search FAISS
        print(f"\n   Query: '{test_query}'")
        print("\n   FAISS Results:")
        faiss_results = faiss_manager.similarity_search(test_query, k=3)
        for i, doc in enumerate(faiss_results, 1):
            preview = doc.page_content[:100].replace('\n', ' ')
            print(f"   {i}. {preview}...")

        # Search Pinecone
        print("\n   Pinecone Results:")
        pinecone_results = pinecone_manager.similarity_search(test_query, k=3)
        for i, doc in enumerate(pinecone_results, 1):
            preview = doc.page_content[:100].replace('\n', ' ')
            print(f"   {i}. {preview}...")

        print("\n✅ Search test complete")

    except Exception as e:
        print(f"⚠️  Search test failed: {e}")


def main():
    """Main migration workflow."""
    print_header("FAISS to Pinecone Migration Tool")

    # Step 1: Validate configuration
    if not validate_configuration():
        print("\n❌ Configuration validation failed")
        sys.exit(1)

    # Step 2: Initialize managers
    print("\n📦 Initializing managers...")

    try:
        embedding_manager = EmbeddingManager()
        faiss_manager = VectorStoreManager(embedding_manager)
        pinecone_manager = PineconeVectorStoreManager(embedding_manager)

        print("✅ Managers initialized")

    except Exception as e:
        print(f"❌ Failed to initialize managers: {e}")
        sys.exit(1)

    # Step 3: Load FAISS documents
    print_header("Step 1: Load FAISS Documents")
    documents = load_faiss_documents(faiss_manager)

    if not documents:
        print("\n❌ No documents to migrate")
        sys.exit(1)

    # Step 4: Migrate to Pinecone
    print_header("Step 2: Migrate to Pinecone")

    # Confirm migration
    print(f"⚠️  You are about to migrate {len(documents)} documents to Pinecone")
    print(f"   Index: {Config.PINECONE_INDEX_NAME}")
    print(f"   Namespace: {Config.PINECONE_NAMESPACE or 'default'}")
    print(f"   Region: {Config.PINECONE_REGION}")

    response = input("\nProceed with migration? (y/n): ")
    if response.lower() != 'y':
        print("\n❌ Migration cancelled")
        sys.exit(0)

    success = migrate_to_pinecone(documents, pinecone_manager)

    if not success:
        print("\n❌ Migration failed")
        sys.exit(1)

    # Step 5: Verify migration
    print_header("Step 3: Verify Migration")
    verify_migration(faiss_manager, pinecone_manager)

    # Step 6: Test search
    print_header("Step 4: Test Search")
    test_search_comparison(faiss_manager, pinecone_manager)

    # Step 7: Next steps
    print_header("Migration Complete!")
    print("✅ Your documents have been migrated to Pinecone")
    print("\n📝 Next Steps:")
    print("   1. Update .env: Set USE_PINECONE=true")
    print("   2. Restart your application")
    print("   3. Test document search functionality")
    print("   4. (Optional) Delete local FAISS data to save space:")
    print(f"      rm -rf {Config.VECTOR_STORE_PATH}")
    print("\n💡 Tip: Keep FAISS data as backup until you verify Pinecone works")


if __name__ == "__main__":
    main()
