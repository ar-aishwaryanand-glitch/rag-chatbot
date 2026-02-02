#!/usr/bin/env python3
"""
Test script for Web Agent Tool.

Tests:
- Single URL extraction
- Multiple URL synthesis
- Error handling
- Content cleaning
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.agent.tools.web_agent_tool import WebAgentTool


def print_separator(char='=', length=80):
    print(char * length)


def print_header(text):
    print()
    print_separator()
    print(f"  {text}")
    print_separator()


def test_single_url():
    """Test extracting content from a single URL."""
    print_header("TEST 1: Single URL Extraction")

    tool = WebAgentTool(timeout=30)

    # Test URL (using a reliable, simple site)
    test_url = "https://example.com"

    print(f"\n🌐 Testing URL: {test_url}")
    print("⏳ Fetching and extracting content...")

    result = tool.run(url=test_url)

    if result.success:
        print("\n✅ SUCCESS!")
        print(f"\nExtracted Content ({len(result.output)} characters):")
        print("-" * 80)
        print(result.output[:500])  # Show first 500 chars
        if len(result.output) > 500:
            print("...")
        print("-" * 80)
    else:
        print(f"\n❌ FAILED: {result.error}")

    return result.success


def test_multiple_urls():
    """Test extracting and synthesizing from multiple URLs."""
    print_header("TEST 2: Multiple URL Synthesis")

    tool = WebAgentTool(timeout=30, max_pages=3)

    # Test URLs
    test_urls = [
        "https://example.com",
        "https://www.iana.org/domains/reserved",
    ]

    print(f"\n🌐 Testing {len(test_urls)} URLs:")
    for url in test_urls:
        print(f"   • {url}")

    print("\n⏳ Fetching and synthesizing content...")

    result = tool.run(urls=test_urls)

    if result.success:
        print("\n✅ SUCCESS!")
        print(f"\nSynthesized Content ({len(result.output)} characters):")
        print("-" * 80)
        print(result.output[:800])  # Show first 800 chars
        if len(result.output) > 800:
            print("...")
        print("-" * 80)
    else:
        print(f"\n❌ FAILED: {result.error}")

    return result.success


def test_error_handling():
    """Test error handling with invalid URLs."""
    print_header("TEST 3: Error Handling")

    tool = WebAgentTool(timeout=5)

    # Test with invalid URL
    invalid_url = "https://this-domain-definitely-does-not-exist-12345.com"

    print(f"\n🌐 Testing invalid URL: {invalid_url}")
    print("⏳ Attempting to fetch...")

    result = tool.run(url=invalid_url)

    if not result.success:
        print("\n✅ Correctly handled error!")
        print(f"Error message: {result.error}")
    else:
        print("\n⚠️  Expected failure but got success (unexpected)")

    return not result.success  # Success means it correctly handled the error


def test_tool_availability():
    """Test tool dependency checking."""
    print_header("TEST 4: Dependency Check")

    tool = WebAgentTool()

    print(f"\n🔍 Checking dependencies...")
    print(f"   Playwright available: {tool.available}")

    if not tool.available:
        print(f"   ⚠️  Error: {tool.error_msg}")
        print("\n📦 To install dependencies:")
        print("   pip install playwright beautifulsoup4 readability-lxml")
        print("   playwright install chromium")
        return False
    else:
        print("   ✅ All dependencies available")
        return True


def run_all_tests():
    """Run all web agent tests."""
    print_separator('=')
    print("  WEB AGENT TOOL TEST SUITE")
    print_separator('=')

    print("""
This test suite validates:
1. ✓ Single URL extraction
2. ✓ Multiple URL synthesis
3. ✓ Error handling
4. ✓ Dependency checking
    """)

    # Check dependencies first
    print_header("DEPENDENCY CHECK")
    deps_ok = test_tool_availability()

    if not deps_ok:
        print("\n❌ Dependencies not available. Please install:")
        print("   pip install playwright beautifulsoup4 readability-lxml lxml")
        print("   playwright install chromium")
        return False

    # Run tests
    test_results = {
        "Single URL": False,
        "Multiple URLs": False,
        "Error Handling": False,
    }

    try:
        test_results["Single URL"] = test_single_url()
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

    try:
        test_results["Multiple URLs"] = test_multiple_urls()
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

    try:
        test_results["Error Handling"] = test_error_handling()
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

    # Summary
    print_header("TEST RESULTS SUMMARY")

    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)

    print(f"\n📊 Overall: {passed}/{total} tests passed ({passed/total*100:.0f}%)\n")

    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")

    print_separator()

    if passed == total:
        print("\n🎉 ALL WEB AGENT TESTS PASSED!")
        print("\nThe Web Agent Tool is working correctly:")
        print("  ✓ Can extract content from single URLs")
        print("  ✓ Can synthesize information from multiple sources")
        print("  ✓ Handles errors gracefully")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review details above.")

    print_separator()

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
