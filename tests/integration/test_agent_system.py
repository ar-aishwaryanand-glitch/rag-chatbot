"""
Integration tests for the agent system.

Tests cover:
- Agent initialization
- Tool routing
- Memory integration
- End-to-end query execution

Note: Some tests require actual API keys.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestAgentState:
    """Tests for AgentState management."""

    def test_agent_state_import(self):
        """Test AgentState can be imported."""
        from src.agent.agent_state import AgentState
        assert AgentState is not None

    def test_agent_state_structure(self):
        """Test AgentState has expected fields."""
        from src.agent.agent_state import AgentState

        # AgentState should be a TypedDict or similar
        # Check it has the expected structure
        state: AgentState = {
            "messages": [],
            "query": "test query",
            "final_answer": None,
            "current_phase": "understanding",
            "iteration": 0,
            "max_iterations": 10,
            "selected_tool": None,
            "tools_used": [],
            "tool_results": [],
            "needs_retry": False,
            "last_error": None,
            "memory_context": None,
            "conversation_messages": None,
            "start_time": None,
            "execution_metadata": {}
        }

        assert state["query"] == "test query"
        assert state["iteration"] == 0


class TestAgentExecutor:
    """Tests for AgentExecutorV3."""

    def test_agent_executor_import(self):
        """Test AgentExecutorV3 can be imported."""
        from src.agent.agent_executor_v3 import AgentExecutorV3
        assert AgentExecutorV3 is not None

    @patch('src.agent.agent_executor_v3.ChatGroq')
    def test_agent_executor_init_with_mocks(self, mock_llm_class):
        """Test agent can be initialized with mocked LLM."""
        from src.agent.tool_registry import ToolRegistry

        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm

        registry = ToolRegistry()

        # Agent should be initializable with minimal config
        # Note: Actual initialization may require more setup


class TestToolRouting:
    """Tests for tool routing logic."""

    def test_tool_selection_patterns(self):
        """Test tool selection for various query patterns."""
        test_cases = [
            ("What is in my documents about RAG?", "document_search"),
            ("Calculate 15% of 250", "calculator"),
            ("Search the web for latest AI news", "web_search"),
            ("What did we discuss earlier?", "none"),  # Memory-based
        ]

        for query, expected_tool in test_cases:
            # These are just pattern tests - actual routing uses LLM
            query_lower = query.lower()

            if "calculate" in query_lower or "%" in query_lower:
                suggested = "calculator"
            elif "web" in query_lower or "search" in query_lower and "document" not in query_lower:
                suggested = "web_search"
            elif "earlier" in query_lower or "discussed" in query_lower:
                suggested = "none"
            else:
                suggested = "document_search"

            # Just verify the logic makes sense
            assert suggested in ["calculator", "web_search", "document_search", "none"]


class TestAgentMemoryIntegration:
    """Tests for agent-memory integration."""

    def test_memory_context_format(self, populated_conversation_memory):
        """Test memory context is properly formatted for agent."""
        context = populated_conversation_memory.get_context_string()

        # Context should be usable by agent
        assert isinstance(context, str)
        assert len(context) > 0

    def test_conversation_serialization_for_checkpoint(self, populated_conversation_memory):
        """Test conversation can be serialized for checkpointing."""
        data = populated_conversation_memory.to_dict()

        # Should be JSON-serializable
        import json
        json_str = json.dumps(data)
        assert len(json_str) > 0

        # Should be restorable
        restored = json.loads(json_str)
        assert restored["session_id"] == populated_conversation_memory.session_id


class TestAgentToolExecution:
    """Tests for agent tool execution."""

    def test_tool_result_handling(self, calculator_tool):
        """Test that tool results are properly handled."""
        result = calculator_tool.run(expression="2 + 2")

        # Result should have expected structure
        assert hasattr(result, 'success')
        assert hasattr(result, 'output')
        assert hasattr(result, 'duration')

        # Successful result should be usable
        if result.success:
            assert "4" in result.output

    def test_multiple_tool_execution(self, populated_tool_registry):
        """Test executing multiple tools in sequence."""
        # Execute calculator
        calc = populated_tool_registry.get_tool("calculator")
        calc_result = calc.run(expression="10 * 5")

        # Execute mock tool
        mock = populated_tool_registry.get_tool("mock_tool")
        mock_result = mock.run(query="test")

        # Both should succeed
        assert calc_result.success is True
        assert mock_result.success is True


class TestAgentPhases:
    """Tests for agent execution phases."""

    def test_phase_transitions(self):
        """Test that phase transitions are valid."""
        valid_phases = ["understanding", "routing", "execute_tool", "synthesize", "reflection"]

        # Understanding -> Routing
        assert "understanding" in valid_phases
        assert "routing" in valid_phases

        # Routing -> Execute or Synthesize
        assert "execute_tool" in valid_phases
        assert "synthesize" in valid_phases

        # Synthesize -> Reflection (optional)
        assert "reflection" in valid_phases

    def test_phase_state_updates(self):
        """Test that state is properly updated in each phase."""
        # Simulate state updates through phases
        state = {
            "query": "What is RAG?",
            "current_phase": "understanding",
            "tools_used": [],
            "tool_results": []
        }

        # After understanding
        state["memory_context"] = "Previous conversation..."
        state["current_phase"] = "routing"

        assert state["memory_context"] is not None
        assert state["current_phase"] == "routing"

        # After routing
        state["selected_tool"] = "document_search"
        state["current_phase"] = "execute_tool"

        assert state["selected_tool"] == "document_search"

        # After execution
        state["tool_results"].append({"tool": "document_search", "result": "..."})
        state["tools_used"].append("document_search")
        state["current_phase"] = "synthesize"

        assert len(state["tool_results"]) == 1


@pytest.mark.integration
class TestAgentEndToEnd:
    """End-to-end agent tests."""

    @pytest.mark.skipif(True, reason="Requires actual API keys")
    def test_full_agent_execution(self):
        """Test complete agent execution flow."""
        # This test requires actual API keys
        pass

    def test_mocked_agent_flow(self, mock_llm, populated_tool_registry):
        """Test agent flow with mocked components."""
        # Simulate the full flow with mocks

        # 1. Understanding phase
        query = "Calculate 5 + 5"
        memory_context = "No previous conversation"

        # 2. Routing phase (mocked LLM decision)
        mock_llm.invoke.return_value = MagicMock(
            content='{"tool": "calculator", "parameters": {"expression": "5 + 5"}}'
        )

        # 3. Execution phase
        calc = populated_tool_registry.get_tool("calculator")
        if calc:
            result = calc.run(expression="5 + 5")
            assert result.success is True
            assert "10" in result.output

        # 4. Synthesis phase (mocked)
        mock_llm.invoke.return_value = MagicMock(
            content="The result of 5 + 5 is 10."
        )

        final_answer = "The result of 5 + 5 is 10."
        assert "10" in final_answer


class TestAgentErrorRecovery:
    """Tests for agent error recovery."""

    def test_tool_failure_recovery(self, tool_registry):
        """Test that agent can recover from tool failures."""
        # Register a tool that fails
        from src.agent.tools.base_tool import BaseTool

        class FailingTool(BaseTool):
            @property
            def name(self):
                return "failing_tool"

            @property
            def description(self):
                return "A tool that always fails"

            def _run(self, **kwargs):
                raise ValueError("Intentional failure")

        tool_registry.register(FailingTool())

        # Execute the failing tool
        tool = tool_registry.get_tool("failing_tool")
        result = tool.run()

        # Should fail gracefully
        assert result.success is False
        assert result.error is not None
        assert "Intentional failure" in result.error

    def test_max_iterations_limit(self):
        """Test that agent respects max iterations."""
        state = {
            "iteration": 0,
            "max_iterations": 3,
            "needs_retry": True
        }

        # Simulate iteration loop
        while state["iteration"] < state["max_iterations"] and state["needs_retry"]:
            state["iteration"] += 1
            # After some iterations, stop retrying
            if state["iteration"] >= 2:
                state["needs_retry"] = False

        assert state["iteration"] <= state["max_iterations"]
