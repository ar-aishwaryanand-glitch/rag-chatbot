"""Agent executor with Phase 3 enhancements: Memory + Self-Reflection."""

import time
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from .agent_state import AgentState
from .tool_registry import ToolRegistry
from .memory import MemoryManager
from .reflection import ReflectionModule, LearningModule


class AgentExecutorV3:
    """
    Enhanced agent executor with memory and self-reflection (Phase 3).

    New features:
    - Conversation memory (short-term context)
    - Episodic memory (long-term patterns)
    - Self-reflection on actions
    - Learning from mistakes
    - Improved context awareness
    """

    def __init__(
        self,
        llm,
        tool_registry: ToolRegistry,
        config,
        enable_memory: bool = True,
        enable_reflection: bool = True
    ):
        """
        Initialize the enhanced agent executor.

        Args:
            llm: LLM instance
            tool_registry: Registry of available tools
            config: Configuration object
            enable_memory: Enable memory features
            enable_reflection: Enable reflection features
        """
        self.llm = llm
        self.tool_registry = tool_registry
        self.config = config

        # Phase 3 features
        self.enable_memory = enable_memory
        self.enable_reflection = enable_reflection

        if enable_memory:
            self.memory_manager = MemoryManager()
        else:
            self.memory_manager = None

        if enable_reflection:
            self.reflection_module = ReflectionModule(llm=llm)
            self.learning_module = LearningModule()
        else:
            self.reflection_module = None
            self.learning_module = None

        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine with reflection."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("understand", self._understand_query)
        workflow.add_node("route", self._route_to_tool)
        workflow.add_node("execute", self._execute_tool)
        workflow.add_node("synthesize", self._synthesize_answer)

        if self.enable_reflection:
            workflow.add_node("reflect", self._reflect_on_interaction)

        # Define edges
        workflow.set_entry_point("understand")
        workflow.add_edge("understand", "route")
        workflow.add_conditional_edges(
            "route",
            self._should_continue,
            {
                "execute": "execute",
                "finish": "synthesize"
            }
        )
        workflow.add_edge("execute", "synthesize")

        if self.enable_reflection:
            workflow.add_edge("synthesize", "reflect")
            workflow.add_edge("reflect", END)
        else:
            workflow.add_edge("synthesize", END)

        return workflow.compile()

    def _understand_query(self, state: AgentState) -> AgentState:
        """
        Understand the query with memory context.
        """
        state['current_phase'] = 'understanding'

        # Add memory context if available
        if self.enable_memory and self.memory_manager:
            # Add user message to memory
            self.memory_manager.add_user_message(state['query'])

            # Get relevant context
            memory_context = self.memory_manager.get_full_context(
                current_query=state['query'],
                include_episodic=True
            )

            state['memory_context'] = memory_context

        return state

    def _route_to_tool(self, state: AgentState) -> AgentState:
        """
        Route to the appropriate tool with memory-informed decisions.
        """
        state['current_phase'] = 'routing'

        # Get tool descriptions
        tool_descriptions = self.tool_registry.get_tool_descriptions()

        # Build prompt with memory context
        prompt_parts = []

        # Add memory context if available
        if state.get('memory_context'):
            prompt_parts.append(f"Context from previous interactions:\n{state['memory_context']}\n")

        prompt_parts.append(
            f"""You are a tool routing assistant. Given a user query, select the most appropriate tool to use.

Available tools:
{tool_descriptions}

**Tool Selection Guidelines:**
- web_search: Returns quick links and snippets from search engines. Use for finding URLs.
- web_agent: Visits websites, extracts full content, and provides detailed summaries with citations. Use when user wants comprehensive information, detailed content, or research from web sources.
- document_search: Search through uploaded documents in the database.

**Important:** If the user asks for "latest news", "recent information", or wants detailed web research (not just links), use web_agent to visit sites and extract full content.

User query: "{state['query']}"

Respond with ONLY the tool name, nothing else."""
        )

        prompt = "\n".join(prompt_parts)

        try:
            # Get LLM decision
            response = self.llm.invoke([HumanMessage(content=prompt)])
            selected_tool = response.content.strip().lower()

            # Validate tool exists
            if selected_tool not in self.tool_registry:
                selected_tool = self.tool_registry.get_tool_names()[0]

            state['selected_tool'] = selected_tool

        except Exception as e:
            state['last_error'] = f"Tool routing error: {str(e)}"
            state['selected_tool'] = None

        return state

    def _should_continue(self, state: AgentState) -> str:
        """Decide whether to execute tool or finish."""
        if state.get('selected_tool') and state['iteration'] < state['max_iterations']:
            return "execute"
        return "finish"

    def _execute_tool(self, state: AgentState) -> AgentState:
        """Execute the selected tool and track performance."""
        state['current_phase'] = 'executing'
        state['iteration'] = state.get('iteration', 0) + 1

        tool_name = state.get('selected_tool')
        if not tool_name:
            state['last_error'] = "No tool selected"
            return state

        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            state['last_error'] = f"Tool '{tool_name}' not found"
            return state

        try:
            # Execute tool (same logic as original)
            query = state['query']
            start_time = time.time()

            if tool_name == "calculator":
                prompt = f"""Extract ONLY the mathematical expression from this query. Return just the expression, nothing else.

Query: {query}

Expression (numbers and operators only):"""
                response = self.llm.invoke([HumanMessage(content=prompt)])
                expression = response.content.strip()
                result = tool.run(expression=expression)

            elif tool_name == "python_executor":
                prompt = f"""Write Python code to accomplish this task. Return ONLY the code, no explanations.

Task: {query}

Code:"""
                response = self.llm.invoke([HumanMessage(content=prompt)])
                code = response.content.strip().replace("```python", "").replace("```", "").strip()
                result = tool.run(code=code)

            elif tool_name == "file_operations":
                prompt = f"""Extract the file operation details from this query.

Query: {query}

Respond with: operation path
Where operation is one of: read, list, search
And path is the file/directory path (use "." if not specified)

Response:"""
                response = self.llm.invoke([HumanMessage(content=prompt)])
                parts = response.content.strip().split(maxsplit=1)
                operation = parts[0] if parts else "list"
                path = parts[1] if len(parts) > 1 else "."
                result = tool.run(operation=operation, path=path)

            elif tool_name == "document_manager":
                action = "info"
                if "stat" in query.lower():
                    action = "stats"
                elif "list" in query.lower():
                    action = "list"
                result = tool.run(action=action)

            elif tool_name == "web_search":
                result = tool.run(query=query)

            elif tool_name == "web_agent":
                # Extract URLs from query
                import re
                url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
                urls = re.findall(url_pattern, query)

                if urls:
                    if len(urls) == 1:
                        result = tool.run_tool(url=urls[0])
                    else:
                        result = tool.run_tool(urls=urls)
                else:
                    # No URLs found - ask LLM to extract or guide user
                    result = tool.run_tool(url=None)

            else:  # document_search
                result = tool.run(query=query)

            duration = time.time() - start_time

            # Store result
            state['tools_used'].append(tool_name)
            state['tool_results'].append({
                'tool': tool_name,
                'success': result.success,
                'output': result.output,
                'error': result.error,
                'duration': duration
            })

            # Reflect on tool selection if enabled
            if self.enable_reflection and self.reflection_module:
                reflection = self.reflection_module.reflect_on_tool_selection(
                    query=query,
                    selected_tool=tool_name,
                    available_tools=self.tool_registry.get_tool_names(),
                    tool_result={
                        'success': result.success,
                        'error': result.error
                    }
                )
                self.learning_module.learn_from_reflection(reflection)

        except Exception as e:
            state['last_error'] = f"Tool execution error: {str(e)}"
            state['tool_results'].append({
                'tool': tool_name,
                'success': False,
                'output': '',
                'error': str(e),
                'duration': 0
            })

            # Reflect on error if enabled
            if self.enable_reflection and self.reflection_module:
                reflection = self.reflection_module.reflect_on_error(
                    query=state['query'],
                    error=str(e),
                    tool=tool_name
                )
                self.learning_module.learn_from_reflection(reflection)

        return state

    def _synthesize_answer(self, state: AgentState) -> AgentState:
        """Synthesize final answer from tool results."""
        state['current_phase'] = 'synthesizing'

        tool_results = state.get('tool_results', [])

        if not tool_results:
            state['final_answer'] = "I couldn't process your query. Please try again."
            return state

        last_result = tool_results[-1]

        if last_result['success']:
            output = last_result['output']
            if "Answer:" in output:
                answer_part = output.split("Sources:")[0].replace("Answer:", "").strip()
                state['final_answer'] = answer_part
            else:
                state['final_answer'] = output
        else:
            error_msg = last_result.get('error', 'Unknown error')
            state['final_answer'] = f"Error: {error_msg}"

        # Add to memory if enabled
        if self.enable_memory and self.memory_manager:
            tools_used = state.get('tools_used', [])
            self.memory_manager.add_assistant_message(
                content=state['final_answer'],
                tools_used=tools_used
            )

        state['current_phase'] = 'done'
        return state

    def _reflect_on_interaction(self, state: AgentState) -> AgentState:
        """
        Reflect on the entire interaction (Phase 3 feature).
        """
        if not self.enable_reflection:
            return state

        # Reflect on answer quality
        if self.reflection_module:
            reflection = self.reflection_module.reflect_on_answer_quality(
                query=state['query'],
                answer=state['final_answer'],
                sources=None,  # Could extract from tool results
                tools_used=state.get('tools_used', [])
            )
            self.learning_module.learn_from_reflection(reflection)

        return state

    def execute(self, query: str) -> Dict[str, Any]:
        """
        Execute the agent for a given query (synchronous).

        Args:
            query: User question

        Returns:
            Final state dictionary with answer and metadata
        """
        # Initialize state
        initial_state = {
            'messages': [HumanMessage(content=query)],
            'query': query,
            'final_answer': '',
            'current_phase': 'init',
            'iteration': 0,
            'max_iterations': self.config.AGENT_MAX_ITERATIONS,
            'selected_tool': None,
            'tools_used': [],
            'tool_results': [],
            'needs_retry': False,
            'last_error': None,
            'memory_context': None,
            'start_time': time.time(),
            'execution_metadata': {}
        }

        # Execute graph
        final_state = self.graph.invoke(initial_state)

        # Add duration
        final_state['execution_metadata']['total_duration'] = time.time() - final_state['start_time']

        # Add reflection summary if enabled
        if self.enable_reflection and self.learning_module:
            final_state['execution_metadata']['performance'] = self.learning_module.get_overall_performance()

        return final_state

    def end_session(self) -> Dict[str, Any]:
        """
        End the current session and save to episodic memory.

        Returns:
            Session summary
        """
        summary = {}

        if self.enable_memory and self.memory_manager:
            # Get session stats
            session_stats = self.memory_manager.get_session_stats()

            # Generate and save episode
            episode = self.memory_manager.finalize_session()

            summary['session_stats'] = session_stats
            summary['episode_id'] = episode.session_id

        if self.enable_reflection:
            # Generate session reflection
            tools_used = dict(self.learning_module.tool_usage)
            performance = self.learning_module.get_overall_performance()

            if self.reflection_module:
                session_reflection = self.reflection_module.reflect_on_session(
                    total_queries=session_stats.get('turn_count', 0) if self.enable_memory else 0,
                    tools_used=tools_used,
                    success_rate=performance.get('success_rate', 0.0),
                    avg_response_time=0.5  # Placeholder
                )

            summary['performance'] = performance
            summary['learning'] = self.learning_module.get_learning_summary()
            summary['insights'] = self.reflection_module.get_insights_summary() if self.reflection_module else {}

        return summary

    def get_memory_context(self) -> str:
        """Get current memory context."""
        if self.enable_memory and self.memory_manager:
            return self.memory_manager.get_conversation_context()
        return ""

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if self.enable_reflection and self.learning_module:
            return self.learning_module.get_overall_performance()
        return {}
