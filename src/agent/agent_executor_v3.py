"""Agent executor with Phase 3 enhancements: Memory + Self-Reflection."""

# Standard library
import re
import time
from typing import Any, Dict, List, Optional

# Third-party
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

# Local
from src.logging_config import get_logger
from src.observability import get_observability
from .agent_state import AgentState
from .memory import MemoryManager
from .reflection import LearningModule, ReflectionModule
from .tool_registry import ToolRegistry

# Policy Engine imports (optional)
try:
    from src.policy import PolicyAction, PolicyEngine, PolicyEvaluationContext, PolicyViolation
    POLICY_ENGINE_AVAILABLE = True
except ImportError:
    POLICY_ENGINE_AVAILABLE = False

logger = get_logger(__name__)


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
        enable_reflection: bool = True,
        enable_checkpoints: bool = True,
        enable_policy_engine: bool = True
    ):
        """
        Initialize the enhanced agent executor.

        Args:
            llm: LLM instance
            tool_registry: Registry of available tools
            config: Configuration object
            enable_memory: Enable memory features
            enable_reflection: Enable reflection features
            enable_checkpoints: Enable checkpoint storage for crash recovery
            enable_policy_engine: Enable policy engine for behavior control
        """
        self.llm = llm
        self.tool_registry = tool_registry
        self.config = config
        self.observability = get_observability()

        # Phase 3 features
        self.enable_memory = enable_memory
        self.enable_reflection = enable_reflection
        self.enable_checkpoints = enable_checkpoints

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

        # Initialize checkpoint manager
        self.checkpoint_manager = None
        if enable_checkpoints:
            try:
                from src.database import get_checkpoint_manager
                self.checkpoint_manager = get_checkpoint_manager()
                if not self.checkpoint_manager.is_available():
                    self.checkpoint_manager = None
            except (ImportError, OSError) as e:
                logger.warning(f"Checkpointing disabled: {e}")
                self.checkpoint_manager = None

        # Initialize policy engine
        self.policy_engine = None
        if enable_policy_engine and POLICY_ENGINE_AVAILABLE:
            try:
                self.policy_engine = PolicyEngine()
                if not self.policy_engine.is_enabled():
                    self.policy_engine = None
            except (ImportError, OSError) as e:
                logger.warning(f"Policy engine disabled: {e}")
                self.policy_engine = None

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

        # Compile with checkpoint saver if available
        if self.checkpoint_manager and self.checkpoint_manager.is_available():
            checkpointer = self.checkpoint_manager.get_checkpointer()
            logger.info("LangGraph compiled with checkpoint storage")
            return workflow.compile(checkpointer=checkpointer)
        else:
            return workflow.compile()

    def _understand_query(self, state: AgentState) -> AgentState:
        """
        Understand the query with memory context.
        """
        state['current_phase'] = 'understanding'

        # Add memory context if available
        if self.enable_memory and self.memory_manager:
            # Restore conversation messages from state if available (checkpoint resume)
            if state.get('conversation_messages'):
                try:
                    # Convert serialized messages back to conversation memory
                    conversation_dict = {
                        'session_id': self.memory_manager.session_id,
                        'session_start': self.memory_manager.conversation_memory.session_start.isoformat(),
                        'turn_count': len([m for m in state['conversation_messages'] if m['role'] == 'user']),
                        'messages': state['conversation_messages'],
                        'summary': None,
                        'stats': self.memory_manager.conversation_memory.stats
                    }
                    from .memory.conversation_memory import ConversationMemory
                    self.memory_manager.conversation_memory = ConversationMemory.from_dict(conversation_dict)
                    logger.info(f"Restored {len(state['conversation_messages'])} messages from checkpoint")
                except Exception as e:
                    logger.warning(f"Failed to restore conversation history: {e}")

            # Add user message to memory
            self.memory_manager.add_user_message(state['query'])

            # Get relevant context
            memory_context = self.memory_manager.get_full_context(
                current_query=state['query'],
                include_episodic=True
            )

            state['memory_context'] = memory_context

            # Store conversation messages in state for checkpoint persistence
            state['conversation_messages'] = [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'metadata': msg.metadata
                }
                for msg in self.memory_manager.conversation_memory.messages
            ]

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
            f"""You are a tool routing assistant. Given a user query, select the most appropriate tool to use OR respond with "none" if you can answer from memory.

Available tools:
{tool_descriptions}

**Tool Selection Guidelines:**
- web_search: Returns quick links and snippets from search engines. Use for finding URLs or quick facts from the internet.
- web_agent: Visits websites, extracts full content, and provides detailed summaries with citations. Use when user wants comprehensive information, detailed content, or research from web sources.
- document_search: Search through uploaded documents in the database. Use for questions about documents, PDFs, or technical content in the knowledge base.
- calculator: Perform mathematical calculations and evaluations.
- file_ops: Read, list, or search files in the workspace.
- none: Use when answering questions about THIS CONVERSATION, previous messages, what was discussed earlier, or anything about the current chat session. Memory context is available for these queries.

**Important Rules:**
1. If user asks about "our conversation", "what we discussed", "earlier", "previous messages", or "this chat" → use "none" (answer from memory)
2. If user wants latest news, recent information, or detailed web research → use "web_agent" to visit sites
3. If user wants to search uploaded documents or knowledge base → use "document_search"
4. If user wants quick web facts or URLs → use "web_search"
5. If user wants calculations → use "calculator"

User query: "{state['query']}"

Respond with ONLY the tool name or "none", nothing else."""
        )

        prompt = "\n".join(prompt_parts)

        try:
            # Get LLM decision
            response = self.llm.invoke([HumanMessage(content=prompt)])
            selected_tool = response.content.strip().lower()

            # Handle "none" - answer from memory without tools
            if selected_tool == "none":
                state['selected_tool'] = None
                state['answer_from_memory'] = True
            # Validate tool exists
            elif selected_tool not in self.tool_registry:
                selected_tool = self.tool_registry.get_tool_names()[0]
                state['selected_tool'] = selected_tool
            else:
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

        # Policy enforcement: Check if tool usage is allowed
        if self.policy_engine:
            try:
                session_id = state.get('execution_metadata', {}).get('session_id', 'default')
                context = PolicyEvaluationContext(
                    session_id=session_id,
                    tool_name=tool_name,
                    input_content=state['query']
                )

                # Evaluate tool usage policy
                decision = self.policy_engine.evaluate_tool_usage(context)

                if not decision.allowed:
                    state['last_error'] = decision.message or f"Tool '{tool_name}' is blocked by policy"
                    state['policy_violation'] = True
                    logger.warning(f"Policy violation: {state['last_error']}")
                    return state

                if decision.warnings:
                    logger.warning(f"Policy warnings: {', '.join(decision.warnings)}")

                if decision.action == PolicyAction.REQUIRE_APPROVAL:
                    state['last_error'] = f"Tool '{tool_name}' requires manual approval"
                    state['requires_approval'] = True
                    return state

            except Exception as e:
                logger.warning(f"Policy check failed: {e}")
                # Continue execution if policy check fails (fail-open for availability)

        try:
            # Execute tool with observability
            query = state['query']
            start_time = time.time()

            with self.observability.trace_operation(
                "agent_tool_execution",
                attributes={
                    "tool_name": tool_name,
                    "query": query[:100],
                    "iteration": state['iteration']
                }
            ) as _:  # span intentionally unused
                if tool_name == "calculator":
                    prompt = f"""Convert this query into a Python mathematical expression. Use Python syntax:
- For square root: sqrt(x)
- For power: x**y
- Operators: +, -, *, /, **
- Functions: sqrt, sin, cos, tan, log, exp, abs

CRITICAL: Return ONLY the mathematical expression. No explanations, no text, no context.
If you cannot create an expression, return "ERROR: cannot calculate"

Query: {query}

Expression:"""
                    response = self.llm.invoke([HumanMessage(content=prompt)])
                    raw_response = response.content.strip()

                    # Extract only the mathematical expression
                    # Remove common prefixes and explanatory text
                    expression = raw_response

                    # Remove "Expression" prefix if present
                    if expression.lower().startswith("expression"):
                        expression = expression.split(":", 1)[-1].strip()

                    # Extract the last line if multi-line (often the expression is on the last line)
                    if "\n" in expression:
                        lines = [line.strip() for line in expression.split("\n") if line.strip()]
                        # Find the line that looks most like a math expression (contains operators)
                        math_line = None
                        for line in reversed(lines):
                            if any(op in line for op in ['+', '-', '*', '/', '(', ')', '**', 'sqrt', 'sin', 'cos']):
                                math_line = line
                                break
                        if math_line:
                            expression = math_line
                        else:
                            expression = lines[-1] if lines else expression

                    # Remove markdown code blocks if present
                    expression = expression.replace("```python", "").replace("```", "").strip()

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

                    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
                    urls = re.findall(url_pattern, query)

                    if urls:
                        # URLs provided directly in query
                        if len(urls) == 1:
                            result = tool.run_tool(url=urls[0])
                        else:
                            result = tool.run_tool(urls=urls)
                    else:
                        # No URLs found - perform web search first to get URLs
                        search_tool = self.tool_registry.get_tool("web_search")
                        if search_tool:
                            # Search for URLs
                            search_result = search_tool.run(query=query)

                            if search_result.success:
                                # Extract URLs from search results
                                search_urls = re.findall(url_pattern, search_result.output)

                                if search_urls:
                                    # Limit to top 3 URLs
                                    search_urls = search_urls[:3]
                                    result = tool.run_tool(urls=search_urls)
                                else:
                                    # No URLs found in search results
                                    result = search_result  # Return search results as fallback
                            else:
                                result = search_result  # Return search error
                        else:
                            # web_search not available
                            from .base_tool import ToolResult
                            result = ToolResult(
                                success=False,
                                output="",
                                error="web_agent requires URLs. Please provide URLs or enable web_search tool.",
                                duration=0
                        )

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

            # Record metrics
            self.observability.record_metric(
                "agent_action",
                duration * 1000,  # Convert to ms
                {
                    "tool_name": tool_name,
                    "success": result.success,
                    "iteration": state['iteration']
                }
            )

            # Record tool execution in policy engine for tracking
            if self.policy_engine:
                try:
                    session_id = state.get('execution_metadata', {}).get('session_id', 'default')
                    self.policy_engine.record_tool_execution(session_id, tool_name)
                except Exception as e:
                    logger.warning(f"Failed to record tool execution: {e}")

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
            # Record error metric
            self.observability.record_metric(
                "error",
                0,
                {
                    "operation": "agent_tool_execution",
                    "tool_name": tool_name,
                    "error": str(e)[:100]
                }
            )

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
        """Synthesize final answer from tool results or memory."""
        state['current_phase'] = 'synthesizing'

        tool_results = state.get('tool_results', [])

        # Handle queries answered from memory without tools
        if not tool_results and state.get('answer_from_memory'):
            memory_context = state.get('memory_context', '')
            query = state['query']

            if memory_context:
                # Use LLM to generate answer from memory context
                synthesis_prompt = f"""Based on the conversation history below, answer the user's question naturally.

Conversation History:
{memory_context}

User Question: {query}

Provide a natural, conversational response based on the conversation history. If the history doesn't contain relevant information, say so."""

                try:
                    response = self.llm.invoke([HumanMessage(content=synthesis_prompt)])
                    state['final_answer'] = response.content.strip()
                except Exception as e:
                    state['final_answer'] = f"I have conversation history but encountered an error: {str(e)}"
            else:
                state['final_answer'] = "I don't have enough conversation history to answer that question yet. We just started chatting!"

            # Add to memory
            if self.enable_memory and self.memory_manager:
                self.memory_manager.add_assistant_message(
                    content=state['final_answer'],
                    tools_used=[]
                )

                # Update conversation messages in state
                state['conversation_messages'] = [
                    {
                        'role': msg.role,
                        'content': msg.content,
                        'timestamp': msg.timestamp.isoformat(),
                        'metadata': msg.metadata
                    }
                    for msg in self.memory_manager.conversation_memory.messages
                ]

            state['current_phase'] = 'done'
            return state

        if not tool_results:
            state['final_answer'] = "I couldn't process your query. Please try again."
            return state

        last_result = tool_results[-1]
        tool_name = last_result.get('tool', '')

        logger.debug(f"[SYNTH] tool_name={tool_name}, success={last_result.get('success')}, output_len={len(str(last_result.get('output','')))}")

        if last_result['success']:
            output = last_result['output']

            # For web search, web agent, and news, ALWAYS use LLM to synthesize detailed natural language response
            if tool_name in ['web_search', 'web_agent', 'news_api'] and output and len(output) > 30:
                logger.debug(f"[SYNTH] Entering synthesis block for {tool_name}")
                try:


                    # Extract sources for later
                    sources_line = ""
                    if 'Sources:' in output:
                        parts = output.rsplit('Sources:', 1)
                        content = parts[0].strip()
                        sources_line = f"\n\nSources: {parts[1].strip()}"
                    else:
                        content = output

                    # Aggressively clean search result artifacts
                    content = re.sub(r'\d+\s+(second|minute|hour|day|week|month|year)s?\s+ago\s*[·\-—–]\s*', '', content)
                    content = re.sub(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s*\d{4}\s*[·\-—–]\s*', '', content)
                    content = re.sub(r'Missing:\s*[^|]+\|\s*Show results with:[^\n]+', '', content)
                    content = re.sub(r'More results from\s+\S+', '', content)
                    content = re.sub(r'www\.\w+\.com', '', content)
                    content = re.sub(r'https?://\S+', '', content)
                    content = re.sub(r'\.\.\.\s*', '. ', content)
                    content = re.sub(r'\s+', ' ', content).strip()

                    synthesis_prompt = f"""The user asked: "{state['query']}"

Here is raw information I gathered from the web:

{content[:2000]}

Write a clear, well-structured answer in 3 short paragraphs separated by blank lines.

Paragraph 1: The most important headline or development.
Paragraph 2: Supporting details and context.
Paragraph 3: Why it matters or what's next.

Rules:
- Each paragraph should be 2-3 sentences MAX. Keep it concise.
- Separate paragraphs with a blank line.
- No bullet points, no lists, no markdown, no bold, no headers.
- No URLs or website names.
- Write naturally like a news briefing to a colleague."""

                    response = self.llm.invoke([HumanMessage(content=synthesis_prompt)])
                    synthesized = response.content.strip()

                    # Clean up any markdown artifacts
                    synthesized = re.sub(r'[*#]+', '', synthesized)
                    synthesized = re.sub(r'https?://\S+', '', synthesized)
                    synthesized = re.sub(r'www\.\S+', '', synthesized)
                    # Collapse triple+ newlines to double
                    synthesized = re.sub(r'\n{3,}', '\n\n', synthesized).strip()

                    state['final_answer'] = synthesized + sources_line
                    logger.info(f"Synthesis complete ({len(synthesized)} chars)")

                except Exception as e:
                    logger.error(f"[SYNTH] SYNTHESIS FAILED: {e}", exc_info=True)
                    # Even on error, try to clean up the output

                    cleaned = re.sub(r'Missing:\s*[^|]+\|\s*Show results with:[^\n]+', '', output)
                    cleaned = re.sub(r'\d+\s+(second|minute|hour|day|week|month|year)s?\s+ago\s*[·\-—–]\s*', '', cleaned)
                    cleaned = re.sub(r'More results from\s+\S+', '', cleaned)
                    state['final_answer'] = cleaned.replace('**', '').strip()

            elif "Answer:" in output:
                # Remove "Answer:" label but keep everything else including sources
                final_output = output.replace("Answer:", "").strip()
                state['final_answer'] = final_output
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

            # Update conversation messages in state for checkpoint persistence
            state['conversation_messages'] = [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'metadata': msg.metadata
                }
                for msg in self.memory_manager.conversation_memory.messages
            ]

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

    def execute(self, query: str, thread_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """
        Execute the agent for a given query (synchronous).

        Args:
            query: User question
            thread_id: Optional thread ID for checkpoint storage (enables crash recovery)
            session_id: Optional session ID for policy tracking

        Returns:
            Final state dictionary with answer and metadata
        """
        # Policy enforcement: Check rate limits and content policies
        if self.policy_engine:
            try:
                context = PolicyEvaluationContext(
                    session_id=session_id or thread_id or 'default',
                    input_content=query,
                    token_count=len(query.split())  # Rough estimate
                )

                # Evaluate all policies (rate limit, content, etc.)
                decision = self.policy_engine.evaluate_all(context)

                if not decision.allowed:
                    # Policy violation - return error
                    return {
                        'query': query,
                        'final_answer': decision.message or 'Request blocked by policy',
                        'current_phase': 'policy_violation',
                        'policy_violation': True,
                        'violated_rules': [r.name for r in decision.violated_rules],
                        'execution_metadata': {'duration': 0}
                    }

                if decision.warnings:
                    logger.warning(f"Policy warnings: {', '.join(decision.warnings)}")

            except Exception as e:
                logger.warning(f"Policy evaluation failed: {e}")
                # Continue execution if policy check fails (fail-open)

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
            'conversation_messages': None,  # Will be populated from checkpoint or created fresh
            'start_time': time.time(),
            'execution_metadata': {'session_id': session_id or thread_id or 'default'}
        }

        # Prepare config for checkpointing
        config = {}
        if thread_id and self.checkpoint_manager and self.checkpoint_manager.is_available():
            config = {"configurable": {"thread_id": thread_id}}
            logger.info(f"Checkpointing enabled for thread: {thread_id}")

        # Execute graph with optional checkpointing
        if config:
            final_state = self.graph.invoke(initial_state, config=config)
        else:
            final_state = self.graph.invoke(initial_state)

        # Add duration
        final_state['execution_metadata']['total_duration'] = time.time() - final_state['start_time']

        # Add reflection summary if enabled
        if self.enable_reflection and self.learning_module:
            final_state['execution_metadata']['performance'] = self.learning_module.get_overall_performance()

        return final_state

    def resume_from_checkpoint(self, thread_id: str, query: str = None) -> Dict[str, Any]:
        """
        Resume execution from the last checkpoint.

        Args:
            thread_id: Thread ID to resume from
            query: Optional new query to continue with

        Returns:
            Final state dictionary with answer and metadata
        """
        if not self.checkpoint_manager or not self.checkpoint_manager.is_available():
            raise ValueError("Checkpoint storage not available. Enable USE_POSTGRES=true and USE_CHECKPOINTS=true")

        # Get the last checkpoint for this thread
        checkpoint = self.checkpoint_manager.get_checkpoint(thread_id)

        if not checkpoint:
            raise ValueError(f"No checkpoint found for thread: {thread_id}")

        logger.info(f"Resuming from checkpoint for thread: {thread_id}")

        # Prepare config
        config = {"configurable": {"thread_id": thread_id}}

        # Resume with optional new input
        if query:
            # Create new state with updated query
            resume_state = checkpoint['state'].copy()
            resume_state['query'] = query
            resume_state['messages'].append(HumanMessage(content=query))
            final_state = self.graph.invoke(resume_state, config=config)
        else:
            # Resume from last state
            final_state = self.graph.invoke(checkpoint['state'], config=config)

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
                # Call reflect_on_session for side effects (updates internal state)
                self.reflection_module.reflect_on_session(
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

    def get_policy_violations(self, session_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get policy violations for a session.

        Args:
            session_id: Optional session ID to filter by
            limit: Maximum number of violations to return

        Returns:
            List of violation records
        """
        if not self.policy_engine:
            return []

        try:
            violations = self.policy_engine.get_violations(session_id=session_id, limit=limit)
            return [
                {
                    'violation_id': v.violation_id,
                    'rule_id': v.rule_id,
                    'policy_type': v.policy_type.value,
                    'action_taken': v.action_taken.value,
                    'details': v.violation_details,
                    'timestamp': v.timestamp.isoformat()
                }
                for v in violations
            ]
        except Exception as e:
            logger.warning(f"Failed to get policy violations: {e}")
            return []

    def get_active_policies(self, policy_type: str = None) -> List[Dict[str, Any]]:
        """
        Get active policies.

        Args:
            policy_type: Optional policy type filter

        Returns:
            List of active policies
        """
        if not self.policy_engine:
            return []

        try:
            from src.policy import PolicyType
            ptype = PolicyType(policy_type) if policy_type else None
            policies = self.policy_engine.list_policies(policy_type=ptype)
            return [
                {
                    'rule_id': p.rule_id,
                    'name': p.name,
                    'description': p.description,
                    'policy_type': p.policy_type.value,
                    'action': p.action.value,
                    'enabled': p.enabled,
                    'priority': p.priority
                }
                for p in policies
            ]
        except Exception as e:
            logger.warning(f"Failed to get policies: {e}")
            return []

    # =========================================================================
    # ASYNC EXECUTION (Message Queue Integration)
    # =========================================================================

    def execute_async(
        self,
        query: str,
        session_id: str = None,
        thread_id: str = None,
        priority: str = "normal"
    ) -> str:
        """
        Execute agent query asynchronously using message queue.

        Args:
            query: User question
            session_id: Optional session ID
            thread_id: Optional thread ID for checkpointing
            priority: Task priority (low, normal, high, urgent)

        Returns:
            Task ID for tracking
        """
        try:
            from src.task_queue import get_task_queue, AgentTask, TaskPriority, TaskType

            task_queue = get_task_queue()

            if not task_queue.is_available():
                raise RuntimeError("Task queue not available. Enable USE_REDIS_QUEUE=true")

            # Map priority string to enum
            priority_map = {
                'low': TaskPriority.LOW,
                'normal': TaskPriority.NORMAL,
                'high': TaskPriority.HIGH,
                'urgent': TaskPriority.URGENT
            }

            task_priority = priority_map.get(priority.lower(), TaskPriority.NORMAL)

            # Create agent task
            task = AgentTask(
                task_type=TaskType.AGENT_QUERY,
                payload={
                    'query': query,
                    'thread_id': thread_id
                },
                priority=task_priority,
                session_id=session_id,
                metadata={
                    'source': 'agent_executor',
                    'async': True
                }
            )

            # Submit to queue
            task_id = task_queue.submit_task(task)

            logger.info(f"Task submitted: {task_id} ({priority} priority)")

            return task_id

        except Exception as e:
            logger.error(f"Failed to submit async task: {e}")
            raise

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of an async task.

        Args:
            task_id: Task ID from execute_async

        Returns:
            Task status dictionary or None
        """
        try:
            from src.task_queue import get_task_queue

            task_queue = get_task_queue()

            if not task_queue.is_available():
                return None

            task = task_queue.get_task(task_id)

            if task:
                return {
                    'task_id': task.task_id,
                    'status': task.status.value,
                    'created_at': task.created_at.isoformat(),
                    'started_at': task.started_at.isoformat() if task.started_at else None,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                    'worker_id': task.worker_id,
                    'error': task.error
                }

            return None

        except Exception as e:
            logger.warning(f"Failed to get task status: {e}")
            return None

    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get result of a completed async task.

        Args:
            task_id: Task ID from execute_async

        Returns:
            Task result dictionary or None
        """
        try:
            from src.task_queue import get_task_queue

            task_queue = get_task_queue()

            if not task_queue.is_available():
                return None

            result = task_queue.get_result(task_id)

            if result:
                return {
                    'task_id': result.task_id,
                    'status': result.status.value,
                    'result': result.result,
                    'error': result.error,
                    'duration': result.duration,
                    'completed_at': result.completed_at.isoformat()
                }

            return None

        except Exception as e:
            logger.warning(f"Failed to get task result: {e}")
            return None

    def cancel_task(self, task_id: str):
        """
        Cancel a pending async task.

        Args:
            task_id: Task ID to cancel
        """
        try:
            from src.task_queue import get_task_queue

            task_queue = get_task_queue()

            if task_queue.is_available():
                task_queue.cancel_task(task_id)

        except Exception as e:
            logger.warning(f"Failed to cancel task: {e}")
