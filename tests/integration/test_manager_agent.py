"""
Integration tests for Manager Agent and related features.

Tests:
- Specialized Agents (Dev, Doc, Security, QA)
- Manager Memory (persistence, recommendations)
- Task Scheduler (scheduling, management)
- Full Manager Agent (orchestration)

Run with: pytest tests/integration/test_manager_agent.py -v
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_rag_chain():
    """Create a mock RAG chain for testing."""
    mock_chain = MagicMock()
    mock_chain.llm = MagicMock()
    mock_chain.get_relevant_context = MagicMock(return_value="Mock context")
    return mock_chain


@pytest.fixture
def mock_llm_response():
    """Factory for creating mock LLM responses."""
    def _create_response(content: str):
        mock_response = MagicMock()
        mock_response.content = content
        return mock_response
    return _create_response


@pytest.fixture
def temp_storage_path():
    """Create a temporary directory for storage tests."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_rag_chain_with_responses(mock_rag_chain, mock_llm_response):
    """RAG chain with intelligent mock responses."""
    def smart_invoke(prompt):
        prompt_str = str(prompt).lower()
        if "code" in prompt_str or "implement" in prompt_str:
            return mock_llm_response("```python\ndef example(): pass\n```")
        elif "document" in prompt_str or "readme" in prompt_str:
            return mock_llm_response("# Documentation\n\nThis is a guide.")
        elif "security" in prompt_str or "vulnerability" in prompt_str:
            return mock_llm_response("## Security Report\n\n- No critical issues")
        elif "requirement" in prompt_str:
            return mock_llm_response("REQ-001: User login\nREQ-002: Password reset")
        elif "test" in prompt_str:
            return mock_llm_response("TC-001: Test login\nTC-002: Test logout")
        else:
            return mock_llm_response("Generic response")

    mock_rag_chain.llm.invoke = smart_invoke
    return mock_rag_chain


# ============================================================================
# Specialized Agents Tests
# ============================================================================

class TestDevAgentInterface:
    """Tests for Developer Agent."""

    def test_import(self):
        """Test module import."""
        from src.agent.specialized_agents import DevAgentInterface
        assert DevAgentInterface is not None

    def test_initialization(self, mock_rag_chain):
        """Test agent initialization."""
        from src.agent.specialized_agents import DevAgentInterface
        agent = DevAgentInterface(mock_rag_chain)

        assert agent.rag_chain == mock_rag_chain
        assert agent.llm == mock_rag_chain.llm

    def test_capabilities(self, mock_rag_chain):
        """Test agent capabilities."""
        from src.agent.specialized_agents import DevAgentInterface
        agent = DevAgentInterface(mock_rag_chain)

        caps = agent.capabilities
        assert caps.name == "Developer Agent"
        assert "code_generator" in caps.tools
        assert "code" in caps.keywords

    def test_execute_code_generation(self, mock_rag_chain_with_responses):
        """Test code generation execution."""
        from src.agent.specialized_agents import DevAgentInterface
        agent = DevAgentInterface(mock_rag_chain_with_responses)

        result = agent.execute("Generate code for authentication")

        assert result["success"] is True
        assert "output" in result

    def test_execute_code_analysis(self, mock_rag_chain_with_responses):
        """Test code analysis execution."""
        from src.agent.specialized_agents import DevAgentInterface
        agent = DevAgentInterface(mock_rag_chain_with_responses)

        result = agent.execute("Analyze this code for issues")

        assert result["success"] is True

    def test_execute_refactoring(self, mock_rag_chain_with_responses):
        """Test refactoring suggestions."""
        from src.agent.specialized_agents import DevAgentInterface
        agent = DevAgentInterface(mock_rag_chain_with_responses)

        result = agent.execute("Refactor the login function")

        assert result["success"] is True


class TestDocAgentInterface:
    """Tests for Documentation Agent."""

    def test_import(self):
        """Test module import."""
        from src.agent.specialized_agents import DocAgentInterface
        assert DocAgentInterface is not None

    def test_initialization(self, mock_rag_chain):
        """Test agent initialization."""
        from src.agent.specialized_agents import DocAgentInterface
        agent = DocAgentInterface(mock_rag_chain)

        assert agent.rag_chain == mock_rag_chain

    def test_capabilities(self, mock_rag_chain):
        """Test agent capabilities."""
        from src.agent.specialized_agents import DocAgentInterface
        agent = DocAgentInterface(mock_rag_chain)

        caps = agent.capabilities
        assert caps.name == "Documentation Agent"
        assert "readme_generator" in caps.tools
        assert "document" in caps.keywords

    def test_execute_readme_generation(self, mock_rag_chain_with_responses):
        """Test README generation."""
        from src.agent.specialized_agents import DocAgentInterface
        agent = DocAgentInterface(mock_rag_chain_with_responses)

        result = agent.execute("Create README for auth module")

        assert result["success"] is True

    def test_execute_api_docs(self, mock_rag_chain_with_responses):
        """Test API documentation generation."""
        from src.agent.specialized_agents import DocAgentInterface
        agent = DocAgentInterface(mock_rag_chain_with_responses)

        result = agent.execute("Document the REST API endpoints")

        assert result["success"] is True


class TestSecurityAgentInterface:
    """Tests for Security Agent."""

    def test_import(self):
        """Test module import."""
        from src.agent.specialized_agents import SecurityAgentInterface
        assert SecurityAgentInterface is not None

    def test_initialization(self, mock_rag_chain):
        """Test agent initialization."""
        from src.agent.specialized_agents import SecurityAgentInterface
        agent = SecurityAgentInterface(mock_rag_chain)

        assert agent.rag_chain == mock_rag_chain

    def test_capabilities(self, mock_rag_chain):
        """Test agent capabilities."""
        from src.agent.specialized_agents import SecurityAgentInterface
        agent = SecurityAgentInterface(mock_rag_chain)

        caps = agent.capabilities
        assert caps.name == "Security Agent"
        assert "security_analyzer" in caps.tools
        assert "security" in caps.keywords

    def test_execute_security_analysis(self, mock_rag_chain_with_responses):
        """Test security analysis."""
        from src.agent.specialized_agents import SecurityAgentInterface
        agent = SecurityAgentInterface(mock_rag_chain_with_responses)

        result = agent.execute("Analyze security vulnerabilities in login")

        assert result["success"] is True

    def test_execute_owasp_check(self, mock_rag_chain_with_responses):
        """Test OWASP vulnerability check."""
        from src.agent.specialized_agents import SecurityAgentInterface
        agent = SecurityAgentInterface(mock_rag_chain_with_responses)

        result = agent.execute("Check for OWASP top 10 vulnerabilities")

        assert result["success"] is True


class TestQAAgentInterface:
    """Tests for QA Agent."""

    def test_import(self):
        """Test module import."""
        from src.agent.manager_agent import QAAgentInterface
        assert QAAgentInterface is not None

    def test_initialization(self, mock_rag_chain):
        """Test agent initialization."""
        from src.agent.manager_agent import QAAgentInterface
        agent = QAAgentInterface(mock_rag_chain)

        assert agent.rag_chain == mock_rag_chain

    def test_capabilities(self, mock_rag_chain):
        """Test agent capabilities."""
        from src.agent.manager_agent import QAAgentInterface
        agent = QAAgentInterface(mock_rag_chain)

        caps = agent.capabilities
        assert caps.name == "QA Agent"
        assert "test_case_generator" in caps.tools
        assert "test" in caps.keywords

    def test_execute_requirements(self, mock_rag_chain_with_responses):
        """Test requirements extraction."""
        from src.agent.manager_agent import QAAgentInterface
        agent = QAAgentInterface(mock_rag_chain_with_responses)

        result = agent.execute("Extract requirements for authentication")

        assert result["success"] is True


# ============================================================================
# Manager Memory Tests
# ============================================================================

class TestManagerMemory:
    """Tests for Manager Memory persistence."""

    def test_import(self):
        """Test module import."""
        from src.agent.manager_memory import ManagerMemory, ExecutionRecord
        assert ManagerMemory is not None
        assert ExecutionRecord is not None

    def test_initialization(self, temp_storage_path):
        """Test memory initialization."""
        from src.agent.manager_memory import ManagerMemory
        memory = ManagerMemory(storage_path=temp_storage_path)

        assert memory.storage_path == temp_storage_path
        assert memory.history_file.parent == temp_storage_path

    def test_record_execution(self, temp_storage_path):
        """Test recording an execution."""
        from src.agent.manager_memory import ManagerMemory
        memory = ManagerMemory(storage_path=temp_storage_path)

        result = {
            "success": True,
            "plan": None,
            "results": {"task_1": {"success": True, "output": "Done"}},
            "summary": "Completed"
        }

        record = memory.record_execution(
            goal="Test authentication",
            result=result,
            duration_seconds=30.0
        )

        assert record.id is not None
        assert record.goal == "Test authentication"
        assert record.success is True
        assert "testing" in record.tags or "authentication" in record.tags

    def test_find_similar_executions(self, temp_storage_path):
        """Test finding similar past executions."""
        from src.agent.manager_memory import ManagerMemory
        memory = ManagerMemory(storage_path=temp_storage_path)

        # Record some executions
        for goal in ["Test login", "Test authentication", "Test payments"]:
            memory.record_execution(
                goal=goal,
                result={"success": True, "results": {}, "summary": ""},
                duration_seconds=10.0
            )

        similar = memory.find_similar_executions("Test user login", limit=3)

        assert len(similar) > 0
        # "Test login" should be most similar
        assert any("login" in r.goal.lower() for r in similar)

    def test_get_recommendations(self, temp_storage_path):
        """Test getting recommendations for a goal."""
        from src.agent.manager_memory import ManagerMemory
        memory = ManagerMemory(storage_path=temp_storage_path)

        # Record execution
        memory.record_execution(
            goal="Test authentication module",
            result={"success": True, "results": {}, "summary": ""},
            duration_seconds=45.0
        )

        recommendations = memory.get_recommendations_for_goal("Test login feature")

        assert "suggested_agents" in recommendations
        assert "estimated_tasks" in recommendations

    def test_get_performance_summary(self, temp_storage_path):
        """Test getting performance summary."""
        from src.agent.manager_memory import ManagerMemory
        memory = ManagerMemory(storage_path=temp_storage_path)

        # Record executions
        memory.record_execution(
            goal="Test 1", result={"success": True, "results": {}, "summary": ""}, duration_seconds=10.0
        )
        memory.record_execution(
            goal="Test 2", result={"success": False, "results": {}, "summary": ""}, duration_seconds=20.0
        )

        summary = memory.get_performance_summary()

        assert summary["total_executions"] == 2
        assert summary["successful_executions"] == 1
        assert summary["success_rate"] == 0.5

    def test_persistence(self, temp_storage_path):
        """Test that data persists to files."""
        from src.agent.manager_memory import ManagerMemory

        # Create memory and record
        memory1 = ManagerMemory(storage_path=temp_storage_path)
        memory1.record_execution(
            goal="Persistent test",
            result={"success": True, "results": {}, "summary": ""},
            duration_seconds=5.0
        )

        # Create new memory instance (simulates restart)
        memory2 = ManagerMemory(storage_path=temp_storage_path)

        # Should load from file
        assert len(memory2._history) == 1
        assert memory2._history[0].goal == "Persistent test"

    def test_add_feedback(self, temp_storage_path):
        """Test adding user feedback."""
        from src.agent.manager_memory import ManagerMemory
        memory = ManagerMemory(storage_path=temp_storage_path)

        record = memory.record_execution(
            goal="Test with feedback",
            result={"success": True, "results": {}, "summary": ""},
            duration_seconds=10.0
        )

        memory.add_feedback(record.id, "Great results!", rating=5)

        updated = memory.get_history()[0]
        assert updated.user_feedback == "Great results!"
        assert updated.rating == 5


# ============================================================================
# Task Scheduler Tests
# ============================================================================

class TestTaskScheduler:
    """Tests for Task Scheduler."""

    def test_import(self):
        """Test module import."""
        from src.agent.task_scheduler import TaskScheduler, ScheduleType
        assert TaskScheduler is not None
        assert ScheduleType is not None

    def test_initialization(self, temp_storage_path):
        """Test scheduler initialization."""
        from src.agent.task_scheduler import TaskScheduler
        scheduler = TaskScheduler(manager_agent=None, storage_path=temp_storage_path)

        assert scheduler.storage_path == temp_storage_path
        assert scheduler._running is False

    def test_schedule_once(self, temp_storage_path):
        """Test one-time scheduling."""
        from src.agent.task_scheduler import TaskScheduler
        scheduler = TaskScheduler(manager_agent=None, storage_path=temp_storage_path)

        run_at = datetime.now() + timedelta(hours=1)
        task_id = scheduler.schedule_once(
            goal="Run QA once",
            run_at=run_at
        )

        assert task_id is not None
        task = scheduler.get_task(task_id)
        assert task.goal == "Run QA once"
        assert task.schedule_type == "once"

    def test_schedule_recurring_daily(self, temp_storage_path):
        """Test daily recurring scheduling."""
        from src.agent.task_scheduler import TaskScheduler
        scheduler = TaskScheduler(manager_agent=None, storage_path=temp_storage_path)

        task_id = scheduler.schedule_recurring(
            goal="Daily QA check",
            schedule_type="daily",
            time="09:00"
        )

        task = scheduler.get_task(task_id)
        assert task.schedule_type == "daily"
        assert task.config["time"] == "09:00"

    def test_schedule_recurring_weekly(self, temp_storage_path):
        """Test weekly recurring scheduling."""
        from src.agent.task_scheduler import TaskScheduler
        scheduler = TaskScheduler(manager_agent=None, storage_path=temp_storage_path)

        task_id = scheduler.schedule_recurring(
            goal="Weekly report",
            schedule_type="weekly",
            day_of_week=0,  # Monday
            time="08:00"
        )

        task = scheduler.get_task(task_id)
        assert task.schedule_type == "weekly"
        assert task.config["day_of_week"] == 0

    def test_enable_disable_task(self, temp_storage_path):
        """Test enabling and disabling tasks."""
        from src.agent.task_scheduler import TaskScheduler
        scheduler = TaskScheduler(manager_agent=None, storage_path=temp_storage_path)

        task_id = scheduler.schedule_recurring(
            goal="Test task",
            schedule_type="daily",
            time="10:00"
        )

        # Disable
        scheduler.disable_task(task_id)
        assert scheduler.get_task(task_id).enabled is False

        # Enable
        scheduler.enable_task(task_id)
        assert scheduler.get_task(task_id).enabled is True

    def test_delete_task(self, temp_storage_path):
        """Test deleting a task."""
        from src.agent.task_scheduler import TaskScheduler
        scheduler = TaskScheduler(manager_agent=None, storage_path=temp_storage_path)

        task_id = scheduler.schedule_once(
            goal="Delete me",
            run_at=datetime.now() + timedelta(hours=1)
        )

        assert scheduler.get_task(task_id) is not None

        scheduler.delete_task(task_id)

        assert scheduler.get_task(task_id) is None

    def test_get_all_tasks(self, temp_storage_path):
        """Test getting all tasks."""
        from src.agent.task_scheduler import TaskScheduler
        scheduler = TaskScheduler(manager_agent=None, storage_path=temp_storage_path)

        scheduler.schedule_recurring(goal="Task 1", schedule_type="daily", time="09:00")
        scheduler.schedule_recurring(goal="Task 2", schedule_type="weekly", time="10:00")

        all_tasks = scheduler.get_all_tasks()

        assert len(all_tasks) == 2

    def test_get_status(self, temp_storage_path):
        """Test getting scheduler status."""
        from src.agent.task_scheduler import TaskScheduler
        scheduler = TaskScheduler(manager_agent=None, storage_path=temp_storage_path)

        scheduler.schedule_recurring(goal="Status test", schedule_type="daily", time="09:00")

        status = scheduler.get_status()

        assert "running" in status
        assert "total_tasks" in status
        assert status["total_tasks"] == 1
        assert status["running"] is False

    def test_persistence(self, temp_storage_path):
        """Test task persistence."""
        from src.agent.task_scheduler import TaskScheduler

        # Create and schedule
        scheduler1 = TaskScheduler(manager_agent=None, storage_path=temp_storage_path)
        scheduler1.schedule_recurring(
            goal="Persistent task",
            schedule_type="daily",
            time="09:00"
        )

        # Create new instance (simulates restart)
        scheduler2 = TaskScheduler(manager_agent=None, storage_path=temp_storage_path)

        # Should load from file
        assert len(scheduler2.get_all_tasks()) == 1
        assert scheduler2.get_all_tasks()[0].goal == "Persistent task"


# ============================================================================
# Manager Agent Tests
# ============================================================================

class TestManagerAgent:
    """Tests for Manager Agent orchestration."""

    def test_import(self):
        """Test module import."""
        from src.agent.manager_agent import ManagerAgent
        assert ManagerAgent is not None

    def test_initialization(self):
        """Test manager initialization."""
        from src.agent.manager_agent import ManagerAgent
        manager = ManagerAgent(llm=None)

        assert manager.agents == {}
        assert manager.execution_history == []

    def test_register_agent(self, mock_rag_chain):
        """Test registering agents."""
        from src.agent.manager_agent import ManagerAgent, QAAgentInterface

        manager = ManagerAgent(llm=None)
        qa_agent = QAAgentInterface(mock_rag_chain)

        manager.register_agent("qa", qa_agent)

        assert "qa" in manager.agents
        assert manager.agents["qa"] == qa_agent

    def test_get_available_capabilities(self, mock_rag_chain):
        """Test getting all agent capabilities."""
        from src.agent.manager_agent import ManagerAgent, QAAgentInterface
        from src.agent.specialized_agents import DevAgentInterface

        manager = ManagerAgent(llm=None)
        manager.register_agent("qa", QAAgentInterface(mock_rag_chain))
        manager.register_agent("developer", DevAgentInterface(mock_rag_chain))

        caps = manager.get_available_capabilities()

        assert "qa" in caps
        assert "developer" in caps

    def test_create_plan_qa_keywords(self, mock_rag_chain):
        """Test plan creation with QA keywords."""
        from src.agent.manager_agent import ManagerAgent, QAAgentInterface

        manager = ManagerAgent(llm=None)
        manager.register_agent("qa", QAAgentInterface(mock_rag_chain))

        plan = manager.create_plan("Create test cases for authentication")

        assert plan.goal == "Create test cases for authentication"
        assert len(plan.tasks) > 0
        assert any(t.agent_type.value == "qa" for t in plan.tasks)

    def test_create_plan_bdd_keywords(self, mock_rag_chain):
        """Test plan creation with BDD keywords."""
        from src.agent.manager_agent import ManagerAgent, QAAgentInterface

        manager = ManagerAgent(llm=None)
        manager.register_agent("qa", QAAgentInterface(mock_rag_chain))

        plan = manager.create_plan("Create BDD scenarios for login")

        # Should include BDD task
        bdd_tasks = [t for t in plan.tasks if "bdd" in t.instruction.lower()]
        assert len(bdd_tasks) > 0

    def test_create_plan_multi_agent(self, mock_rag_chain):
        """Test plan creation involving multiple agents."""
        from src.agent.manager_agent import ManagerAgent, QAAgentInterface
        from src.agent.specialized_agents import DocAgentInterface, SecurityAgentInterface

        manager = ManagerAgent(llm=None)
        manager.register_agent("qa", QAAgentInterface(mock_rag_chain))
        manager.register_agent("documentation", DocAgentInterface(mock_rag_chain))
        manager.register_agent("security", SecurityAgentInterface(mock_rag_chain))

        plan = manager.create_plan("Document the API and check for security vulnerabilities")

        agent_types = {t.agent_type.value for t in plan.tasks}
        assert "documentation" in agent_types
        assert "security" in agent_types

    def test_execute_goal(self, mock_rag_chain_with_responses):
        """Test goal execution."""
        from src.agent.manager_agent import ManagerAgent, QAAgentInterface

        manager = ManagerAgent(llm=mock_rag_chain_with_responses.llm)
        manager.register_agent("qa", QAAgentInterface(mock_rag_chain_with_responses))

        result = manager.execute("Extract requirements for login")

        assert "success" in result
        assert "summary" in result
        assert "results" in result

    def test_execute_with_progress_callback(self, mock_rag_chain_with_responses):
        """Test execution with progress callback."""
        from src.agent.manager_agent import ManagerAgent, QAAgentInterface

        manager = ManagerAgent(llm=mock_rag_chain_with_responses.llm)
        manager.register_agent("qa", QAAgentInterface(mock_rag_chain_with_responses))

        progress_updates = []
        def callback(msg, pct):
            progress_updates.append((msg, pct))

        manager.execute("Test login", progress_callback=callback)

        assert len(progress_updates) > 0
        assert progress_updates[-1][1] == 100  # Should end at 100%

    def test_get_history(self, mock_rag_chain_with_responses):
        """Test execution history."""
        from src.agent.manager_agent import ManagerAgent, QAAgentInterface

        manager = ManagerAgent(llm=mock_rag_chain_with_responses.llm)
        manager.register_agent("qa", QAAgentInterface(mock_rag_chain_with_responses))

        manager.execute("Test 1")
        manager.execute("Test 2")

        history = manager.get_history()

        assert len(history) == 2


# ============================================================================
# Factory Function Tests
# ============================================================================

class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_manager_with_qa_agent(self, mock_rag_chain):
        """Test creating manager with QA agent."""
        from src.agent.manager_agent import create_manager_with_qa_agent

        manager = create_manager_with_qa_agent(mock_rag_chain)

        assert "qa" in manager.agents

    def test_create_full_manager(self, mock_rag_chain):
        """Test creating full manager with all agents."""
        from src.agent.manager_agent import create_full_manager

        manager = create_full_manager(mock_rag_chain, enable_memory=False)

        assert "qa" in manager.agents
        assert "developer" in manager.agents
        assert "documentation" in manager.agents
        assert "security" in manager.agents

    def test_create_full_manager_with_memory(self, mock_rag_chain, temp_storage_path):
        """Test creating full manager with memory enabled."""
        from src.agent.manager_agent import create_full_manager

        # Patch default memory path
        with patch('src.agent.manager_memory.DEFAULT_MEMORY_PATH', temp_storage_path):
            manager = create_full_manager(mock_rag_chain, enable_memory=True)

            assert manager.memory is not None

    def test_create_manager_with_scheduler(self, mock_rag_chain, temp_storage_path):
        """Test creating manager with scheduler."""
        from src.agent.manager_agent import ManagerAgent, QAAgentInterface
        from src.agent.task_scheduler import TaskScheduler

        # Create manager manually for this test
        manager = ManagerAgent(llm=mock_rag_chain.llm)
        manager.register_agent("qa", QAAgentInterface(mock_rag_chain))

        scheduler = TaskScheduler(
            manager_agent=manager,
            storage_path=temp_storage_path
        )

        assert manager is not None
        assert scheduler is not None
        assert scheduler._running is False


# ============================================================================
# Integration Tests
# ============================================================================

class TestManagerIntegration:
    """Integration tests for Manager Agent system."""

    def test_full_workflow(self, mock_rag_chain_with_responses, temp_storage_path):
        """Test complete workflow: schedule -> execute -> persist."""
        from src.agent.manager_agent import ManagerAgent, QAAgentInterface
        from src.agent.manager_memory import ManagerMemory
        from src.agent.task_scheduler import TaskScheduler

        # Setup
        memory = ManagerMemory(storage_path=temp_storage_path)
        manager = ManagerAgent(
            llm=mock_rag_chain_with_responses.llm,
            memory=memory
        )
        manager.register_agent("qa", QAAgentInterface(mock_rag_chain_with_responses))

        scheduler = TaskScheduler(
            manager_agent=manager,
            storage_path=temp_storage_path
        )

        # Schedule a task
        task_id = scheduler.schedule_recurring(
            goal="Test authentication",
            schedule_type="daily",
            time="09:00"
        )

        # Execute manually (instead of waiting for scheduler)
        result = manager.execute("Test authentication")

        # Verify memory recorded
        history = memory.get_history()
        assert len(history) == 1

        # Verify recommendations work
        recommendations = memory.get_recommendations_for_goal("Test login")
        assert "suggested_agents" in recommendations

    def test_all_agents_execute(self, mock_rag_chain_with_responses):
        """Test that all agents can execute instructions without crashing."""
        from src.agent.manager_agent import QAAgentInterface
        from src.agent.specialized_agents import (
            DevAgentInterface,
            DocAgentInterface,
            SecurityAgentInterface
        )

        agents = [
            (QAAgentInterface(mock_rag_chain_with_responses), "Test the login"),
            (DevAgentInterface(mock_rag_chain_with_responses), "Generate code"),
            (DocAgentInterface(mock_rag_chain_with_responses), "Create documentation"),
            (SecurityAgentInterface(mock_rag_chain_with_responses), "Check security"),
        ]

        for agent, instruction in agents:
            result = agent.execute(instruction)
            # All agents should return a result dict with expected keys
            assert "success" in result, f"{agent.capabilities.name} missing 'success' key"
            assert "output" in result, f"{agent.capabilities.name} missing 'output' key"
            # Dev, Doc, Security agents should succeed with mock responses
            if not isinstance(agent, QAAgentInterface):
                assert result["success"] is True, f"{agent.capabilities.name} failed"

    def test_error_handling(self, mock_rag_chain):
        """Test error handling when LLM fails."""
        from src.agent.manager_agent import QAAgentInterface

        mock_rag_chain.llm.invoke.side_effect = Exception("LLM error")
        agent = QAAgentInterface(mock_rag_chain)

        result = agent.execute("This should fail gracefully")

        # Should not crash, return failure result
        assert result["success"] is False or "error" in str(result.get("output", "")).lower()


# ============================================================================
# Run with: pytest tests/integration/test_manager_agent.py -v
# ============================================================================
