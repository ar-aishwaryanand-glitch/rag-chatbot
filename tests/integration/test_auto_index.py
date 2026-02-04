#!/usr/bin/env python3
"""
Test script for automated document indexing.

Run this to see auto-indexing in action without modifying your Streamlit app.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.auto_indexer import get_auto_indexer


def main():
    print("=" * 70)
    print("AUTOMATED DOCUMENT INDEXING - TEST SCRIPT")
    print("=" * 70)

    # Get auto-indexer instance
    auto_indexer = get_auto_indexer()

    # Show current status
    print("\n📊 Current Status:")
    print("-" * 70)
    status = auto_indexer.get_status()

    print(f"Documents directory: {status['documents_dir']}")
    print(f"Total indexed: {status['total_indexed']} documents")
    print(f"Last indexed: {status.get('last_index', 'Never')}")

    # Show pending changes
    print("\n📝 Pending Changes:")
    pending = status['pending_changes']
    print(f"  - New files: {pending['new']}")
    print(f"  - Modified files: {pending['modified']}")
    print(f"  - Deleted files: {pending['deleted']}")

    # Check if indexing is needed
    if status['needs_indexing']:
        print("\n⚠️  Indexing required!")

        response = input("\nWould you like to index now? (y/n): ")

        if response.lower() == 'y':
            print("\n" + "=" * 70)
            print("STARTING AUTO-INDEXING")
            print("=" * 70)

            result = auto_indexer.index_documents(force_rebuild=False, verbose=True)

            print("\n" + "=" * 70)
            print("INDEXING RESULTS")
            print("=" * 70)
            print(f"Status: {result['status']}")
            print(f"New documents: {result.get('new', 0)}")
            print(f"Modified documents: {result.get('modified', 0)}")
            print(f"Deleted documents: {result.get('deleted', 0)}")
            print(f"Total files: {result.get('total_files', 0)}")

            if result['status'] == 'success':
                print("\n✅ Auto-indexing completed successfully!")
            else:
                print(f"\n❌ Auto-indexing failed: {result.get('message', 'Unknown error')}")
        else:
            print("\n⏭️  Skipping indexing")
    else:
        print("\n✅ All documents are up to date! No indexing needed.")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
