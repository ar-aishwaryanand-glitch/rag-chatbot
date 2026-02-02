# Phase 3: Memory & Self-Reflection - Design Document

## Overview

Phase 3 enhances the agentic RAG system with conversation memory and self-reflection capabilities, enabling the agent to:
- Remember past conversations and context
- Learn from previous interactions
- Self-evaluate and improve responses
- Provide more personalized and context-aware answers

## Architecture

### 1. Memory System

#### Short-Term Memory (Conversation Buffer)
```python
class ConversationMemory:
    """Manages conversation history within a session."""

    - conversation_history: List[Message]  # Recent messages
    - context_summary: str  # Condensed summary of older messages
    - max_messages: int = 10  # Keep last N messages
    - session_id: str  # Unique session identifier
```

**Features:**
- Stores last N messages (default: 10)
- Automatically summarizes older messages to save tokens
- Injects relevant history into agent prompts
- Clears on session end

#### Long-Term Memory (Episodic Memory)
```python
class EpisodicMemory:
    """Stores summaries of past conversations."""

    - memory_store: Dict[str, Episode]  # session_id -> Episode
    - memory_embeddings: VectorStore  # Search past conversations
```

**Storage:**
```python
Episode = {
    "session_id": str,
    "timestamp": datetime,
    "summary": str,  # What was discussed
    "user_preferences": Dict,  # Learned preferences
    "outcomes": List[str],  # Success/failure of actions
    "key_entities": List[str]  # Important topics/names
}
```

**Features:**
- Persists to disk/database
- Searchable via embeddings
- Retrieves relevant past conversations
- Learns user patterns over time

#### Working Memory (Agent State)
Already implemented in `AgentState`:
- Current task context
- Active tool results
- Iteration tracking
- Error history

### 2. Self-Reflection System

#### Reflection Module
```python
class ReflectionModule:
    """Evaluates agent performance and suggests improvements."""

    def reflect_on_action(self, action, result, context):
        """Analyze if action was appropriate."""

    def reflect_on_answer(self, question, answer, sources):
        """Evaluate answer quality."""

    def suggest_improvements(self, history):
        """Identify patterns for improvement."""
```

**Reflection Triggers:**
1. **After Tool Execution**: Was the right tool selected?
2. **After Answer Generation**: Is the answer complete and accurate?
3. **On Error**: What went wrong and how to fix it?
4. **End of Session**: Overall performance review

**Reflection Prompt Template:**
```
Evaluate the following interaction:

Question: {question}
Tool Selected: {tool}
Tool Result: {result}
Final Answer: {answer}

Analysis:
1. Was the tool selection appropriate? (Yes/No + reasoning)
2. Was the tool execution successful? (Yes/No + errors)
3. Is the answer accurate and complete? (1-5 rating)
4. Are there better approaches? (Suggestions)

Provide structured feedback:
- What went well: ...
- What could improve: ...
- Recommended action: ...
```

#### Learning from Reflection
```python
class LearningModule:
    """Applies insights from reflection to improve future performance."""

    - success_patterns: Dict  # What works well
    - failure_patterns: Dict  # Common mistakes
    - tool_performance: Dict  # Tool accuracy stats
```

**Metrics Tracked:**
- Tool selection accuracy per query type
- Average response time per tool
- User satisfaction indicators
- Error rates and recovery success

### 3. Integration with Existing System

#### Modified Agent Executor Flow
```
1. Understand Query
   ├─> Check conversation memory
   └─> Retrieve relevant past episodes

2. Route to Tool
   ├─> Consider memory context
   └─> Apply learned patterns

3. Execute Tool
   └─> Track execution metadata

4. Synthesize Answer
   ├─> Include memory context
   └─> Check against past similar queries

5. Reflect [NEW]
   ├─> Evaluate tool selection
   ├─> Evaluate answer quality
   └─> Update learning metrics

6. Update Memory [NEW]
   ├─> Add to conversation history
   ├─> Update episodic memory if significant
   └─> Extract user preferences
```

### 4. New Components

#### File Structure
```
src/agent/
├── memory/
│   ├── __init__.py
│   ├── conversation_memory.py    # Short-term memory
│   ├── episodic_memory.py        # Long-term memory
│   └── memory_manager.py         # Unified interface
├── reflection/
│   ├── __init__.py
│   ├── reflection_module.py      # Self-evaluation
│   └── learning_module.py        # Pattern extraction
└── agent_executor_v3.py          # Enhanced executor
```

#### New Tools
```python
class MemorySearchTool(BaseTool):
    """Search past conversations for relevant context."""
    name = "memory_search"

class PreferenceManagerTool(BaseTool):
    """Manage and retrieve user preferences."""
    name = "preference_manager"
```

## Implementation Plan

### Step 1: Conversation Memory (Basic)
- [x] Design memory structure
- [ ] Implement ConversationMemory class
- [ ] Add to AgentState
- [ ] Test with multi-turn conversations

### Step 2: Memory Integration
- [ ] Inject memory into prompts
- [ ] Add memory summarization
- [ ] Implement memory retrieval
- [ ] Test memory context improves answers

### Step 3: Episodic Memory (Advanced)
- [ ] Design Episode storage format
- [ ] Implement EpisodicMemory class
- [ ] Add vector search for past conversations
- [ ] Persist to disk
- [ ] Test cross-session memory

### Step 4: Basic Reflection
- [ ] Implement ReflectionModule
- [ ] Add post-action evaluation
- [ ] Add post-answer evaluation
- [ ] Log reflections

### Step 5: Learning Module
- [ ] Track tool performance metrics
- [ ] Identify success/failure patterns
- [ ] Store learned patterns
- [ ] Apply patterns to improve routing

### Step 6: Advanced Reflection
- [ ] Self-correction on errors
- [ ] Iterative improvement
- [ ] Explanation generation
- [ ] Confidence scoring

### Step 7: Memory Tools
- [ ] Implement MemorySearchTool
- [ ] Implement PreferenceManagerTool
- [ ] Register with tool registry
- [ ] Test agent using memory tools

### Step 8: Testing & Validation
- [ ] Unit tests for memory components
- [ ] Unit tests for reflection components
- [ ] Integration tests
- [ ] Performance benchmarks
- [ ] User testing

## Example Use Cases

### Use Case 1: Contextual Conversations
```
User: "Calculate 50 * 30"
Agent: [uses calculator] "Result: 1500"
Memory: Stores this interaction

User: "Now multiply that by 10"
Agent: [retrieves "that" = 1500 from memory]
       [uses calculator] "15000"
```

### Use Case 2: Learning Preferences
```
User: "Search Python documentation"
Memory: User frequently searches Python topics

[Later session]
User: "Find docs about decorators"
Agent: [remembers Python preference]
       [searches Python-specific sources]
```

### Use Case 3: Self-Correction
```
User: "What is the capital of France?"
Agent: [uses web_search incorrectly]
Reflection: "Should use document_search for factual questions"
Learning: Updates routing patterns
Memory: Stores correction

[Next similar query]
Agent: [applies learned pattern] [uses document_search correctly]
```

### Use Case 4: Error Recovery
```
User: "Read file important.txt"
Agent: [file_operations] Error: File not found
Reflection: "Failed to find file, should list directory first"
Agent: [file_operations] Lists available files
Agent: "I couldn't find important.txt. Available files: [...]. Did you mean one of these?"
```

## Success Metrics

### Memory System
- Conversation continuity score (how well it remembers context)
- Cross-session recall accuracy
- Memory retrieval relevance

### Reflection System
- Error recovery rate
- Tool selection improvement over time
- Answer quality trend
- User satisfaction increase

## Technical Considerations

### Token Management
- Summarize old messages to save tokens
- Smart context injection (only relevant memory)
- Configurable memory limits

### Performance
- Memory search should be <50ms
- Reflection adds <500ms overhead
- Async processing where possible

### Privacy
- User data isolation
- Option to clear memory
- No PII in episodic storage without consent

### Scalability
- Memory per user/session
- Efficient storage format
- Pagination for large histories

## Next Steps

1. Start with basic conversation memory
2. Add simple reflection (logging only)
3. Gradually enhance both systems
4. Test extensively before production
5. Add UI for memory visualization

## Notes

- Phase 3 is additive - all Phase 2 features remain
- Memory is optional - system works without it
- Reflection runs in background, doesn't block responses
- Start simple, enhance based on real usage patterns
