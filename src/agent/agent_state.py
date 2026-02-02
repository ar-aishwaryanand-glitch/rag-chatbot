"""State definition for the agent using LangGraph."""

from typing import TypedDict, Annotated, Sequence, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    """
    State for the agent workflow.

    This defines all the data that flows through the agent's execution graph.
    """
    # Core
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    final_answer: str

    # Agent execution
    current_phase: str  # 'init', 'understanding', 'routing', 'executing', 'reflecting', 'synthesizing', 'done'
    iteration: int
    max_iterations: int

    # Tool execution
    selected_tool: Optional[str]
    tools_used: List[str]
    tool_results: List[Dict[str, Any]]

    # Reflection & retry
    needs_retry: bool
    last_error: Optional[str]

    # Memory context
    memory_context: Optional[str]

    # Metadata
    start_time: Optional[float]
    execution_metadata: Dict[str, Any]
