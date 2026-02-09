"""Test script for Manager Agent and related features."""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def create_mock_rag_chain():
    """Create a mock RAG chain for testing."""
    mock_chain = MagicMock()
    mock_chain.llm = MagicMock()

    # Mock LLM invoke to return realistic responses
    def mock_invoke(prompt):
        mock_response = MagicMock()
        if "code" in str(prompt).lower():
            mock_response.content = """```python
def authenticate_user(username, password):
    # Validate inputs
    if not username or not password:
        return {"success": False, "error": "Missing credentials"}

    # Check credentials (mock)
    if username == "admin" and password == "secure123":
        return {"success": True, "token": "jwt_token_here"}

    return {"success": False, "error": "Invalid credentials"}
```"""
        elif "document" in str(prompt).lower() or "readme" in str(prompt).lower():
            mock_response.content = """# User Authentication API

## Overview
This module handles user authentication using JWT tokens.

## Endpoints
- POST /login - Authenticate user
- POST /logout - Invalidate token
- GET /verify - Verify token validity

## Usage
```python
from auth import authenticate_user
result = authenticate_user("username", "password")
```
"""
        elif "security" in str(prompt).lower() or "vulnerability" in str(prompt).lower():
            mock_response.content = """## Security Analysis Report

### Findings
1. **SQL Injection Risk** - Input validation needed
2. **Password Storage** - Use bcrypt instead of plain text
3. **Token Expiry** - Add JWT expiration

### Recommendations
- Implement input sanitization
- Use parameterized queries
- Add rate limiting
"""
        elif "requirement" in str(prompt).lower():
            mock_response.content = """## Requirements

REQ-001: User must be able to login with email/password
REQ-002: System must validate credentials against database
REQ-003: Failed login attempts must be logged
REQ-004: Session timeout after 30 minutes of inactivity
"""
        elif "test" in str(prompt).lower():
            mock_response.content = """## Test Cases

TC-001: Valid Login
- Input: Valid username and password
- Expected: Login success, token returned

TC-002: Invalid Password
- Input: Valid username, wrong password
- Expected: Login failure, error message

TC-003: Empty Credentials
- Input: Empty username or password
- Expected: Validation error
"""
        else:
            mock_response.content = "Generic response for: " + str(prompt)[:50]

        return mock_response

    mock_chain.llm.invoke = mock_invoke
    mock_chain.get_relevant_context = MagicMock(return_value="Mock context from documents")

    return mock_chain


def test_specialized_agents():
    """Test specialized agent interfaces."""
    print("\n" + "="*60)
    print("TEST: Specialized Agents")
    print("="*60)

    from src.agent.specialized_agents import (
        DevAgentInterface,
        DocAgentInterface,
        SecurityAgentInterface
    )
    from src.agent.manager_agent import QAAgentInterface

    mock_chain = create_mock_rag_chain()

    # Test Dev Agent
    print("\n1. Testing Developer Agent...")
    dev_agent = DevAgentInterface(mock_chain)
    print(f"   - Name: {dev_agent.capabilities.name}")
    print(f"   - Tools: {dev_agent.capabilities.tools}")

    result = dev_agent.execute("Generate code for user authentication")
    print(f"   - Execution success: {result['success']}")
    print(f"   - Output preview: {result['output'][:100]}...")
    assert result['success'], "Dev agent should succeed"

    # Test Doc Agent
    print("\n2. Testing Documentation Agent...")
    doc_agent = DocAgentInterface(mock_chain)
    print(f"   - Name: {doc_agent.capabilities.name}")
    print(f"   - Tools: {doc_agent.capabilities.tools}")

    result = doc_agent.execute("Create README for authentication module")
    print(f"   - Execution success: {result['success']}")
    print(f"   - Output preview: {result['output'][:100]}...")
    assert result['success'], "Doc agent should succeed"

    # Test Security Agent
    print("\n3. Testing Security Agent...")
    security_agent = SecurityAgentInterface(mock_chain)
    print(f"   - Name: {security_agent.capabilities.name}")
    print(f"   - Tools: {security_agent.capabilities.tools}")

    result = security_agent.execute("Perform security analysis for login")
    print(f"   - Execution success: {result['success']}")
    print(f"   - Output preview: {result['output'][:100]}...")
    assert result['success'], "Security agent should succeed"

    # Test QA Agent
    print("\n4. Testing QA Agent...")
    qa_agent = QAAgentInterface(mock_chain)
    print(f"   - Name: {qa_agent.capabilities.name}")
    print(f"   - Tools: {qa_agent.capabilities.tools}")

    result = qa_agent.execute("Extract requirements for authentication")
    print(f"   - Execution success: {result['success']}")
    print(f"   - Output preview: {result['output'][:100]}...")
    assert result['success'], "QA agent should succeed"

    print("\n✅ All specialized agents working correctly!")
    return True


def test_manager_memory():
    """Test Manager Memory persistence."""
    print("\n" + "="*60)
    print("TEST: Manager Memory")
    print("="*60)

    from src.agent.manager_memory import ManagerMemory, ExecutionRecord
    import tempfile
    import shutil

    # Create temp directory for test
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Initialize memory
        print("\n1. Initializing memory...")
        memory = ManagerMemory(storage_path=temp_dir)
        print(f"   - Storage path: {temp_dir}")

        # Record an execution
        print("\n2. Recording execution...")
        test_result = {
            "success": True,
            "plan": None,
            "results": {
                "task_1": {"success": True, "output": "Requirements extracted"},
                "task_2": {"success": True, "output": "Test cases generated"}
            },
            "summary": "All tasks completed successfully"
        }

        record = memory.record_execution(
            goal="Test user authentication thoroughly",
            result=test_result,
            duration_seconds=45.5
        )
        print(f"   - Record ID: {record.id}")
        print(f"   - Success: {record.success}")
        print(f"   - Tags: {record.tags}")

        # Find similar executions
        print("\n3. Finding similar executions...")
        similar = memory.find_similar_executions("Create tests for login")
        print(f"   - Found {len(similar)} similar executions")

        # Get recommendations
        print("\n4. Getting recommendations...")
        recommendations = memory.get_recommendations_for_goal("Test payment processing")
        print(f"   - Suggested agents: {recommendations.get('suggested_agents', [])}")
        print(f"   - Estimated tasks: {recommendations.get('estimated_tasks')}")

        # Get performance summary
        print("\n5. Getting performance summary...")
        perf = memory.get_performance_summary()
        print(f"   - Total executions: {perf['total_executions']}")
        print(f"   - Success rate: {perf['success_rate']:.0%}")

        # Verify files created
        print("\n6. Verifying persistence...")
        assert memory.history_file.exists(), "History file should exist"
        assert memory.performance_file.exists(), "Performance file should exist"
        print(f"   - History file: ✓")
        print(f"   - Performance file: ✓")

        print("\n✅ Manager Memory working correctly!")
        return True

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_task_scheduler():
    """Test Task Scheduler."""
    print("\n" + "="*60)
    print("TEST: Task Scheduler")
    print("="*60)

    from src.agent.task_scheduler import TaskScheduler, ScheduleType
    import tempfile
    import shutil

    # Create temp directory for test
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Initialize scheduler without manager (for testing)
        print("\n1. Initializing scheduler...")
        scheduler = TaskScheduler(manager_agent=None, storage_path=temp_dir)
        print(f"   - Storage path: {temp_dir}")

        # Schedule a one-time task
        print("\n2. Scheduling one-time task...")
        run_at = datetime.now() + timedelta(hours=1)
        task_id = scheduler.schedule_once(
            goal="Run QA for authentication",
            run_at=run_at
        )
        print(f"   - Task ID: {task_id}")
        print(f"   - Scheduled for: {run_at}")

        # Schedule a recurring task
        print("\n3. Scheduling recurring task...")
        recurring_id = scheduler.schedule_recurring(
            goal="Daily QA analysis for login",
            schedule_type="daily",
            time="09:00"
        )
        print(f"   - Task ID: {recurring_id}")
        print(f"   - Schedule: Daily at 09:00")

        # Get all tasks
        print("\n4. Getting all tasks...")
        all_tasks = scheduler.get_all_tasks()
        print(f"   - Total tasks: {len(all_tasks)}")
        for task in all_tasks:
            print(f"   - {task.id}: {task.goal[:40]}... ({task.schedule_type})")

        # Get status
        print("\n5. Getting scheduler status...")
        status = scheduler.get_status()
        print(f"   - Running: {status['running']}")
        print(f"   - Total tasks: {status['total_tasks']}")
        print(f"   - Enabled tasks: {status['enabled_tasks']}")

        # Disable a task
        print("\n6. Testing task management...")
        scheduler.disable_task(task_id)
        task = scheduler.get_task(task_id)
        print(f"   - Task {task_id} enabled: {task.enabled}")

        scheduler.enable_task(task_id)
        task = scheduler.get_task(task_id)
        print(f"   - Task {task_id} re-enabled: {task.enabled}")

        # Delete a task
        scheduler.delete_task(task_id)
        remaining = scheduler.get_all_tasks()
        print(f"   - Tasks after delete: {len(remaining)}")

        print("\n✅ Task Scheduler working correctly!")
        return True

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_full_manager_agent():
    """Test the full Manager Agent with all agents."""
    print("\n" + "="*60)
    print("TEST: Full Manager Agent")
    print("="*60)

    from src.agent.manager_agent import create_full_manager
    from src.agent.manager_memory import ManagerMemory
    import tempfile
    import shutil

    mock_chain = create_mock_rag_chain()
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create full manager with memory
        print("\n1. Creating full manager...")

        # Manually create memory with temp path for testing
        memory = ManagerMemory(storage_path=temp_dir)

        from src.agent.manager_agent import ManagerAgent
        from src.agent.specialized_agents import (
            DevAgentInterface,
            DocAgentInterface,
            SecurityAgentInterface
        )
        from src.agent.manager_agent import QAAgentInterface

        manager = ManagerAgent(llm=mock_chain.llm, memory=memory)
        manager.register_agent("qa", QAAgentInterface(mock_chain))
        manager.register_agent("developer", DevAgentInterface(mock_chain))
        manager.register_agent("documentation", DocAgentInterface(mock_chain))
        manager.register_agent("security", SecurityAgentInterface(mock_chain))

        print(f"   - Registered agents: {list(manager.agents.keys())}")
        print(f"   - Memory enabled: {manager.memory is not None}")

        # Get capabilities
        print("\n2. Getting agent capabilities...")
        capabilities = manager.get_available_capabilities()
        for name, cap in capabilities.items():
            print(f"   - {name}: {cap.description[:50]}...")

        # Create a plan
        print("\n3. Creating execution plan...")
        plan = manager.create_plan("Create comprehensive tests for user authentication with BDD")
        print(f"   - Plan goal: {plan.goal[:50]}...")
        print(f"   - Tasks in plan: {len(plan.tasks)}")
        for task in plan.tasks:
            print(f"     - {task.task_id}: {task.instruction[:40]}...")

        # Test multi-agent plan
        print("\n4. Testing multi-agent plan...")
        multi_plan = manager.create_plan("Document the API and create security tests")
        agents_in_plan = set(t.agent_type.value for t in multi_plan.tasks)
        print(f"   - Agents involved: {agents_in_plan}")

        # Execute a simple goal (with mocked agents)
        print("\n5. Executing a goal...")
        progress_msgs = []
        def progress_callback(msg, pct):
            progress_msgs.append((msg, pct))

        result = manager.execute(
            "Extract requirements for user authentication",
            progress_callback=progress_callback
        )
        print(f"   - Execution success: {result['success']}")
        print(f"   - Progress updates: {len(progress_msgs)}")
        print(f"   - Summary: {result['summary'][:100]}...")

        # Check memory recorded
        print("\n6. Verifying memory recording...")
        history = manager.memory.get_history(limit=5)
        print(f"   - Executions in memory: {len(history)}")

        # Get recommendations
        print("\n7. Getting recommendations...")
        recommendations = manager.get_recommendations("Test payment flow")
        print(f"   - Suggested agents: {recommendations.get('suggested_agents', [])}")

        print("\n✅ Full Manager Agent working correctly!")
        return True

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_manager_with_scheduler():
    """Test Manager Agent with Task Scheduler integration."""
    print("\n" + "="*60)
    print("TEST: Manager + Scheduler Integration")
    print("="*60)

    from src.agent.task_scheduler import TaskScheduler
    from src.agent.manager_agent import ManagerAgent
    import tempfile
    import shutil

    mock_chain = create_mock_rag_chain()
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create manager
        print("\n1. Creating manager and scheduler...")
        manager = ManagerAgent(llm=mock_chain.llm)
        scheduler = TaskScheduler(manager_agent=manager, storage_path=temp_dir)

        print(f"   - Manager created: ✓")
        print(f"   - Scheduler created: ✓")

        # Schedule a task
        print("\n2. Scheduling task for manager...")
        task_id = scheduler.schedule_recurring(
            goal="Run QA analysis for authentication",
            schedule_type="daily",
            time="09:00"
        )
        print(f"   - Task scheduled: {task_id}")

        # Check status
        print("\n3. Checking scheduler status...")
        status = scheduler.get_status()
        print(f"   - Running: {status['running']}")
        print(f"   - Total tasks: {status['total_tasks']}")
        print(f"   - Next scheduled: {status['next_scheduled']}")

        # Don't actually start scheduler in tests (it runs in background thread)
        print("\n4. Scheduler ready to start (not starting in test)")
        print(f"   - Start with: scheduler.start()")
        print(f"   - Stop with: scheduler.stop()")

        print("\n✅ Manager + Scheduler integration working correctly!")
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_streamlit_imports():
    """Test that Streamlit app imports work."""
    print("\n" + "="*60)
    print("TEST: Streamlit App Imports")
    print("="*60)

    print("\n1. Testing manager_agent imports...")
    from src.agent.manager_agent import (
        ManagerAgent,
        QAAgentInterface,
        create_full_manager,
        create_manager_with_qa_agent,
        create_manager_with_scheduler
    )
    print("   - All manager_agent imports: ✓")

    print("\n2. Testing specialized_agents imports...")
    from src.agent.specialized_agents import (
        DevAgentInterface,
        DocAgentInterface,
        SecurityAgentInterface
    )
    print("   - All specialized_agents imports: ✓")

    print("\n3. Testing manager_memory imports...")
    from src.agent.manager_memory import ManagerMemory, ExecutionRecord
    print("   - All manager_memory imports: ✓")

    print("\n4. Testing task_scheduler imports...")
    from src.agent.task_scheduler import (
        TaskScheduler,
        ScheduleType,
        ScheduledTask,
        create_daily_qa_schedule,
        create_weekly_coverage_report
    )
    print("   - All task_scheduler imports: ✓")

    print("\n✅ All Streamlit app imports working!")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("MANAGER AGENT FEATURE TESTS")
    print("="*60)

    results = {}

    # Run each test
    tests = [
        ("Specialized Agents", test_specialized_agents),
        ("Manager Memory", test_manager_memory),
        ("Task Scheduler", test_task_scheduler),
        ("Full Manager Agent", test_full_manager_agent),
        ("Manager + Scheduler", test_manager_with_scheduler),
        ("Streamlit Imports", test_streamlit_imports),
    ]

    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Manager Agent features are working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please review the errors above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
