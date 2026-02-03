"""Test script for URL handler functionality."""

from src.ui.url_handler import (
    validate_url,
    sanitize_url_for_filename,
    fetch_url_content
)


def test_validate_url():
    """Test URL validation."""
    print("\n🧪 Testing URL Validation...")

    test_cases = [
        ("https://example.com", True),
        ("http://example.com/article", True),
        ("https://example.com/path/to/page", True),
        ("not-a-url", False),
        ("", False),
        ("ftp://example.com", False),
    ]

    passed = 0
    for url, expected_valid in test_cases:
        is_valid, _ = validate_url(url)
        status = "✅" if is_valid == expected_valid else "❌"
        print(f"  {status} {url[:50]:50} -> {'Valid' if is_valid else 'Invalid'}")
        if is_valid == expected_valid:
            passed += 1

    print(f"\n📊 URL Validation: {passed}/{len(test_cases)} passed\n")
    return passed == len(test_cases)


def test_sanitize_filename():
    """Test filename sanitization."""
    print("🧪 Testing Filename Sanitization...")

    test_cases = [
        "https://example.com",
        "https://example.com/article/title",
        "https://www.github.com/user/repo",
        "https://news.site.com/2024/01/article?param=value",
    ]

    for url in test_cases:
        filename = sanitize_url_for_filename(url)
        print(f"  ✅ {url[:50]:50} -> {filename}")

    print()
    return True


def test_fetch_content():
    """Test fetching content from a URL."""
    print("🧪 Testing URL Content Fetching...")

    # Test with a simple, reliable URL
    test_url = "https://example.com"

    print(f"  Fetching: {test_url}")
    print("  (This may take a few seconds...)")

    success, content, error = fetch_url_content(test_url)

    if success:
        print(f"  ✅ Successfully fetched content ({len(content)} characters)")
        print(f"  Preview: {content[:100]}...")
        return True
    else:
        print(f"  ❌ Failed: {error}")
        if "playwright" in error.lower():
            print("  💡 Tip: Install Playwright with: pip install playwright && playwright install chromium")
        return False


def main():
    """Run all tests."""
    print("=" * 80)
    print("🧪 URL Handler Test Suite")
    print("=" * 80)

    results = []

    # Test 1: URL Validation
    results.append(("URL Validation", test_validate_url()))

    # Test 2: Filename Sanitization
    results.append(("Filename Sanitization", test_sanitize_filename()))

    # Test 3: Content Fetching (may fail if Playwright not installed)
    try:
        results.append(("Content Fetching", test_fetch_content()))
    except Exception as e:
        print(f"  ❌ Content fetching test failed: {e}")
        results.append(("Content Fetching", False))

    # Summary
    print("\n" + "=" * 80)
    print("📊 Test Summary")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.0f}%)\n")

    if passed == total:
        print("🎉 All tests passed!")
    elif passed > 0:
        print("⚠️  Some tests passed. Check failures above.")
    else:
        print("❌ All tests failed. Please check your setup.")

    print("=" * 80)


if __name__ == "__main__":
    main()
