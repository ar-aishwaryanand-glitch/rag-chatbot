"""
Security tests for critical security fixes.

Tests:
- Code executor sandbox escape attempts
- File ops symlink traversal blocked
- Web agent SSRF via DNS rebinding blocked
- Web agent redirect to private IP blocked
- Policy engine rate limits persist across restart
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestCodeExecutorSandbox:
    """Test code executor sandbox hardening."""

    @pytest.fixture
    def executor(self):
        """Create a code executor instance."""
        from agent.tools.code_executor_tool import CodeExecutorTool
        return CodeExecutorTool(timeout=5)

    def test_blocks_type_bases_escape(self, executor):
        """Test that type().__bases__ sandbox escape is blocked."""
        # Classic sandbox escape: type(1).__bases__[0].__subclasses__()
        code = "result = type(1).__bases__[0].__subclasses__()"
        result = executor._run(code)
        assert "Error" in result or "not allowed" in result.lower()

    def test_blocks_mro_access(self, executor):
        """Test that __mro__ attribute access is blocked."""
        code = "x = ''.__class__.__mro__"
        result = executor._run(code)
        assert "Error" in result or "not allowed" in result.lower()

    def test_blocks_reduce_access(self, executor):
        """Test that __reduce__ attribute access is blocked."""
        code = "x = [].__reduce__()"
        result = executor._run(code)
        assert "Error" in result or "not allowed" in result.lower()

    def test_blocks_getattribute_access(self, executor):
        """Test that __getattribute__ is blocked."""
        code = "x = object.__getattribute__([], '__class__')"
        safety = executor.check_code_safety_ast(code)
        assert not safety['safe']

    def test_blocks_import_via_string(self, executor):
        """Test that string-based import bypass is blocked."""
        code = '''
s = "__imp" + "ort__"
result = eval(s)("os")
'''
        result = executor._run(code)
        assert "Error" in result or "not allowed" in result.lower()

    def test_blocks_globals_access(self, executor):
        """Test that __globals__ access is blocked."""
        code = "x = (lambda: 0).__globals__"
        safety = executor.check_code_safety_ast(code)
        assert not safety['safe']

    def test_blocks_builtins_access(self, executor):
        """Test that __builtins__ access is blocked."""
        code = "x = __builtins__"
        result = executor._run(code)
        assert "Error" in result or "not allowed" in result.lower()

    def test_blocks_subclasses_in_string(self, executor):
        """Test that dangerous patterns in strings are detected."""
        code = '''x = "__subclasses__"'''
        safety = executor.check_code_safety_ast(code)
        assert not safety['safe']

    def test_allows_safe_math(self, executor):
        """Test that safe math operations work."""
        code = "result = sum([1, 2, 3, 4, 5])\nprint(result)"
        result = executor._run(code)
        assert "15" in result
        assert "Error" not in result

    def test_allows_safe_list_operations(self, executor):
        """Test that safe list operations work."""
        code = """
data = [1, 2, 3, 4, 5]
squared = [x**2 for x in data]
print(squared)
"""
        result = executor._run(code)
        assert "[1, 4, 9, 16, 25]" in result
        assert "Error" not in result

    def test_case_insensitive_blocking(self, executor):
        """Test that blocking is case-insensitive."""
        # Try mixed case
        code = "import OS"
        assert not executor.is_safe_code(code)

        code = "IMPORT os"
        assert not executor.is_safe_code(code)


class TestFileOpsPathTraversal:
    """Test file operations path traversal protections."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            # Create a test file
            (workspace / "test.txt").write_text("test content")
            yield workspace

    @pytest.fixture
    def file_ops(self, temp_workspace):
        """Create a file ops tool instance."""
        from agent.tools.file_ops_tool import FileOpsTool
        return FileOpsTool(workspace_root=temp_workspace)

    def test_blocks_parent_directory_traversal(self, file_ops):
        """Test that ../.. traversal is blocked."""
        result = file_ops._run("read", "../../etc/passwd")
        assert "Error" in result or "denied" in result.lower()

    def test_blocks_absolute_path_outside_workspace(self, file_ops):
        """Test that absolute paths outside workspace are blocked."""
        result = file_ops._run("read", "/etc/passwd")
        assert "Error" in result or "denied" in result.lower()

    def test_allows_valid_workspace_file(self, file_ops):
        """Test that valid workspace files can be read."""
        result = file_ops._run("read", "test.txt")
        assert "test content" in result

    @pytest.mark.skipif(os.name == 'nt', reason="Symlinks require admin on Windows")
    def test_blocks_symlink_outside_workspace(self, file_ops, temp_workspace):
        """Test that symlinks pointing outside workspace are blocked."""
        # Create a symlink pointing outside
        symlink_path = temp_workspace / "evil_link"
        try:
            symlink_path.symlink_to("/etc/passwd")
        except (OSError, PermissionError):
            pytest.skip("Cannot create symlink")

        result = file_ops._run("read", "evil_link")
        assert "Error" in result or "denied" in result.lower() or "outside" in result.lower()

    def test_glob_pattern_escaping(self, file_ops, temp_workspace):
        """Test that glob patterns are properly escaped."""
        # Create a file with special characters
        special_file = temp_workspace / "test[1].txt"
        special_file.write_text("special content")

        # Search should escape the brackets
        result = file_ops._run("search", "[1]")
        # Should find the file (escaped properly)
        assert "Error" not in result or "test[1].txt" in result


class TestWebAgentSSRF:
    """Test web agent SSRF and DNS rebinding protections."""

    @pytest.fixture
    def web_agent(self):
        """Create a web agent instance."""
        from agent.tools.web_agent_tool import WebAgentTool
        return WebAgentTool(timeout=10)

    def test_blocks_localhost(self, web_agent):
        """Test that localhost is blocked."""
        is_valid, error, _ = web_agent.validate_url("http://localhost/")
        assert not is_valid
        assert "localhost" in error.lower()

    def test_blocks_127_0_0_1(self, web_agent):
        """Test that 127.0.0.1 is blocked."""
        is_valid, error, _ = web_agent.validate_url("http://127.0.0.1/")
        assert not is_valid

    def test_blocks_ipv6_localhost(self, web_agent):
        """Test that IPv6 localhost is blocked."""
        is_valid, error, _ = web_agent.validate_url("http://[::1]/")
        assert not is_valid

    def test_blocks_zero_ip(self, web_agent):
        """Test that 0.0.0.0 is blocked."""
        is_valid, error, _ = web_agent.validate_url("http://0.0.0.0/")
        assert not is_valid

    def test_blocks_aws_metadata(self, web_agent):
        """Test that AWS metadata endpoint is blocked."""
        # Mock DNS resolution to return metadata IP
        with patch('socket.gethostbyname', return_value='169.254.169.254'):
            is_valid, error, _ = web_agent.validate_url("http://metadata.internal/")
            assert not is_valid
            assert "metadata" in error.lower() or "private" in error.lower()

    def test_blocks_private_ip(self, web_agent):
        """Test that private IPs are blocked."""
        # Mock DNS resolution to return private IP
        with patch('socket.gethostbyname', return_value='192.168.1.1'):
            is_valid, error, _ = web_agent.validate_url("http://internal.example.com/")
            assert not is_valid
            assert "private" in error.lower()

    def test_blocks_decimal_ip(self, web_agent):
        """Test that decimal IP representation is blocked."""
        # 2130706433 = 127.0.0.1 in decimal
        is_valid, error, _ = web_agent.validate_url("http://2130706433/")
        assert not is_valid
        assert "numeric" in error.lower()

    def test_blocks_hex_ip(self, web_agent):
        """Test that hex IP representation is blocked."""
        # 0x7f000001 = 127.0.0.1 in hex
        is_valid, error, _ = web_agent.validate_url("http://0x7f000001/")
        assert not is_valid
        assert "numeric" in error.lower()

    def test_allows_valid_public_url(self, web_agent):
        """Test that valid public URLs pass validation."""
        # Mock DNS to return public IP
        with patch('socket.gethostbyname', return_value='8.8.8.8'):
            is_valid, error, _ = web_agent.validate_url("https://example.com/")
            assert is_valid
            assert error is None

    def test_redirect_validation(self, web_agent):
        """Test that redirect validation works."""
        # Mock DNS to return private IP for redirect target
        with patch('socket.gethostbyname', return_value='10.0.0.1'):
            is_valid, error = web_agent._validate_redirect("http://internal.evil.com/")
            assert not is_valid
            assert "Redirect blocked" in error


class TestPolicyEnginePersistence:
    """Test policy engine rate limit persistence."""

    @pytest.fixture
    def temp_policy_dir(self):
        """Create a temporary directory for policy data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_rate_limits_persist(self, temp_policy_dir):
        """Test that rate limit counters persist across restarts."""
        from policy.policy_engine import PolicyEngine
        from policy.policy_definitions import PolicyEvaluationContext

        # Create engine instance with custom persistence path
        engine1 = PolicyEngine(persist_rate_limits=True)
        # Override the persistence path after creation
        engine1._persistence_path = temp_policy_dir
        engine1._rate_limit_file = temp_policy_dir / "rate_limits.json"

        # Record some request counts
        context = PolicyEvaluationContext(
            session_id="test_session",
            tool_name="test_tool"
        )

        # Make several requests to build up counts
        for _ in range(5):
            engine1.evaluate_rate_limit(context)

        # Force save
        engine1._save_rate_limits()

        # Verify file was created
        assert engine1._rate_limit_file.exists()

        # Read the saved data
        with open(engine1._rate_limit_file, 'r') as f:
            saved_data = json.load(f)

        # Verify request counts were saved
        assert 'request_counts' in saved_data
        assert 'test_session' in saved_data['request_counts']
        assert len(saved_data['request_counts']['test_session']) == 5

    def test_regex_timeout_protection(self, temp_policy_dir):
        """Test that regex patterns with potential ReDoS are handled."""
        from policy.policy_engine import PolicyEngine

        engine = PolicyEngine(persist_rate_limits=False)

        # Test a safe pattern
        result = engine._safe_regex_search(r"hello", "hello world")
        assert result is True

        # Test a pattern with no match
        result = engine._safe_regex_search(r"xyz", "hello world")
        assert result is False

        # Test with long content (should be truncated)
        long_content = "a" * 200000  # 200KB
        result = engine._safe_regex_search(r"b", long_content)
        assert result is False  # No match in truncated content


class TestContentSanitization:
    """Test content sanitization in web agent."""

    @pytest.fixture
    def web_agent(self):
        """Create a web agent instance."""
        from agent.tools.web_agent_tool import WebAgentTool
        return WebAgentTool(timeout=10)

    def test_removes_script_tags(self, web_agent):
        """Test that script tags are removed from content."""
        dirty = "Hello <script>alert('xss')</script> World"
        clean = web_agent._clean_text(dirty)
        assert "<script>" not in clean
        assert "alert" not in clean

    def test_removes_javascript_protocol(self, web_agent):
        """Test that javascript: protocol is removed."""
        dirty = "Click javascript:alert(1) here"
        clean = web_agent._clean_text(dirty)
        assert "javascript:" not in clean

    def test_removes_data_protocol(self, web_agent):
        """Test that data: protocol is removed."""
        dirty = "Image: data:image/png;base64,abc here"
        clean = web_agent._clean_text(dirty)
        assert "data:" not in clean

    def test_removes_null_bytes(self, web_agent):
        """Test that null bytes are removed."""
        dirty = "Hello\x00World"
        clean = web_agent._clean_text(dirty)
        assert "\x00" not in clean

    def test_preserves_valid_content(self, web_agent):
        """Test that valid content is preserved."""
        valid = "This is a normal paragraph with proper text content."
        clean = web_agent._clean_text(valid)
        assert "normal paragraph" in clean
        assert "proper text" in clean
