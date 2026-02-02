# RAG Agent UI Guide (Phase 3)

Complete guide for using the enhanced RAG Agent UI with Memory and Self-Reflection capabilities.

## 🚀 Quick Start

### Launch the Agent UI

**Mac/Linux:**
```bash
./launch_agent_ui.sh
```

**Windows:**
```bash
launch_agent_ui.bat
```

**Or directly:**
```bash
streamlit run run_agent_ui.py
```

The app will open at [http://localhost:8501](http://localhost:8501)

---

## 🧠 Phase 3 Features

### 1. Memory System

The agent has two types of memory:

#### Conversation Memory (Short-term)
- Remembers the last 10 messages in your conversation
- Automatically summarizes older messages
- Helps agent understand context and references like "that", "the previous result", etc.

**Example:**
```
You: Calculate 25 * 4
Agent: Result: 100

You: Now multiply that by 2
Agent: [Retrieves "that" = 100 from memory] Result: 200
```

#### Episodic Memory (Long-term)
- Saves session summaries to disk
- Learns patterns across multiple sessions
- Tracks user preferences and common query types
- Stored in: `data/episodic_memory/`

### 2. Self-Reflection System

The agent evaluates its own performance:

#### Reflection Types:
1. **Tool Selection** - Was the right tool chosen?
2. **Answer Quality** - How good was the answer? (1-5 scale)
3. **Error Analysis** - What went wrong and how to fix it?
4. **Session Summary** - Overall performance review

#### Learning Module:
- Tracks tool performance metrics
- Learns which tools work best for different query types
- Improves routing decisions over time
- Displays success rates and rankings

### 3. Multi-Tool Intelligence

The agent can intelligently choose from 6 tools:

| Tool | Use Case | Examples |
|------|----------|----------|
| **document_search** | Answer from indexed documents | "What is RAG?", "Explain AI agents" |
| **web_search** | Current information from web | "Latest AI news", "Weather in Paris" |
| **calculator** | Math calculations | "Calculate 15% of 2000" |
| **python_executor** | Run Python code | "Sort this list: [3,1,4,1,5]" |
| **file_operations** | File/folder operations | "List files", "Read config.py" |
| **document_manager** | Vector store info | "What documents are indexed?" |

---

## 🎮 Using the Interface

### Main Chat Area

1. **Welcome Screen**: Shows capabilities and example queries
2. **Chat History**: Your conversation with the agent
3. **Agent Reasoning** (expandable): See tool selection and execution details
4. **Memory Context** (expandable): View conversation history
5. **Reflection Insights** (expandable): See learning statistics

### Sidebar Controls

#### 🧠 Phase 3 Features
- **Enable Memory** - Turn conversation and episodic memory on/off
- **Enable Self-Reflection** - Turn self-evaluation and learning on/off

*Note: Changing these settings will restart the agent*

#### 📊 Display Options
- **Show Agent Reasoning** - Display tool selection and execution steps
- **Show Memory Context** - Display conversation history and session stats
- **Show Reflection Insights** - Display learning stats and tool rankings

#### 📈 Session Stats
- **Queries** - Number of questions asked in this session
- **Success Rate** - Percentage of successful tool executions
- **Tools Used** - Number of unique tools used

#### Actions
- **End Session & Save** - Finalize session and save to episodic memory
- **Clear Chat** - Clear conversation history
- **Reset System** - Restart agent from scratch

---

## 💡 Example Queries

### Document Search (RAG)
```
"What is Retrieval-Augmented Generation?"
"Explain how AI agents work"
"What are the benefits of vector databases?"
```

### Web Search
```
"What's the latest news about GPT-5?"
"Current weather in London"
"Recent developments in quantum computing"
```

### Calculations
```
"Calculate 15% tip on $125.50"
"What is 2^10?"
"Calculate compound interest: $10000, 5% annual, 3 years"
```

### Code Execution
```
"Write Python code to reverse a string"
"Generate a list of prime numbers up to 50"
"Create a function to calculate factorial"
```

### File Operations
```
"List files in the current directory"
"Show me the contents of README.md"
"Search for files containing 'config'"
```

### Document Management
```
"What documents are indexed?"
"Show vector store statistics"
"How many chunks are in the index?"
```

### Context-Aware (Requires Memory Enabled)
```
You: Calculate 100 * 5
Agent: Result: 500

You: Add 250 to that
Agent: [Uses memory] Result: 750

You: What was my first question?
Agent: [Retrieves from memory] You asked me to calculate 100 * 5
```

---

## 🔧 Customization

### Enable/Disable Features

Toggle features in the sidebar:
- Memory can be disabled for stateless operation
- Reflection can be disabled to reduce processing time
- Display options can be adjusted for cleaner interface

### Configuration

Adjust agent behavior in `src/config.py`:

```python
# Agent settings
AGENT_MAX_ITERATIONS = 3

# Memory settings
CONVERSATION_MEMORY_MAX_MESSAGES = 10

# File operations workspace
FILE_OPS_WORKSPACE = "workspace"
```

---

## 📊 Understanding Agent Reasoning

When "Show Agent Reasoning" is enabled, you'll see:

### Execution Details:
- **Selected Tool**: Which tool was chosen
- **Tools Used**: All tools executed (if multiple)
- **Execution Phase**: Current stage (understanding, routing, executing, synthesizing)
- **Iterations**: Number of processing steps

### Tool Results:
- ✅ Success indicator
- Tool name and execution time
- Any errors encountered

**Example:**
```
🔍 Agent Reasoning Process
├─ Selected Tool: calculator
├─ Tools Used: calculator
├─ Execution Phase: done
├─ Iterations: 1 / 3
└─ ✅ calculator (0.15s)
```

---

## 🧠 Understanding Memory Context

When "Show Memory Context" is enabled, you'll see:

### Conversation History:
```
Turn 1:
User: Calculate 5 * 5
Assistant: Result: 25

Turn 2:
User: Double that
Assistant: Result: 50
```

### Session Stats:
- **Turn Count**: Number of back-and-forth exchanges
- **Messages**: Total messages in conversation
- **Session ID**: Unique identifier for this session

---

## 📈 Understanding Reflection Insights

When "Show Reflection Insights" is enabled, you'll see:

### Overall Performance:
- **Total Actions**: Number of tool executions
- **Success Rate**: Percentage of successful operations
- **Avg Quality**: Average answer quality score (1-5)
- **Tools**: Number of unique tools used

### Tool Performance Rankings:
Visual progress bars showing which tools perform best:
```
calculator         ████████████ 12.0
document_search    ████████     8.0
web_search         ████         4.0
```

### Recent Insights:
Latest learnings from reflection:
- "Tool 'calculator' successfully handled query type"
- "High-quality answer with good detail"
- "Answer grounded in 3 source(s)"

---

## 🔄 Session Management

### During Session:
- Agent maintains conversation memory
- Learns from each interaction
- Updates performance statistics

### End Session:
Click "🏁 End Session & Save" to:
1. Finalize current session
2. Save summary to episodic memory
3. Generate session report

### Session Summary:
```json
{
  "session_stats": {
    "session_id": "abc123...",
    "turn_count": 5,
    "total_messages": 10,
    "duration": 45.7
  },
  "performance": {
    "total_actions": 5,
    "success_rate": 1.0
  },
  "learning": {
    "query_types_learned": 3,
    "avg_quality_score": 4.2
  }
}
```

---

## 🆚 Comparison: Basic UI vs Agent UI

| Feature | Basic UI (`run_ui.py`) | Agent UI (`run_agent_ui.py`) |
|---------|------------------------|------------------------------|
| **Interface** | Simple Q&A | Multi-tool agent |
| **Memory** | ❌ None | ✅ Conversation + Episodic |
| **Learning** | ❌ None | ✅ Self-reflection & improvement |
| **Tools** | Document search only | 6 specialized tools |
| **Context** | ❌ No context awareness | ✅ Remembers conversation |
| **Routing** | N/A | ✅ Intelligent tool selection |
| **Insights** | ❌ None | ✅ Performance metrics |
| **Best For** | Simple document Q&A | Complex, multi-turn conversations |

---

## 🐛 Troubleshooting

### Agent Not Responding
- Check if agent initialized successfully (look for error messages)
- Try "Reset System" button in sidebar
- Check console for detailed error logs

### Memory Not Working
- Ensure "Enable Memory" is checked
- Check `data/episodic_memory/` directory exists
- Verify write permissions

### Tools Failing
- **Web Search**: Requires `ddgs` package installed
- **Code Executor**: Check Python sandbox is working
- **File Operations**: Check workspace directory permissions

### Slow Performance
- Disable "Show Agent Reasoning" for faster responses
- Reduce `CONVERSATION_MEMORY_MAX_MESSAGES` in config
- Use faster LLM model (e.g., llama-3.1-8b-instant)

---

## 💾 Data Storage

### Episodic Memory:
- **Location**: `data/episodic_memory/`
- **Format**: JSON files (one per session)
- **Filename**: `{session_id}.json`

### Vector Store:
- **Location**: `data/vector_store/`
- **Format**: FAISS index
- **Rebuilding**: Use document management features in sidebar

---

## 🎯 Best Practices

### For Best Results:
1. **Enable Memory** for multi-turn conversations
2. **Enable Reflection** to let agent learn and improve
3. **Use "Show Agent Reasoning"** to understand decisions
4. **End Session** after important conversations to save learnings

### Query Tips:
- Be specific: "Calculate the square root of 144"
- Use context: "Double that" (with memory enabled)
- Ask follow-ups: "Tell me more about that concept"
- Try different tools: The agent will choose the best one

### Performance Tips:
- Clear chat periodically for cleaner interface
- End sessions to save memory and start fresh
- Monitor success rate to understand agent performance

---

## 🚀 Advanced Usage

### Chaining Operations:
```
You: Calculate 15% of 2000
Agent: Result: 300

You: Write Python code to compound that value over 5 years at 7% annual growth
Agent: [Executes code] Final value after 5 years: $420.76
```

### Multi-Tool Queries:
```
You: Search the documents for information about RAG, then summarize it
Agent: [Uses document_search] RAG stands for Retrieval-Augmented Generation...
```

### Learning Over Time:
The agent gets better at routing queries as you use it more. After 10-20 queries, it will learn patterns and make smarter tool choices automatically.

---

## 📚 Additional Resources

- [Phase 3 Complete Documentation](PHASE3_COMPLETE.md)
- [Phase 3 Design Document](PHASE3_DESIGN.md)
- [Project Overview](PROJECT_OVERVIEW.md)
- [Main README](README.md)

---

## 🎉 Enjoy Your Intelligent Agent!

The Phase 3 agent brings your RAG system to life with memory, learning, and intelligent multi-tool capabilities. Explore, experiment, and watch it learn and improve over time!

**Happy Chatting!** 🤖
