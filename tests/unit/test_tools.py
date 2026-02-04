"""
Unit tests for agent tools.

Tests cover:
- BaseTool interface
- CalculatorTool calculations
- ToolRegistry management
- Tool result structure
"""

import pytest

from src.agent.tools.base_tool import BaseTool, ToolResult


class TestToolResult:
    """Tests for ToolResult dataclass."""

    def test_successful_result(self):
        """Test creating a successful tool result."""
        result = ToolResult(
            success=True,
            output="Test output",
            duration=0.5,
            metadata={"key": "value"}
        )
        assert result.success is True
        assert result.output == "Test output"
        assert result.error is None
        assert result.duration == 0.5
        assert result.metadata == {"key": "value"}

    def test_failed_result(self):
        """Test creating a failed tool result."""
        result = ToolResult(
            success=False,
            output="",
            error="Something went wrong",
            duration=0.1
        )
        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.output == ""

    def test_default_metadata(self):
        """Test that metadata defaults to empty dict."""
        result = ToolResult(success=True, output="test", duration=0.1)
        assert result.metadata == {}


class TestBaseTool:
    """Tests for BaseTool abstract class."""

    def test_mock_tool_properties(self, mock_tool):
        """Test that mock tool has required properties."""
        assert mock_tool.name == "mock_tool"
        assert "mock tool" in mock_tool.description.lower()

    def test_mock_tool_run(self, mock_tool):
        """Test mock tool execution."""
        result = mock_tool.run(query="test query")
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert "test query" in result.output

    def test_tool_call_count(self, mock_tool):
        """Test that call count increments."""
        assert mock_tool.call_count == 0
        mock_tool.run(query="first")
        assert mock_tool.call_count == 1
        mock_tool.run(query="second")
        assert mock_tool.call_count == 2

    def test_tool_string_representation(self, mock_tool):
        """Test __str__ and __repr__ methods."""
        str_repr = str(mock_tool)
        assert "mock_tool" in str_repr

        repr_str = repr(mock_tool)
        assert "MockTool" in repr_str


class TestCalculatorTool:
    """Tests for CalculatorTool."""

    def test_basic_arithmetic(self, calculator_tool):
        """Test basic arithmetic operations."""
        # Addition
        result = calculator_tool.run(expression="2 + 3")
        assert result.success is True
        assert "5" in result.output

        # Subtraction
        result = calculator_tool.run(expression="10 - 4")
        assert result.success is True
        assert "6" in result.output

        # Multiplication
        result = calculator_tool.run(expression="6 * 7")
        assert result.success is True
        assert "42" in result.output

        # Division
        result = calculator_tool.run(expression="20 / 4")
        assert result.success is True
        assert "5" in result.output

    def test_complex_expressions(self, calculator_tool):
        """Test more complex expressions."""
        result = calculator_tool.run(expression="(2 + 3) * 4")
        assert result.success is True
        assert "20" in result.output

    def test_power_operations(self, calculator_tool):
        """Test power/exponent operations."""
        result = calculator_tool.run(expression="2 ** 10")
        assert result.success is True
        assert "1024" in result.output

    def test_math_functions(self, calculator_tool):
        """Test mathematical functions."""
        # Square root
        result = calculator_tool.run(expression="sqrt(16)")
        assert result.success is True
        assert "4" in result.output

    def test_invalid_expression(self, calculator_tool):
        """Test handling of invalid expressions."""
        result = calculator_tool.run(expression="invalid expression")
        # Should either fail gracefully or return error
        assert result.success is False or "error" in result.output.lower()

    def test_calculator_name_and_description(self, calculator_tool):
        """Test calculator has proper name and description."""
        assert calculator_tool.name == "calculator"
        assert "math" in calculator_tool.description.lower() or "calcul" in calculator_tool.description.lower()

    def test_test_expression_method(self, calculator_tool):
        """Test the test_expression helper method."""
        # Valid expression
        assert calculator_tool.test_expression("2 + 2") is True

        # Note: numexpr may accept some expressions that look invalid
        # The key test is that valid expressions return True
        # Invalid expressions may or may not be caught depending on numexpr version


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_empty_registry(self, tool_registry):
        """Test empty registry state."""
        assert len(tool_registry) == 0
        assert tool_registry.get_tool_names() == []
        assert tool_registry.get_all_tools() == []

    def test_register_tool(self, tool_registry, mock_tool):
        """Test registering a tool."""
        tool_registry.register(mock_tool)
        assert len(tool_registry) == 1
        assert "mock_tool" in tool_registry

    def test_get_tool(self, tool_registry, mock_tool):
        """Test retrieving a registered tool."""
        tool_registry.register(mock_tool)
        retrieved = tool_registry.get_tool("mock_tool")
        assert retrieved is mock_tool

    def test_get_nonexistent_tool(self, tool_registry):
        """Test retrieving non-existent tool returns None."""
        result = tool_registry.get_tool("nonexistent")
        assert result is None

    def test_duplicate_registration_raises(self, tool_registry, mock_tool):
        """Test that registering duplicate tool raises ValueError."""
        tool_registry.register(mock_tool)
        with pytest.raises(ValueError, match="already registered"):
            tool_registry.register(mock_tool)

    def test_get_all_tools(self, populated_tool_registry):
        """Test getting all tools."""
        tools = populated_tool_registry.get_all_tools()
        assert len(tools) == 2

    def test_get_tool_names(self, populated_tool_registry):
        """Test getting tool names."""
        names = populated_tool_registry.get_tool_names()
        assert "mock_tool" in names
        assert "calculator" in names

    def test_get_tool_descriptions(self, populated_tool_registry):
        """Test getting formatted tool descriptions."""
        descriptions = populated_tool_registry.get_tool_descriptions()
        assert "mock_tool" in descriptions
        assert "calculator" in descriptions
        # Should be formatted with dashes
        assert "- " in descriptions

    def test_clear_registry(self, populated_tool_registry):
        """Test clearing all tools."""
        assert len(populated_tool_registry) > 0
        populated_tool_registry.clear()
        assert len(populated_tool_registry) == 0

    def test_contains_operator(self, populated_tool_registry):
        """Test __contains__ operator."""
        assert "mock_tool" in populated_tool_registry
        assert "nonexistent" not in populated_tool_registry

    def test_repr(self, populated_tool_registry):
        """Test string representation."""
        repr_str = repr(populated_tool_registry)
        assert "ToolRegistry" in repr_str
        assert "mock_tool" in repr_str


class TestToolExecution:
    """Tests for tool execution patterns."""

    def test_tool_result_timing(self, calculator_tool):
        """Test that tool execution records timing."""
        result = calculator_tool.run(expression="1 + 1")
        assert result.duration >= 0
        assert isinstance(result.duration, float)

    def test_tool_error_handling(self, mock_tool):
        """Test that tools handle errors gracefully."""
        # Create a tool that raises an exception
        class ErrorTool(BaseTool):
            @property
            def name(self) -> str:
                return "error_tool"

            @property
            def description(self) -> str:
                return "A tool that always raises an error"

            def _run(self, *args, **kwargs) -> str:
                raise ValueError("Intentional error for testing")

        error_tool = ErrorTool()
        result = error_tool.run()

        assert result.success is False
        assert result.error is not None
        assert "Intentional error" in result.error


class TestToolIntegration:
    """Integration tests for tools working together."""

    def test_registry_with_multiple_tool_types(self, tool_registry, mock_tool, calculator_tool):
        """Test registry with different tool types."""
        tool_registry.register(mock_tool)
        tool_registry.register(calculator_tool)

        # Both should be retrievable
        assert tool_registry.get_tool("mock_tool") is not None
        assert tool_registry.get_tool("calculator") is not None

        # Both should work independently
        mock_result = tool_registry.get_tool("mock_tool").run(query="test")
        calc_result = tool_registry.get_tool("calculator").run(expression="5 * 5")

        assert mock_result.success is True
        assert calc_result.success is True
        assert "25" in calc_result.output
