"""Manager Agent - Orchestrates multiple specialized agents.

This module implements a hierarchical agent system where a Manager Agent
coordinates specialized worker agents (QA Agent, Dev Agent, etc.) to
accomplish complex tasks.

Architecture:
    Manager Agent (Planner/Coordinator)
         │
         ├── QA Agent (Testing & Quality)
         ├── Dev Agent (Code Generation) [Future]
         └── Doc Agent (Documentation) [Future]

Usage:
    manager = ManagerAgent(llm=llm, agents={"qa": qa_agent})
    result = manager.execute("Create comprehensive tests for user authentication")
"""

# Standard library
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# Local
from src.agent.types import AgentCapability, AgentType, ExecutionPlan, TaskAssignment
from src.logging_config import get_logger

logger = get_logger(__name__)


class QAAgentInterface:
    """Interface to wrap QA Agent for manager communication.

    This wraps the existing QA tools and agent to provide a clean
    interface for the manager agent to interact with.
    """

    def __init__(self, rag_chain, tool_registry=None):
        """
        Initialize QA Agent interface.

        Args:
            rag_chain: RAGChain instance for document retrieval
            tool_registry: Optional ToolRegistry with registered tools
        """
        self.rag_chain = rag_chain
        self.tool_registry = tool_registry
        self._tools = {}
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize QA tools."""
        try:
            from src.agent.tools import (
                QAAnalysisTool,
                BugReportTool,
                TestStrategyTool,
                RequirementsExtractorTool,
                TraceabilityMatrixTool,
                BDDGeneratorTool,
                TestDataGeneratorTool
            )

            self._tools = {
                "test_case_generator": self._create_test_generator(),
                "qa_analysis": QAAnalysisTool(self.rag_chain),
                "bug_report": BugReportTool(self.rag_chain),
                "test_strategy": TestStrategyTool(self.rag_chain),
                "requirements_extractor": RequirementsExtractorTool(self.rag_chain),
                "traceability_matrix": TraceabilityMatrixTool(self.rag_chain),
                "bdd_generator": BDDGeneratorTool(self.rag_chain),
                "test_data_generator": TestDataGeneratorTool(self.rag_chain)
            }
        except ImportError as e:
            logger.warning(f"Could not import some QA tools: {e}")

    def _create_test_generator(self):
        """Create test generator tool if available."""
        try:
            from src.agent.tools.test_generator_tool import TestGeneratorTool
            return TestGeneratorTool(self.rag_chain)
        except ImportError:
            return None

    @property
    def capabilities(self) -> AgentCapability:
        """Return QA agent capabilities."""
        return AgentCapability(
            name="QA Agent",
            description="Specialized in test automation, quality assurance, and testing workflows",
            tools=list(self._tools.keys()),
            keywords=[
                "test", "testing", "qa", "quality", "bug", "defect",
                "requirements", "coverage", "traceability", "bdd",
                "gherkin", "test data", "test cases", "test strategy"
            ]
        )

    def execute(self, instruction: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute an instruction from the manager.

        Args:
            instruction: What the manager wants done
            context: Additional context (previous results, constraints)

        Returns:
            Dict with 'success', 'output', 'tool_used', 'metadata'
        """
        context = context or {}

        # Determine which tool to use based on instruction
        tool_name, params = self._route_instruction(instruction, context)

        if not tool_name or tool_name not in self._tools:
            return {
                "success": False,
                "output": f"Could not determine appropriate tool for: {instruction}",
                "tool_used": None,
                "metadata": {}
            }

        tool = self._tools[tool_name]
        if tool is None:
            return {
                "success": False,
                "output": f"Tool '{tool_name}' is not available",
                "tool_used": tool_name,
                "metadata": {}
            }

        try:
            result = tool.run(**params)
            return {
                "success": result.success if hasattr(result, 'success') else True,
                "output": result.output if hasattr(result, 'output') else str(result),
                "tool_used": tool_name,
                "metadata": {
                    "duration": getattr(result, 'duration', None),
                    "params": params
                }
            }
        except Exception as e:
            logger.error(f"Error executing {tool_name}: {e}")
            return {
                "success": False,
                "output": f"Error: {str(e)}",
                "tool_used": tool_name,
                "metadata": {"error": str(e)}
            }

    def _route_instruction(self, instruction: str, context: Dict) -> tuple:
        """Route instruction to appropriate tool with parameters."""
        instruction_lower = instruction.lower()

        # Extract previous results for context chaining
        previous_results = context.get("previous_results", {})

        # Find requirements from previous task outputs
        requirements_context = ""
        for task_id, result in previous_results.items():
            output = result.get("output", "")
            # Check if this looks like requirements output
            if "REQ-" in output or "requirement" in output.lower():
                requirements_context = output
                break

        # Find test cases from previous task outputs
        test_cases_context = ""
        for task_id, result in previous_results.items():
            output = result.get("output", "")
            if "TC-" in output or "test case" in output.lower():
                test_cases_context = output
                break

        # Build enhanced query with requirements context
        def build_query_with_requirements(base_instruction):
            if requirements_context:
                return f"{base_instruction}\n\nBased on these requirements:\n{requirements_context[:2000]}"
            return base_instruction

        # Routing rules based on keywords
        routing_rules = [
            # Test case generation - USE requirements from previous tasks
            (["generate test", "create test", "write test case"],
             "test_case_generator",
             {"query": build_query_with_requirements(instruction)}),

            # QA Analysis - USE test cases from previous tasks
            (["analyze test", "coverage gap", "test coverage", "review test"],
             "qa_analysis",
             {"test_cases": test_cases_context or context.get("test_cases", instruction)}),

            # Bug reports
            (["bug report", "report bug", "document bug", "create bug"],
             "bug_report",
             {"bug_description": context.get("bug_description", instruction)}),

            # Test strategy
            (["test strategy", "testing plan", "test approach", "how to test"],
             "test_strategy",
             {"feature_description": instruction}),

            # Requirements
            (["extract requirement", "get requirement", "find requirement"],
             "requirements_extractor",
             {"topic": instruction}),

            # Traceability - USE requirements if available
            (["traceability", "coverage matrix", "req to test", "mapping"],
             "traceability_matrix",
             {"topic": build_query_with_requirements(instruction)}),

            # BDD - USE requirements for better scenarios
            (["bdd", "gherkin", "feature file", "cucumber", "behave", "given when then"],
             "bdd_generator",
             {"feature_description": build_query_with_requirements(instruction)}),

            # Test data
            (["test data", "generate data", "sample data", "mock data"],
             "test_data_generator",
             {"field_definitions": context.get("fields", instruction)})
        ]

        for keywords, tool_name, params in routing_rules:
            if any(kw in instruction_lower for kw in keywords):
                return tool_name, params

        # Default to test case generation for generic requests
        return "test_case_generator", {"query": build_query_with_requirements(instruction)}

    def run_pipeline(self, topic: str, progress_callback: Callable = None) -> Dict[str, Any]:
        """
        Run the full QA pipeline.

        Args:
            topic: Feature/topic to analyze
            progress_callback: Optional callback(message, percentage)

        Returns:
            Combined pipeline results
        """
        try:
            from src.agent.qa_pipeline import QAPipeline
            pipeline = QAPipeline(self.rag_chain, progress_callback)
            return pipeline.run(topic)
        except ImportError:
            # Manual pipeline execution
            results = {}

            # Stage 1: Extract requirements
            req_result = self.execute(f"Extract requirements for {topic}")
            results["requirements"] = req_result

            # Stage 2: Generate test cases
            tc_result = self.execute(f"Generate test cases for {topic}")
            results["test_cases"] = tc_result

            # Stage 3: Analyze gaps
            if tc_result.get("success"):
                gap_result = self.execute(
                    "Analyze test coverage gaps",
                    {"test_cases": tc_result["output"]}
                )
                results["gap_analysis"] = gap_result

            return {
                "success": all(r.get("success", False) for r in results.values()),
                "stages": results
            }


class ManagerAgent:
    """
    Manager Agent that orchestrates specialized worker agents.

    The manager:
    1. Receives high-level goals from users
    2. Creates execution plans
    3. Delegates tasks to appropriate agents
    4. Aggregates and synthesizes results
    5. Handles errors and retries
    6. Learns from past executions (with memory)

    Example:
        manager = ManagerAgent(llm=llm)
        manager.register_agent("qa", qa_agent_interface)
        result = manager.execute("Ensure user authentication is fully tested")
    """

    def __init__(self, llm=None, agents: Dict[str, Any] = None, memory=None):
        """
        Initialize Manager Agent.

        Args:
            llm: Language model for planning and synthesis
            agents: Dict of agent_name -> agent_interface
            memory: Optional ManagerMemory for persistent history
        """
        self.llm = llm
        self.agents: Dict[str, Any] = agents or {}
        self.execution_history: List[Dict] = []
        self.current_plan: Optional[ExecutionPlan] = None
        self.memory = memory  # ManagerMemory instance for persistence

    def register_agent(self, name: str, agent_interface: Any):
        """Register a specialized agent."""
        self.agents[name] = agent_interface
        logger.info(f"Registered agent: {name}")

    def get_available_capabilities(self) -> Dict[str, AgentCapability]:
        """Get capabilities of all registered agents."""
        capabilities = {}
        for name, agent in self.agents.items():
            if hasattr(agent, 'capabilities'):
                capabilities[name] = agent.capabilities
        return capabilities

    def create_plan(self, goal: str) -> ExecutionPlan:
        """
        Create an execution plan for a goal.

        Uses LLM to break down the goal into tasks and assign to agents.
        """
        # Get available capabilities
        capabilities = self.get_available_capabilities()

        if self.llm:
            # Use LLM for intelligent planning
            plan = self._llm_plan(goal, capabilities)
        else:
            # Rule-based planning fallback
            plan = self._rule_based_plan(goal, capabilities)

        self.current_plan = plan
        return plan

    def _llm_plan(self, goal: str, capabilities: Dict) -> ExecutionPlan:
        """Use LLM to create execution plan."""
        from langchain_core.prompts import ChatPromptTemplate

        cap_text = "\n".join([
            f"- {name}: {cap.description} (tools: {', '.join(cap.tools)})"
            for name, cap in capabilities.items()
        ])

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a task planning agent. Break down goals into specific tasks.

Available agents and their capabilities:
{capabilities}

For each task, specify:
1. Which agent should handle it
2. Clear instruction for that agent
3. Any dependencies on other tasks
4. Priority (1=highest)

Output as JSON:
{{
    "tasks": [
        {{
            "id": "task_1",
            "agent": "qa",
            "instruction": "specific instruction",
            "priority": 1,
            "dependencies": []
        }}
    ],
    "execution_order": ["task_1", "task_2"]
}}"""),
            ("human", "Goal: {goal}\n\nCreate an execution plan:")
        ])

        try:
            messages = prompt.format_messages(
                capabilities=cap_text,
                goal=goal
            )
            response = self.llm.invoke(messages)

            # Parse JSON response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response.content)
            if json_match:
                plan_data = json.loads(json_match.group())

                tasks = []
                for t in plan_data.get("tasks", []):
                    agent_type = AgentType.QA if t.get("agent") == "qa" else AgentType.QA
                    tasks.append(TaskAssignment(
                        task_id=t.get("id", f"task_{len(tasks)+1}"),
                        agent_type=agent_type,
                        instruction=t.get("instruction", ""),
                        priority=t.get("priority", 1),
                        dependencies=t.get("dependencies", [])
                    ))

                return ExecutionPlan(
                    goal=goal,
                    tasks=tasks,
                    execution_order=plan_data.get("execution_order", [t.task_id for t in tasks]),
                    estimated_steps=len(tasks)
                )
        except Exception as e:
            logger.warning(f"LLM planning failed, falling back to rules: {e}")

        return self._rule_based_plan(goal, capabilities)

    def _rule_based_plan(self, goal: str, capabilities: Dict) -> ExecutionPlan:
        """Create plan using keyword rules."""
        goal_lower = goal.lower()
        tasks = []

        # Define keyword mappings for each agent type
        agent_keywords = {
            AgentType.QA: ["test", "qa", "quality", "bug", "coverage", "requirement", "bdd", "gherkin"],
            AgentType.DEVELOPER: ["code", "implement", "function", "class", "refactor", "generate code"],
            AgentType.DOCUMENTATION: ["document", "readme", "guide", "api doc", "tutorial", "explain"],
            AgentType.SECURITY: ["security", "vulnerability", "owasp", "penetration", "secure"]
        }

        # Determine which agents to use based on keywords
        agents_needed = []
        for agent_type, keywords in agent_keywords.items():
            if any(kw in goal_lower for kw in keywords):
                agents_needed.append(agent_type)

        # Default to QA if no specific match
        if not agents_needed:
            agents_needed = [AgentType.QA]

        # Build tasks based on detected agents
        task_id_counter = 1

        # QA workflow
        if AgentType.QA in agents_needed:
            tasks.extend([
                TaskAssignment(
                    task_id=f"task_{task_id_counter}",
                    agent_type=AgentType.QA,
                    instruction=f"Extract requirements for: {goal}",
                    priority=1
                ),
                TaskAssignment(
                    task_id=f"task_{task_id_counter + 1}",
                    agent_type=AgentType.QA,
                    instruction=f"Generate test cases for: {goal}",
                    priority=2,
                    dependencies=[f"task_{task_id_counter}"]
                )
            ])
            task_id_counter += 2

            # Add BDD if specifically mentioned
            if "bdd" in goal_lower or "gherkin" in goal_lower:
                tasks.append(TaskAssignment(
                    task_id=f"task_{task_id_counter}",
                    agent_type=AgentType.QA,
                    instruction=f"Generate BDD/Gherkin scenarios for: {goal}",
                    priority=3,
                    dependencies=[f"task_{task_id_counter - 1}"]
                ))
                task_id_counter += 1

        # Developer workflow
        if AgentType.DEVELOPER in agents_needed:
            tasks.append(TaskAssignment(
                task_id=f"task_{task_id_counter}",
                agent_type=AgentType.DEVELOPER,
                instruction=f"Generate code for: {goal}",
                priority=2 if tasks else 1
            ))
            task_id_counter += 1

        # Documentation workflow
        if AgentType.DOCUMENTATION in agents_needed:
            deps = [tasks[-1].task_id] if tasks else []
            tasks.append(TaskAssignment(
                task_id=f"task_{task_id_counter}",
                agent_type=AgentType.DOCUMENTATION,
                instruction=f"Create documentation for: {goal}",
                priority=len(tasks) + 1,
                dependencies=deps
            ))
            task_id_counter += 1

        # Security workflow
        if AgentType.SECURITY in agents_needed:
            tasks.append(TaskAssignment(
                task_id=f"task_{task_id_counter}",
                agent_type=AgentType.SECURITY,
                instruction=f"Perform security analysis for: {goal}",
                priority=len(tasks) + 1
            ))
            task_id_counter += 1

        return ExecutionPlan(
            goal=goal,
            tasks=tasks,
            execution_order=[t.task_id for t in tasks],
            estimated_steps=len(tasks)
        )

    def get_recommendations(self, goal: str) -> Dict[str, Any]:
        """
        Get recommendations for a goal based on past executions.

        Args:
            goal: The goal to get recommendations for

        Returns:
            Dict with suggestions from memory
        """
        if not self.memory:
            return {
                "message": "Memory not enabled",
                "suggested_agents": list(self.agents.keys())[:3],
                "tips": ["Enable memory for personalized recommendations"]
            }

        return self.memory.get_recommendations_for_goal(goal)

    def get_similar_executions(self, goal: str, limit: int = 5) -> List[Dict]:
        """
        Find similar past executions.

        Args:
            goal: Goal to find similar executions for
            limit: Maximum results

        Returns:
            List of similar execution records
        """
        if not self.memory:
            return []

        records = self.memory.find_similar_executions(goal, limit)
        return [r.to_dict() for r in records]

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary from memory."""
        if not self.memory:
            return {
                "total_executions": len(self.execution_history),
                "message": "Enable memory for detailed analytics"
            }

        return self.memory.get_performance_summary()

    def execute(
        self,
        goal: str,
        progress_callback: Callable[[str, int], None] = None
    ) -> Dict[str, Any]:
        """
        Execute a goal by planning and delegating to agents.

        Args:
            goal: High-level goal to accomplish
            progress_callback: Optional callback(message, percentage)

        Returns:
            Dict with 'success', 'plan', 'results', 'summary'
        """
        # Create plan
        if progress_callback:
            progress_callback("Planning execution...", 5)

        plan = self.create_plan(goal)

        # Execute tasks in order
        results = {}
        context = {}  # Shared context between tasks
        total_tasks = len(plan.execution_order)

        for i, task_id in enumerate(plan.execution_order):
            task = next((t for t in plan.tasks if t.task_id == task_id), None)
            if not task:
                continue

            # Check dependencies
            deps_met = all(
                results.get(dep, {}).get("success", False)
                for dep in task.dependencies
            )

            if not deps_met:
                results[task_id] = {
                    "success": False,
                    "output": "Dependencies not met",
                    "skipped": True
                }
                continue

            # Progress update
            progress_pct = int(10 + (i / total_tasks) * 80)
            if progress_callback:
                progress_callback(f"Executing: {task.instruction[:50]}...", progress_pct)

            # Get appropriate agent
            agent_name = task.agent_type.value
            agent = self.agents.get(agent_name)

            if not agent:
                results[task_id] = {
                    "success": False,
                    "output": f"No agent registered for: {agent_name}"
                }
                continue

            # Add previous results to context
            context["previous_results"] = results

            # Execute task
            try:
                result = agent.execute(task.instruction, context)
                results[task_id] = result
                task.status = "completed" if result.get("success") else "failed"
                task.result = result.get("output")

                # Update context with result
                context[task_id] = result.get("output")

            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}")
                results[task_id] = {
                    "success": False,
                    "output": str(e),
                    "error": True
                }
                task.status = "failed"

        # Generate summary
        if progress_callback:
            progress_callback("Generating summary...", 95)

        summary = self._generate_summary(goal, plan, results)

        # Calculate duration
        execution_end = datetime.now()
        duration_seconds = (execution_end - plan.created_at).total_seconds()

        # Store in history
        execution_record = {
            "goal": goal,
            "plan": plan,
            "results": results,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        self.execution_history.append(execution_record)

        # Store in persistent memory if available
        result_dict = {
            "success": all(r.get("success", False) for r in results.values()),
            "plan": plan,
            "results": results,
            "summary": summary
        }

        if self.memory:
            try:
                self.memory.record_execution(goal, result_dict, duration_seconds)
            except Exception as e:
                logger.warning(f"Failed to record in memory: {e}")

        if progress_callback:
            progress_callback("Complete", 100)

        return result_dict

    def _generate_summary(
        self,
        goal: str,
        plan: ExecutionPlan,
        results: Dict[str, Any]
    ) -> str:
        """Generate a summary of execution."""
        successful = sum(1 for r in results.values() if r.get("success"))
        total = len(results)

        summary_parts = [
            f"## Execution Summary",
            f"**Goal:** {goal}",
            f"**Tasks Completed:** {successful}/{total}",
            "",
            "### Task Results:"
        ]

        for task_id, result in results.items():
            status = "✅" if result.get("success") else "❌"
            summary_parts.append(f"- {status} {task_id}: {result.get('output', '')[:100]}...")

        if self.llm:
            # Use LLM for better summary
            try:
                from langchain_core.prompts import ChatPromptTemplate
                prompt = ChatPromptTemplate.from_messages([
                    ("system", "Summarize the execution results concisely."),
                    ("human", f"Goal: {goal}\n\nResults:\n{json.dumps(results, default=str)[:2000]}")
                ])
                messages = prompt.format_messages()
                response = self.llm.invoke(messages)
                summary_parts.append("\n### AI Summary:")
                summary_parts.append(response.content)
            except Exception as e:
                logger.debug(f"AI summary generation failed: {e}")

        return "\n".join(summary_parts)

    def get_history(self) -> List[Dict]:
        """Get execution history."""
        return self.execution_history


# ============================================================================
# Factory functions for easy setup
# ============================================================================

def create_manager_with_qa_agent(rag_chain, llm=None) -> ManagerAgent:
    """
    Factory function to create a manager with QA agent pre-configured.

    Args:
        rag_chain: RAGChain instance
        llm: Optional LLM for intelligent planning

    Returns:
        Configured ManagerAgent

    Example:
        from src.rag_chain import RAGChain
        rag_chain = RAGChain()
        manager = create_manager_with_qa_agent(rag_chain, rag_chain.llm)
        result = manager.execute("Create comprehensive tests for login feature")
    """
    qa_agent = QAAgentInterface(rag_chain)
    manager = ManagerAgent(llm=llm)
    manager.register_agent("qa", qa_agent)
    return manager


def create_full_manager(rag_chain, llm=None, enable_memory: bool = True) -> ManagerAgent:
    """
    Factory function to create a manager with ALL agents pre-configured.

    Includes:
    - QA Agent (testing, quality)
    - Dev Agent (code generation)
    - Doc Agent (documentation)
    - Security Agent (security analysis)

    Args:
        rag_chain: RAGChain instance
        llm: Optional LLM for intelligent planning
        enable_memory: Enable persistent memory

    Returns:
        Fully configured ManagerAgent

    Example:
        manager = create_full_manager(rag_chain, rag_chain.llm)
        result = manager.execute("Document the API and create tests for it")
    """
    from src.agent.specialized_agents import (
        DevAgentInterface,
        DocAgentInterface,
        SecurityAgentInterface
    )
    from src.agent.manager_memory import ManagerMemory

    # Create manager with memory
    memory = ManagerMemory() if enable_memory else None
    manager = ManagerAgent(llm=llm, memory=memory)

    # Register all agents
    manager.register_agent("qa", QAAgentInterface(rag_chain))
    manager.register_agent("developer", DevAgentInterface(rag_chain))
    manager.register_agent("documentation", DocAgentInterface(rag_chain))
    manager.register_agent("security", SecurityAgentInterface(rag_chain))

    return manager


def create_manager_with_scheduler(
    rag_chain,
    llm=None,
    auto_start: bool = False
) -> tuple:
    """
    Create a manager with scheduler attached.

    Args:
        rag_chain: RAGChain instance
        llm: Optional LLM
        auto_start: Start scheduler immediately

    Returns:
        Tuple of (ManagerAgent, TaskScheduler)

    Example:
        manager, scheduler = create_manager_with_scheduler(rag_chain)
        scheduler.schedule_recurring("Run QA for auth", schedule_type="daily", time="09:00")
        scheduler.start()
    """
    from src.agent.task_scheduler import TaskScheduler

    manager = create_full_manager(rag_chain, llm, enable_memory=True)
    scheduler = TaskScheduler(manager)

    if auto_start:
        scheduler.start()

    return manager, scheduler


# ============================================================================
# Streamlit Integration Helper
# ============================================================================

def integrate_with_streamlit():
    """
    Example of how to integrate manager agent with Streamlit UI.

    Add this to streamlit_app_agent.py:

    ```python
    from src.agent.manager_agent import create_manager_with_qa_agent

    # In initialization
    if "manager_agent" not in st.session_state:
        st.session_state.manager_agent = create_manager_with_qa_agent(
            rag_chain=st.session_state.rag_chain,
            llm=st.session_state.rag_chain.llm
        )

    # In UI
    with st.expander("🤖 Manager Agent"):
        goal = st.text_area("Enter your goal:",
            placeholder="e.g., Ensure user authentication is fully tested")

        if st.button("Execute"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(msg, pct):
                progress_bar.progress(pct / 100)
                status_text.text(msg)

            result = st.session_state.manager_agent.execute(
                goal,
                progress_callback=update_progress
            )

            st.markdown(result["summary"])
    ```
    """
    pass


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manager Agent CLI")
    parser.add_argument("goal", help="Goal to execute")
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    # This would need actual RAGChain setup
    print(f"Goal: {args.goal}")
    print("Note: Run through Streamlit for full functionality")
    print("\nTo use:")
    print("  1. Start Streamlit: streamlit run src/ui/streamlit_app_agent.py")
    print("  2. Use the Manager Agent section in the UI")
