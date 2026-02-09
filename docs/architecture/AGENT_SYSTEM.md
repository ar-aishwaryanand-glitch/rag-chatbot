# Agent System Documentation

## Overview

The agent system is the core intelligent component that orchestrates tool usage, manages conversation flow, and generates answers. It's built using **LangGraph**, a framework for creating stateful, multi-step LLM applications.

## Architecture

### Component Hierarchy

```
AgentExecutorV3 (State Machine)
├── Agent State (Current execution state)
├── Tool Registry (Available tools)
├── Memory Manager (Conversation context)
├── Reflection Module (Self-evaluation)
└── Checkpoint Backend (Persistence)
```

## AgentExecutorV3

**File**: [src/agent/agent_executor_v3.py](../src/agent/agent_executor_v3.py)

The main agent execution engine that processes queries through multiple phases using a LangGraph state machine.

### Execution Phases

#### Phase 1: Understanding (`_understand_query`)
**Purpose**: Analyze the user's query with full conversation context.

```python
def _understand_query(self, state: AgentState) -> AgentState:
    """
    Understand the query with memory context.

    Steps:
    1. Restore conversation messages from checkpoint (if resuming)
    2. Add user message to memory
    3. Get memory context (recent + episodic)
    4. Save conversation_messages to state
    """
```

**Key Operations**:
- Restore previous conversation from `state['conversation_messages']`
- Add new user message to `MemoryManager`
- Retrieve memory context for LLM prompt
- Serialize and save updated messages back to state

**Memory Context Format**:
```
[Recent conversation]
User: Previous question...
Assistant: Previous answer...
User: Current question...

[Patterns from past interactions]
- User often asks about machine learning
- Prefers detailed technical explanations
```

#### Phase 2: Tool Routing (`_route_to_tool`)
**Purpose**: Select and execute the most appropriate tool.

```python
def _route_to_tool(self, state: AgentState) -> AgentState:
    """
    Route to the appropriate tool with memory-informed decisions.

    Steps:
    1. Get all available tools from registry
    2. Create routing prompt with tool descriptions
    3. LLM selects tool and parameters
    4. Execute selected tool
    5. Store results in state
    """
```

**Routing Prompt**:
```
Available Tools:
- document_search: Search through indexed documents
- web_search: Search the internet for current info
- calculator: Perform mathematical calculations
- ...

Query: [user's question]
Memory Context: [conversation history]

Which tool should be used? Return JSON:
{
  "tool": "tool_name",
  "parameters": {...},
  "reasoning": "why this tool"
}
```

**Tool Execution**:
```python
tool = self.tool_registry.get_tool(tool_name)
result = tool.execute(**parameters)

state['tool_results'].append({
    'tool': tool_name,
    'result': result,
    'timestamp': time.time()
})
```

#### Phase 3: Answer Synthesis (`_synthesize_answer`)
**Purpose**: Generate final answer from tool results.

```python
def _synthesize_answer(self, state: AgentState) -> AgentState:
    """
    Synthesize final answer from tool results.

    Steps:
    1. Format tool results
    2. Create synthesis prompt with context
    3. LLM generates answer
    4. Add assistant message to memory
    5. Save conversation_messages to state
    """
```

**Synthesis Prompt**:
```
Query: [user's question]
Memory Context: [conversation history]

Tool Results:
- [tool_1]: [result_1]
- [tool_2]: [result_2]

Generate a comprehensive answer that:
- Answers the user's question directly
- References sources appropriately
- Maintains conversation continuity
```

#### Phase 4: Reflection (`_reflect_on_interaction`)
**Purpose**: Self-evaluate and learn from the interaction (optional).

```python
def _reflect_on_interaction(self, state: AgentState) -> AgentState:
    """
    Reflect on the entire interaction.

    Steps:
    1. Evaluate answer quality
    2. Check for hallucinations
    3. Identify improvement opportunities
    4. Store learnings in episodic memory
    """
```

### State Machine Graph

```
START
  ↓
understanding
  ↓
routing ←─────┐ (retry if needed)
  ↓           │
execute_tool  │
  ↓           │
check_retry ──┘
  ↓
synthesize
  ↓
reflection (optional)
  ↓
END
```

**Graph Definition**:
```python
workflow = StateGraph(AgentState)

# Add nodes for each phase
workflow.add_node("understanding", self._understand_query)
workflow.add_node("routing", self._route_to_tool)
workflow.add_node("synthesize", self._synthesize_answer)
workflow.add_node("reflection", self._reflect_on_interaction)

# Define edges
workflow.set_entry_point("understanding")
workflow.add_edge("understanding", "routing")
workflow.add_conditional_edges(
    "routing",
    lambda s: "synthesize" if not s['needs_retry'] else "routing"
)
workflow.add_edge("synthesize", "reflection" if enable_reflection else END)
workflow.add_edge("reflection", END)
```

## Agent State

**File**: [src/agent/agent_state.py](../src/agent/agent_state.py)

The state that flows through the agent execution graph. All data persists in checkpoints.

```python
class AgentState(TypedDict):
    # Core query data
    messages: List[BaseMessage]      # LangChain messages
    query: str                        # Original user query
    final_answer: Optional[str]       # Generated answer

    # Execution state
    current_phase: str                # "understanding", "routing", etc.
    iteration: int                    # Current iteration (for retries)
    max_iterations: int               # Max allowed iterations

    # Tool state
    selected_tool: Optional[str]      # Currently selected tool
    tools_used: List[str]             # History of tools used
    tool_results: List[Dict]          # Results from tool executions

    # Retry & error handling
    needs_retry: bool                 # Should we retry with different tool?
    last_error: Optional[str]         # Last error message

    # Memory state
    memory_context: Optional[str]     # Formatted memory context for LLM
    conversation_messages: Optional[List[Dict]]  # Serialized conversation

    # Metadata
    start_time: Optional[float]       # Execution start timestamp
    execution_metadata: Dict          # Session ID, etc.
```

### State Flow Example

```python
# Initial state
{
    'query': "What did we discuss about ML?",
    'messages': [...],
    'iteration': 0,
    'conversation_messages': None  # Will be populated from checkpoint
}

# After understanding phase
{
    'query': "What did we discuss about ML?",
    'current_phase': 'understanding',
    'memory_context': "[Recent conversation]\nUser: I like ML...",
    'conversation_messages': [
        {'role': 'user', 'content': 'I like ML', ...},
        {'role': 'assistant', 'content': 'Great!', ...},
        {'role': 'user', 'content': 'What did we discuss about ML?', ...}
    ]
}

# After routing phase
{
    'selected_tool': 'document_search',
    'tool_results': [
        {'tool': 'document_search', 'result': {...}, ...}
    ]
}

# After synthesis phase
{
    'final_answer': "We discussed machine learning topics including...",
    'conversation_messages': [
        # ... previous messages ...
        {'role': 'assistant', 'content': 'We discussed...', ...}
    ]
}
```

## Tool Registry

**File**: [src/agent/tool_registry.py](../src/agent/tool_registry.py)

Manages all tools available to the agent.

### Usage

```python
# Create registry
registry = ToolRegistry()

# Register tools
registry.register(RAGTool(rag_chain))
registry.register(CalculatorTool())
registry.register(WebSearchTool())

# Get tool
tool = registry.get_tool("calculator")
result = tool.execute(expression="2 + 2")

# Get all tools for LLM prompt
descriptions = registry.get_tool_descriptions()
# Output:
# - document_search: Search through indexed documents
# - calculator: Perform mathematical calculations
# - web_search: Search the internet for information
```

### Tool Interface

All tools must extend `BaseTool`:

```python
class BaseTool:
    name: str                    # Unique tool identifier
    description: str             # What the tool does (for LLM)
    parameters: Dict[str, Type]  # Parameter schema

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool and return results."""
        pass
```

### Available Tools

See [TOOLS_REFERENCE.md](../features/TOOLS_REFERENCE.md) for complete list.

| Tool | Description | Example |
|------|-------------|---------|
| `document_search` | RAG search in indexed docs | "Find info about transformers" |
| `web_search` | Internet search | "Latest news on AI" |
| `calculator` | Math calculations | "Calculate 15% of 250" |
| `code_executor` | Run Python code | "Generate fibonacci series" |
| `file_ops` | File operations | "Save this data to CSV" |
| `news_api` | Fetch news articles | "Tech news from today" |

## Memory Integration

The agent has full access to conversation history through `MemoryManager`.

### Memory in Understanding Phase

```python
if self.enable_memory and self.memory_manager:
    # Restore from checkpoint if resuming
    if state.get('conversation_messages'):
        # Deserialize messages back to ConversationMemory
        conversation_dict = {
            'messages': state['conversation_messages'],
            'session_id': self.memory_manager.session_id,
            # ...
        }
        self.memory_manager.conversation_memory = ConversationMemory.from_dict(conversation_dict)

    # Add new user message
    self.memory_manager.add_user_message(state['query'])

    # Get full context
    memory_context = self.memory_manager.get_full_context(
        current_query=state['query'],
        include_episodic=True
        
    )

    state['memory_context'] = memory_context

    # Serialize for checkpoint persistence
    state['conversation_messages'] = [
        {
            'role': msg.role,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'metadata': msg.metadata
        }
        for msg in self.memory_manager.conversation_memory.messages
    ]
```

### Memory in Synthesis Phase

```python
if self.enable_memory and self.memory_manager:
    # Add assistant message
    self.memory_manager.add_assistant_message(
        content=state['final_answer'],
        tools_used=state['tools_used']
    )

    # Update conversation_messages in state
    state['conversation_messages'] = [...]
```

## Checkpoint Integration

The agent uses LangGraph's checkpoint system to persist state across executions.

### Execution with Thread ID

```python
# First query (creates checkpoint)
agent.execute(
    query="My name is Alice",
    thread_id="user_123",
    session_id="web_session_456"
)
# → Checkpoint saved with thread_id="user_123"

# Second query (resumes checkpoint)
agent.execute(
    query="What's my name?",
    thread_id="user_123",  # SAME thread_id
    session_id="web_session_456"
)
# → Checkpoint loaded, conversation_messages restored
# → Agent knows name is Alice!
```

### Checkpoint Content

```python
{
    'thread_id': 'user_123',
    'checkpoint_id': 'abc123...',
    'state': {
        'query': 'What is my name?',
        'final_answer': 'Your name is Alice',
        'conversation_messages': [
            {'role': 'user', 'content': 'My name is Alice', ...},
            {'role': 'assistant', 'content': 'Nice to meet you...', ...},
            {'role': 'user', 'content': 'What is my name?', ...},
            {'role': 'assistant', 'content': 'Your name is Alice', ...}
        ],
        'tools_used': ['document_search'],
        # ... all other state fields
    }
}
```

## Reflection & Self-Correction

**File**: [src/agent/reflection/reflection_module.py](../src/agent/reflection/reflection_module.py)

Optional module for self-evaluation and learning.

### Reflection Process

```python
class ReflectionModule:
    def reflect_on_interaction(self, query, answer, context, tools_used):
        """
        Evaluate the quality of the interaction.

        Returns:
            {
                'quality_score': 0.8,
                'issues': ['Could be more concise'],
                'suggestions': ['Add source citations'],
                'learnings': 'User prefers technical depth'
            }
        """
        # 1. Check answer relevance
        # 2. Detect hallucinations
        # 3. Evaluate tool selection
        # 4. Identify patterns
```

### Integration in Agent

```python
if self.enable_reflection:
    reflection_result = self.reflection_module.reflect_on_interaction(
        query=state['query'],
        answer=state['final_answer'],
        context=state['memory_context'],
        tools_used=state['tools_used']
    )

    # Store learnings in episodic memory
    if reflection_result['learnings']:
        self.memory_manager.episodic_memory.add_learning(
            reflection_result['learnings']
        )
```

## Configuration

**Relevant Settings** (from `.env`):

```bash
# Agent Behavior
AGENT_ENABLED=true                  # Enable/disable agent
AGENT_MODE=hybrid                   # react, plan-execute, hybrid
AGENT_MAX_ITERATIONS=10             # Max tool retries
AGENT_TIMEOUT=120                   # Execution timeout (seconds)
AGENT_VERBOSE=true                  # Debug logging

# Memory
MEMORY_ENABLED=true                 # Enable conversation memory
MEMORY_WINDOW_SIZE=10               # Recent message window
MEMORY_SUMMARY_FREQUENCY=5          # Summarize every N turns

# Reflection
REFLECTION_ENABLED=true             # Enable self-reflection
HALLUCINATION_DETECTION=false       # Detect hallucinations
```

## Usage Examples

### Basic Query

```python
from src.agent.agent_executor_v3 import AgentExecutorV3

# Initialize agent
agent = AgentExecutorV3(
    llm=llm,
    tool_registry=tool_registry,
    config=Config,
    enable_memory=True,
    enable_reflection=False
)

# Execute query
result = agent.execute(
    query="What is a transformer architecture?",
    thread_id="user_123"
)

print(result['answer'])
# Output: "A transformer architecture is..."
```

### Multi-Turn Conversation

```python
# Turn 1
result1 = agent.execute(
    query="My favorite topic is machine learning",
    thread_id="conversation_abc"
)

# Turn 2 (agent remembers previous context)
result2 = agent.execute(
    query="Can you recommend some resources?",
    thread_id="conversation_abc"  # SAME thread_id
)
# Agent knows to recommend ML resources!
```

### Tool-Heavy Query

```python
result = agent.execute(
    query="What's the latest news on AI, and calculate the ROI if we invest $10k",
    thread_id="multi_tool"
)

# Agent will:
# 1. Use news_api tool to fetch AI news
# 2. Use calculator tool for ROI calculation
# 3. Synthesize answer combining both results
```

## Error Handling

### Retry Logic

```python
# If tool fails, agent can retry with different tool
state['needs_retry'] = True
state['last_error'] = "Tool execution failed: ..."
state['iteration'] += 1

if state['iteration'] < state['max_iterations']:
    # Route to different tool
    return "routing"
else:
    # Give up and synthesize best-effort answer
    return "synthesize"
```

### Timeout Protection

```python
if time.time() - state['start_time'] > Config.AGENT_TIMEOUT:
    raise TimeoutError("Agent execution exceeded timeout")
```

## Performance Optimization

### Caching
- Tool results cached within same execution
- Memory context cached for repeated queries
- LLM responses cached (if using Langchain cache)

### Parallel Execution
- Multiple independent tools can run in parallel (future enhancement)
- Async tool execution supported

### Checkpoint Efficiency
- Only save state on phase transitions
- Incremental updates to conversation_messages
- Database connection pooling

## Debugging

### Enable Verbose Mode

```bash
AGENT_VERBOSE=true
```

Output:
```
🔍 Phase: understanding
📝 Memory context: [Recent conversation]...
🔧 Selected tool: document_search
🎯 Tool result: {...}
💡 Synthesized answer: ...
✅ Execution complete (2.3s)
```

### Inspect State

```python
# During execution
print(state['current_phase'])
print(state['tools_used'])
print(state['conversation_messages'])
```

### Checkpoint Debugging

```python
from src.database.checkpoint_backend import get_checkpoint_manager

checkpoint_mgr = get_checkpoint_manager()

# List checkpoints for thread
checkpoints = checkpoint_mgr.list_checkpoints(thread_id="user_123")
for cp in checkpoints:
    print(f"Checkpoint: {cp['checkpoint_id']} at {cp['created_at']}")

# Get specific checkpoint
checkpoint_data = checkpoint_mgr.get_checkpoint(
    thread_id="user_123",
    checkpoint_id="abc123..."
)
```

## Best Practices

1. **Always use thread_id** for multi-turn conversations
2. **Enable memory** for context-aware responses
3. **Limit iterations** to prevent infinite loops
4. **Handle timeouts** gracefully
5. **Monitor checkpoint growth** in database
6. **Clear old checkpoints** periodically
7. **Use reflection** in production for quality monitoring
8. **Test tool selection** with diverse queries
9. **Log execution metrics** for performance tuning
10. **Sanitize user input** before tool execution

## Troubleshooting

### Agent not remembering context
- Check `MEMORY_ENABLED=true`
- Verify `USE_CHECKPOINTS=true`
- Ensure same `thread_id` across queries
- See [CONVERSATION_MEMORY_FIX.md](../CONVERSATION_MEMORY_FIX.md)

### Tool selection issues
- Review tool descriptions (make them clear)
- Check LLM temperature (lower = more deterministic)
- Enable verbose mode to see reasoning
- Test with specific tool-targeted queries

### Slow execution
- Profile each phase with timing logs
- Check network latency (web search, LLM API)
- Enable caching for repeated queries
- Reduce `MEMORY_WINDOW_SIZE` if too large

### Checkpoint errors
- Verify database connection
- Check `langgraph-checkpoint-postgres` installed
- Ensure PostgreSQL tables created
- Test with `checkpoint_mgr.is_available()`

## Related Documentation

- [Memory System](MEMORY_SYSTEM.md) - Conversation and episodic memory
- [Tools Reference](../features/TOOLS_REFERENCE.md) - All available tools
- [Database Persistence](DATABASE_PERSISTENCE.md) - Checkpoint storage
- [Configuration](../CONFIGURATION.md) - All agent settings
