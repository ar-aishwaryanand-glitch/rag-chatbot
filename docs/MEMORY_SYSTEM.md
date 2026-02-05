# Memory System Documentation

## Overview

The memory system enables the agent to maintain context across conversations, remember past interactions, and provide personalized responses. It consists of two complementary memory types:

1. **Conversation Memory**: Short-term message history within a session
2. **Episodic Memory**: Long-term summaries and patterns across sessions

## Architecture

```
MemoryManager (Unified Interface)
├── ConversationMemory (Short-term)
│   ├── Message buffer (recent N messages)
│   ├── Session metadata
│   └── Serialization (for checkpoints)
│
└── EpisodicMemory (Long-term)
    ├── Episode storage (past sessions)
    ├── Pattern detection
    └── Preference aggregation
```

## Conversation Memory

**File**: [src/agent/memory/conversation_memory.py](../src/agent/memory/conversation_memory.py)

Stores recent messages within the current conversation session.

### Structure

```python
class ConversationMessage:
    role: str              # "user" or "assistant"
    content: str           # Message text
    timestamp: datetime    # When message was sent
    metadata: Dict         # Additional data (tools_used, etc.)

class ConversationMemory:
    session_id: str                      # Unique session ID
    session_start: datetime              # Session start time
    messages: List[ConversationMessage]  # Message buffer
    max_messages: int                    # Buffer size limit
    turn_count: int                      # Number of user turns
```

### Key Features

#### 1. Message Buffer with Sliding Window

```python
# Create memory with max 10 messages
memory = ConversationMemory(session_id="session_123", max_messages=10)

# Add messages
memory.add_message("user", "What is machine learning?")
memory.add_message("assistant", "Machine learning is...")

# When buffer exceeds 10 messages, oldest are removed
# → Always keeps most recent conversation
```

#### 2. Context Retrieval

```python
# Get formatted context for LLM
context = memory.get_context_string(max_messages=5)

# Output:
"""
[Recent conversation]
User: What is machine learning?
Assistant: Machine learning is...
User: Can you give examples?
Assistant: Sure! Here are examples...
User: What about deep learning?
"""
```

#### 3. Serialization for Checkpoints

```python
# Export to dict (for checkpoint storage)
conversation_dict = memory.to_dict()
# Returns:
{
    'session_id': 'session_123',
    'session_start': '2026-02-04T10:00:00',
    'messages': [
        {'role': 'user', 'content': '...', 'timestamp': '...', 'metadata': {}},
        # ...
    ],
    'turn_count': 5,
    'summary': None,
    'stats': {...}
}

# Restore from dict (when resuming)
restored_memory = ConversationMemory.from_dict(conversation_dict)
# → Full conversation history restored!
```

### Usage

```python
from src.agent.memory.conversation_memory import ConversationMemory

# Initialize
memory = ConversationMemory(session_id="user_123")

# Add user message
memory.add_message(
    role="user",
    content="What's the weather like?",
    metadata={'source': 'web_ui'}
)

# Add assistant message with tool info
memory.add_message(
    role="assistant",
    content="It's sunny and 72°F",
    metadata={'tools_used': ['web_search']}
)

# Get recent context
context = memory.get_context_string(max_messages=5)

# Get last user message
last_query = memory.get_last_user_message()
# → "What's the weather like?"

# Get statistics
stats = memory.get_stats()
# Returns: {'turn_count': 1, 'total_messages': 2, 'session_duration_seconds': 15}
```

### Integration with Agent State

**CRITICAL**: Conversation messages must be stored in agent state for checkpoint persistence.

```python
# In agent_executor_v3.py

# AFTER adding user message:
memory_manager.add_user_message(state['query'])

# Serialize to state for checkpoint
state['conversation_messages'] = [
    {
        'role': msg.role,
        'content': msg.content,
        'timestamp': msg.timestamp.isoformat(),
        'metadata': msg.metadata
    }
    for msg in memory_manager.conversation_memory.messages
]

# WHEN resuming from checkpoint:
if state.get('conversation_messages'):
    # Deserialize back to ConversationMemory
    conversation_dict = {
        'session_id': memory_manager.session_id,
        'session_start': memory_manager.conversation_memory.session_start.isoformat(),
        'messages': state['conversation_messages'],
        'turn_count': len([m for m in state['conversation_messages'] if m['role'] == 'user']),
        'summary': None,
        'stats': memory_manager.conversation_memory.stats
    }
    memory_manager.conversation_memory = ConversationMemory.from_dict(conversation_dict)
```

See [CONVERSATION_MEMORY_FIX.md](../CONVERSATION_MEMORY_FIX.md) for detailed explanation.

## Episodic Memory

**File**: [src/agent/memory/episodic_memory.py](../src/agent/memory/episodic_memory.py)

Stores long-term summaries and patterns from past sessions.

### Structure

```python
class Episode:
    episode_id: str          # Unique episode ID
    session_id: str          # Original session ID
    timestamp: datetime      # When episode was created
    summary: str             # High-level summary of session
    user_queries: List[str]  # All user questions in session
    tools_used: List[str]    # Tools used during session
    outcomes: List[str]      # Success/failure notes
    key_entities: List[str]  # Important topics/entities
    metadata: Dict           # Additional data

class EpisodicMemory:
    storage_path: Path       # Where to save episodes
    episodes: List[Episode]  # All stored episodes
```

### Key Features

#### 1. Session Summarization

```python
# At end of session, create episode
episode = episodic_memory.create_episode_from_conversation(
    session_id="session_123",
    conversation_summary="User asked about ML algorithms and model evaluation",
    user_queries=["What is ML?", "How to evaluate models?"],
    tools_used=["document_search", "web_search"],
    outcomes=["Successfully answered questions"],
    key_entities=["machine learning", "evaluation", "metrics"]
)
```

#### 2. Pattern Detection

```python
# Get user preferences across sessions
preferences = episodic_memory.get_aggregated_preferences()

# Returns:
{
    'most_common_topics': ['machine learning', 'python', 'data science'],
    'most_used_tools': ['document_search', 'web_search'],
    'typical_query_types': ['how-to questions', 'conceptual questions'],
    'session_count': 15,
    'avg_turns_per_session': 4.2
}
```

#### 3. Context Retrieval

```python
# Search past episodes for relevant context
relevant_episodes = episodic_memory.search_episodes(
    query="machine learning algorithms",
    max_results=3
)

# Returns episodes with similar topics
for episode in relevant_episodes:
    print(f"{episode.timestamp}: {episode.summary}")
    print(f"Topics: {', '.join(episode.key_entities)}")
```

### Usage

```python
from src.agent.memory.episodic_memory import EpisodicMemory

# Initialize (loads from disk if exists)
episodic = EpisodicMemory(storage_path="data/memory_store")

# Create episode from session
episode = episodic.create_episode_from_conversation(
    session_id="session_123",
    conversation_summary="Discussion about neural networks",
    user_queries=["What are neural networks?", "How do they learn?"],
    tools_used=["document_search"],
    key_entities=["neural networks", "deep learning", "backpropagation"]
)

# Search episodes
results = episodic.search_episodes("neural networks", max_results=3)

# Get preferences
prefs = episodic.get_aggregated_preferences()

# Get summary
summary = episodic.get_summary()
# Returns: {'total_episodes': 42, 'date_range': ..., 'most_common_topics': ...}

# Clear all (use with caution!)
episodic.clear_all()
```

## Memory Manager

**File**: [src/agent/memory/memory_manager.py](../src/agent/memory/memory_manager.py)

Unified interface that coordinates both memory types.

### Architecture

```python
class MemoryManager:
    conversation_memory: ConversationMemory  # Current session
    episodic_memory: EpisodicMemory         # Long-term storage
    session_id: str                         # Current session ID
```

### Key Methods

#### Add Messages

```python
memory_manager = MemoryManager(session_id="user_123")

# Add user message
memory_manager.add_user_message(
    content="What is machine learning?",
    metadata={'source': 'web_ui'}
)

# Add assistant message
memory_manager.add_assistant_message(
    content="Machine learning is...",
    tools_used=["document_search"],
    metadata={'confidence': 0.95}
)
```

#### Get Full Context

```python
# Get combined context: recent conversation + relevant history
full_context = memory_manager.get_full_context(
    current_query="How do I train a model?",
    include_episodic=True,
    max_conversation_messages=5
)

# Output:
"""
[Relevant past conversations]
1. 2026-02-01: Discussion about ML fundamentals
   Topics: machine learning, algorithms, training

[Recent conversation]
User: What is machine learning?
Assistant: Machine learning is...
User: How do I train a model?
"""
```

#### Finalize Session

```python
# At end of session, create episode
episode = memory_manager.finalize_session(
    summary="User learned about ML training process",
    outcomes=["Successfully explained training concepts"],
    key_entities=["training", "validation", "overfitting"]
)

# Episode is now stored in episodic memory
```

### Integration with Agent

```python
# In AgentExecutorV3

class AgentExecutorV3:
    def __init__(self, ..., enable_memory=True):
        if enable_memory:
            self.memory_manager = MemoryManager(
                session_id=session_id,
                storage_path=Config.MEMORY_STORE_PATH,
                max_conversation_messages=Config.MEMORY_WINDOW_SIZE
            )

    def _understand_query(self, state):
        if self.enable_memory:
            # Restore from checkpoint if resuming
            if state.get('conversation_messages'):
                self.memory_manager.conversation_memory = ConversationMemory.from_dict(...)

            # Add user message
            self.memory_manager.add_user_message(state['query'])

            # Get full context
            memory_context = self.memory_manager.get_full_context(
                current_query=state['query'],
                include_episodic=True
            )

            state['memory_context'] = memory_context

            # Save to state for checkpoint
            state['conversation_messages'] = [...]

    def _synthesize_answer(self, state):
        if self.enable_memory:
            # Add assistant message
            self.memory_manager.add_assistant_message(
                content=state['final_answer'],
                tools_used=state['tools_used']
            )

            # Update state
            state['conversation_messages'] = [...]
```

## Checkpoint Persistence

### The Problem

Before the fix, conversation memory was **lost** when resuming from checkpoints:

```
Query 1 (thread_id="abc"):
└─ ConversationMemory.messages = ["User: Hi", "Assistant: Hello"]
└─ Checkpoint saves state BUT NOT messages ❌

Query 2 (thread_id="abc"):
└─ Checkpoint loads state
└─ But ConversationMemory starts fresh: messages = [] ❌
└─ Agent has NO CONTEXT! 😞
```

### The Solution

Store `conversation_messages` **in agent state** so it persists:

```
Query 1 (thread_id="abc"):
├─ ConversationMemory.messages = ["User: Hi", "Assistant: Hello"]
├─ Serialize to state['conversation_messages'] = [...]
└─ Checkpoint saves state WITH messages ✅

Query 2 (thread_id="abc"):
├─ Checkpoint loads state with conversation_messages
├─ Restore to ConversationMemory.from_dict(state['conversation_messages'])
└─ Agent has FULL CONTEXT! 🎉
```

See [CONVERSATION_MEMORY_FIX.md](../CONVERSATION_MEMORY_FIX.md) for implementation details.

## Configuration

**Memory Settings** (from `.env`):

```bash
# Enable/disable memory
MEMORY_ENABLED=true

# Conversation window size (number of recent messages)
MEMORY_WINDOW_SIZE=10

# How often to summarize long conversations
MEMORY_SUMMARY_FREQUENCY=5

# Storage path for episodic memory
# (default: data/memory_store/)
```

## Usage Examples

### Basic Conversation

```python
# Initialize
memory = MemoryManager(session_id="user_123")

# Turn 1
memory.add_user_message("My name is Alice")
memory.add_assistant_message("Nice to meet you, Alice!")

# Turn 2
context = memory.get_full_context("What's my name?")
print(context)
# Output:
# [Recent conversation]
# User: My name is Alice
# Assistant: Nice to meet you, Alice!
# User: What's my name?

memory.add_assistant_message("Your name is Alice!")
```

### Multi-Session Learning

```python
# Session 1
memory1 = MemoryManager(session_id="session_1")
memory1.add_user_message("I'm interested in ML")
memory1.add_assistant_message("Great! Let's discuss ML")
memory1.finalize_session(
    summary="User expressed interest in ML",
    key_entities=["machine learning"]
)

# Session 2 (days later)
memory2 = MemoryManager(session_id="session_2")
memory2.add_user_message("Can you recommend ML resources?")

# Get relevant history
history = memory2.get_relevant_history("ML resources")
# → Finds Session 1 because of "machine learning" entity match!

print(history)
# Output:
# [Relevant past conversations]
# 1. 2026-02-01: User expressed interest in ML
#    Topics: machine learning
```

### Personalized Responses

```python
# Get user preferences
prefs = memory_manager.get_user_preferences()

if "technical details" in prefs['most_common_topics']:
    # User likes technical depth
    response_style = "detailed_technical"
else:
    response_style = "simplified"

# Generate response with appropriate style
answer = generate_answer(query, context, style=response_style)
```

## Statistics and Monitoring

### Session Stats

```python
stats = memory_manager.get_session_stats()

# Returns:
{
    'session_id': 'session_123',
    'turn_count': 5,
    'total_messages': 10,
    'session_start': '2026-02-04T10:00:00',
    'session_duration_seconds': 245
}
```

### Memory Summary

```python
summary = memory_manager.get_memory_summary()

# Returns:
{
    'current_session': {
        'turn_count': 5,
        'total_messages': 10,
        # ...
    },
    'episodic_memory': {
        'total_episodes': 42,
        'date_range': ['2026-01-15', '2026-02-04'],
        'most_common_topics': ['ML', 'Python', 'Data Science'],
        'total_user_queries': 178
    }
}
```

## Best Practices

### 1. Always Use Same thread_id for Multi-Turn Conversations

```python
# ✅ CORRECT
agent.execute(query="My name is Alice", thread_id="user_123")
agent.execute(query="What's my name?", thread_id="user_123")  # SAME ID

# ❌ WRONG
agent.execute(query="My name is Alice", thread_id="conv_1")
agent.execute(query="What's my name?", thread_id="conv_2")  # DIFFERENT ID
```

### 2. Finalize Sessions for Long-Term Learning

```python
# At end of conversation
memory_manager.finalize_session(
    summary="Discussed ML model deployment",
    outcomes=["User understood deployment process"],
    key_entities=["deployment", "docker", "kubernetes"]
)
```

### 3. Clear Conversation Between Topics

```python
# If user switches to completely different topic
memory_manager.clear_conversation()
# → Clears recent messages but keeps episodic memory
```

### 4. Monitor Memory Usage

```python
# Periodically check memory size
summary = memory_manager.get_memory_summary()
episode_count = summary['episodic_memory']['total_episodes']

if episode_count > 1000:
    # Consider archiving old episodes
    pass
```

### 5. Serialize for Checkpoints

```python
# Always save conversation_messages to state
state['conversation_messages'] = [
    msg.to_dict() for msg in memory_manager.conversation_memory.messages
]

# Always restore on resume
if state.get('conversation_messages'):
    memory_manager.conversation_memory = ConversationMemory.from_dict(...)
```

## Troubleshooting

### Memory Not Persisting

**Symptom**: Agent forgets previous conversation

**Solutions**:
1. Check `MEMORY_ENABLED=true` in `.env`
2. Verify `USE_CHECKPOINTS=true`
3. Ensure same `thread_id` across queries
4. Verify `conversation_messages` in state
5. See [CONVERSATION_MEMORY_FIX.md](../CONVERSATION_MEMORY_FIX.md)

### Episodic Search Not Finding Relevant Context

**Symptom**: Past conversations not included in context

**Solutions**:
1. Ensure `include_episodic=True` in `get_full_context()`
2. Check if episodes have `key_entities` set
3. Verify episodic memory storage path exists
4. Test search directly: `episodic_memory.search_episodes(query)`

### Memory Growing Too Large

**Symptom**: Slow performance, high memory usage

**Solutions**:
1. Reduce `MEMORY_WINDOW_SIZE` (default: 10)
2. Archive old episodes periodically
3. Clear conversation between topics
4. Implement episode expiration policy

### Conversation Context Too Long for LLM

**Symptom**: Token limit exceeded errors

**Solutions**:
1. Reduce `max_conversation_messages` parameter
2. Use summary instead of full messages
3. Implement intelligent message pruning
4. Store only key information in metadata

## Performance Considerations

### Memory Overhead

- **Conversation Memory**: ~1KB per message
- **Episode Storage**: ~5KB per episode
- **In-Memory**: All episodes loaded at startup

### Optimization Tips

1. **Limit conversation buffer**: Keep `max_messages` <= 20
2. **Archive old episodes**: Move episodes older than 90 days
3. **Lazy load episodes**: Load only when searching
4. **Cache searches**: Cache episodic search results
5. **Compress storage**: Use JSON compression for disk storage

## Future Enhancements

- [ ] Vector-based episode search (semantic similarity)
- [ ] Automatic preference learning from interactions
- [ ] Multi-user memory isolation
- [ ] Memory compression for long-term storage
- [ ] Real-time memory synchronization across devices
- [ ] Smart memory pruning based on relevance
- [ ] Memory export/import for portability

## Related Documentation

- [Agent System](AGENT_SYSTEM.md) - How memory integrates with agent
- [Database Persistence](DATABASE_PERSISTENCE.md) - Checkpoint storage
- [Configuration](CONFIGURATION.md) - Memory settings
- [Conversation Memory Fix](../CONVERSATION_MEMORY_FIX.md) - Implementation details
