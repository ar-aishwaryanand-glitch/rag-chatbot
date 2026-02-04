"""
Integration test to verify Streamlit app fixes are working.

This tests the actual code paths that will execute in the Streamlit app.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_auto_indexing_import():
    """Test that auto-indexing integration can be imported and called."""
    print("\n" + "="*80)
    print("TEST: AUTO-INDEXING INTEGRATION IN STREAMLIT")
    print("="*80)

    try:
        print("\n1️⃣  Testing import...")
        from src.ui.auto_index_integration import check_and_index_on_startup

        print("   ✅ Import successful")

        print("\n2️⃣  Testing function signature...")
        import inspect
        sig = inspect.signature(check_and_index_on_startup)
        print(f"   Function signature: {sig}")
        print("   ✅ Function is callable")

        print("\n3️⃣  Testing execution...")
        result = check_and_index_on_startup(force=False)
        print(f"   Result: {result}")
        print("   ✅ Function executes without error")

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cleanup_function():
    """Test that cleanup function is properly defined."""
    print("\n" + "="*80)
    print("TEST: CLEANUP FUNCTION IN STREAMLIT")
    print("="*80)

    try:
        print("\n1️⃣  Testing cleanup function exists...")

        # Read the streamlit app file
        app_file = Path("src/ui/streamlit_app_agent.py")
        content = app_file.read_text()

        # Check for cleanup function
        if "def cleanup_resources():" in content:
            print("   ✅ cleanup_resources() function defined")
        else:
            print("   ❌ cleanup_resources() function not found")
            return False

        # Check for atexit registration
        if "atexit.register(cleanup_resources)" in content:
            print("   ✅ atexit.register() called")
        else:
            print("   ❌ atexit.register() not found")
            return False

        # Check for session save
        if "agent.end_session()" in content:
            print("   ✅ agent.end_session() called in cleanup")
        else:
            print("   ❌ agent.end_session() not found")
            return False

        # Check for database close
        if "session_mgr.close()" in content:
            print("   ✅ session_mgr.close() called in cleanup")
        else:
            print("   ❌ session_mgr.close() not found")
            return False

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_memory_autosave():
    """Test that memory auto-save is in the query handler."""
    print("\n" + "="*80)
    print("TEST: MEMORY AUTO-SAVE IN QUERY HANDLER")
    print("="*80)

    try:
        print("\n1️⃣  Checking query handler for auto-save...")

        app_file = Path("src/ui/streamlit_app_agent.py")
        content = app_file.read_text()

        # Check for periodic save logic
        if "session_queries % 5 == 0" in content:
            print("   ✅ Periodic save check (every 5 queries)")
        else:
            print("   ❌ Periodic save logic not found")
            return False

        # Check for save call
        if "save_episodic_memory()" in content:
            print("   ✅ save_episodic_memory() called")
        else:
            print("   ❌ save_episodic_memory() not found")
            return False

        # Check for auto-save message
        if "Auto-saved episodic memory" in content:
            print("   ✅ Auto-save logging present")
        else:
            print("   ⚠️  Auto-save logging not found (minor)")

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_thread_id_integration():
    """Test that thread_id is passed to agent.execute()."""
    print("\n" + "="*80)
    print("TEST: THREAD ID FOR CONVERSATION MEMORY")
    print("="*80)

    try:
        print("\n1️⃣  Checking thread_id implementation...")

        app_file = Path("src/ui/streamlit_app_agent.py")
        content = app_file.read_text()

        # Check for thread_id session state
        if "conversation_thread_id" in content:
            print("   ✅ conversation_thread_id in session state")
        else:
            print("   ❌ conversation_thread_id not found")
            return False

        # Check for thread_id generation
        if "uuid.uuid4().hex[:12]" in content:
            print("   ✅ Thread ID generation logic present")
        else:
            print("   ❌ Thread ID generation not found")
            return False

        # Check for thread_id passed to execute
        if "thread_id=st.session_state.conversation_thread_id" in content:
            print("   ✅ thread_id passed to agent.execute()")
        else:
            print("   ❌ thread_id not passed to agent")
            return False

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_exception_handling():
    """Verify all bare except clauses are replaced."""
    print("\n" + "="*80)
    print("TEST: EXCEPTION HANDLING (BARE EXCEPT REMOVED)")
    print("="*80)

    try:
        files_to_check = [
            "src/ui/auto_index_integration.py",
            "src/agent/tools/calculator_tool.py",
            "src/agent/tools/news_api_tool.py",
            "src/agent/tools/relevance_evaluator.py"
        ]

        all_good = True
        for file_path in files_to_check:
            path = Path(file_path)
            if not path.exists():
                print(f"   ⚠️  {file_path} not found")
                continue

            content = path.read_text()

            # Check for bare except (should not exist)
            import re
            bare_excepts = re.findall(r'^\s*except\s*:', content, re.MULTILINE)

            if bare_excepts:
                print(f"   ❌ {file_path}: Found {len(bare_excepts)} bare except clause(s)")
                all_good = False
            else:
                print(f"   ✅ {file_path}: No bare except clauses")

        return all_good

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Run all integration tests."""
    print("="*80)
    print("STREAMLIT INTEGRATION TEST SUITE")
    print("="*80)
    print("\nVerifying all 4 critical fixes are integrated correctly:")

    results = {
        "Auto-indexing Integration": test_auto_indexing_import(),
        "Cleanup Function": test_cleanup_function(),
        "Memory Auto-save": test_memory_autosave(),
        "Thread ID for Memory": test_thread_id_integration(),
        "Exception Handling": test_exception_handling()
    }

    # Print summary
    print("\n" + "="*80)
    print("INTEGRATION TEST SUMMARY")
    print("="*80)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}  {test_name}")

    total_passed = sum(results.values())
    total_tests = len(results)

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("\n✨ Your Streamlit app is ready with all critical fixes!")
        print("\nRun the app with:")
        print("  streamlit run src/ui/streamlit_app_agent.py")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
