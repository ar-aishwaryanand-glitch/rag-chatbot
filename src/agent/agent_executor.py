"""Agent executor using LangGraph for agentic RAG system."""

import time
from typing import Dict, Any, AsyncGenerator
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from .agent_state import AgentState
from .tool_registry import ToolRegistry


class AgentExecutor:
    """
    Main agent executor using LangGraph state machine.

    Implements a simple workflow: understand → route → execute → synthesize
    """

    def __init__(self, llm, tool_registry: ToolRegistry, config):
        """
        Initialize the agent executor.

        Args:
            llm: LLM instance (Groq ChatGroq)
            tool_registry: Registry of available tools
            config: Configuration object
        """
        self.llm = llm
        self.tool_registry = tool_registry
        self.config = config
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("understand", self._understand_query)
        workflow.add_node("route", self._route_to_tool)
        workflow.add_node("execute", self._execute_tool)
        workflow.add_node("synthesize", self._synthesize_answer)

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
        workflow.add_edge("synthesize", END)

        return workflow.compile()

    def _understand_query(self, state: AgentState) -> AgentState:
        """
        Understand the query and prepare context.

        In Phase 1, this is simple - just sets the phase.
        In later phases, will add intent classification, entity extraction, etc.
        """
        state['current_phase'] = 'understanding'
        return state

    def _route_to_tool(self, state: AgentState) -> AgentState:
        """
        Route to the appropriate tool based on query.

        Uses LLM to select which tool to use.
        """
        state['current_phase'] = 'routing'

        # Get tool descriptions
        tool_descriptions = self.tool_registry.get_tool_descriptions()

        # Create routing prompt
        prompt = f"""You are a tool routing assistant. Given a user query, select the most appropriate tool to use.

Available tools:
{tool_descriptions}

User query: "{state['query']}"

Respond with ONLY the tool name, nothing else."""

        try:
            # Get LLM decision
            response = self.llm.invoke([HumanMessage(content=prompt)])
            selected_tool = response.content.strip().lower()

            # Validate tool exists
            if selected_tool not in self.tool_registry:
                # Default to first available tool (RAG in Phase 1)
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
        """Execute the selected tool."""
        state['current_phase'] = 'executing'
        state['iteration'] = state.get('iteration', 0) + 1

        tool_name = state.get('selected_tool')
        if not tool_name:
            state['last_error'] = "No tool selected"
            return state

        # Get tool
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            state['last_error'] = f"Tool '{tool_name}' not found"
            return state

        try:
            # Execute tool with appropriate parameter
            # Extract tool-specific input from query using LLM
            query = state['query']

            if tool_name == "calculator":
                # Extract math expression from query
                prompt = f"""Extract ONLY the mathematical expression from this query. Return just the expression, nothing else.

Query: {query}

Expression (numbers and operators only):"""
                response = self.llm.invoke([HumanMessage(content=prompt)])
                expression = response.content.strip()
                result = tool.run(expression=expression)

            elif tool_name == "python_executor":
                # Generate Python code for the task
                prompt = f"""Write Python code to accomplish this task. Return ONLY the code, no explanations.

Task: {query}

Code:"""
                response = self.llm.invoke([HumanMessage(content=prompt)])
                code = response.content.strip().replace("```python", "").replace("```", "").strip()
                result = tool.run(code=code)

            elif tool_name == "file_operations":
                # Extract operation and path
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
                # Determine action
                action = "info"
                if "stat" in query.lower():
                    action = "stats"
                elif "list" in query.lower():
                    action = "list"
                result = tool.run(action=action)

            elif tool_name == "web_search":
                result = tool.run(query=query)

            else:  # document_search
                result = tool.run(query=query)

            # Store result
            state['tools_used'].append(tool_name)
            state['tool_results'].append({
                'tool': tool_name,
                'success': result.success,
                'output': result.output,
                'error': result.error,
                'duration': result.duration
            })

        except Exception as e:
            state['last_error'] = f"Tool execution error: {str(e)}"
            state['tool_results'].append({
                'tool': tool_name,
                'success': False,
                'output': '',
                'error': str(e),
                'duration': 0
            })

        return state

    def _synthesize_answer(self, state: AgentState) -> AgentState:
        """Synthesize final answer from tool results."""
        state['current_phase'] = 'synthesizing'

        # Get tool results
        tool_results = state.get('tool_results', [])

        if not tool_results:
            state['final_answer'] = "I couldn't process your query. Please try again."
            return state

        # For Phase 1 with single tool, just use the output directly
        last_result = tool_results[-1]

        if last_result['success']:
            # Extract just the answer part (before "Sources:")
            output = last_result['output']
            if "Answer:" in output:
                answer_part = output.split("Sources:")[0].replace("Answer:", "").strip()
                state['final_answer'] = answer_part
            else:
                state['final_answer'] = output
        else:
            error_msg = last_result.get('error', 'Unknown error')
            state['final_answer'] = f"Error: {error_msg}"

        state['current_phase'] = 'done'
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

        return final_state

    async def execute_stream(self, query: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute the agent with streaming (for future UI updates).

        Args:
            query: User question

        Yields:
            State updates as they occur
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

        # Stream execution
        async for state in self.graph.astream(initial_state):
            yield state
