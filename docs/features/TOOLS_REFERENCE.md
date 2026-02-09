# Tools Reference Documentation

## Overview

Tools extend the agent's capabilities beyond text generation. The system includes 10+ built-in tools for document search, web access, calculations, code execution, and more.

## Architecture

### Tool Interface

All tools extend `BaseTool`:

```python
class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier (e.g., 'web_search')"""

    @property
    @abstractmethod
    def description(self) -> str:
        """What the tool does - used by LLM for selection"""

    @abstractmethod
    def _run(self, *args, **kwargs) -> str:
        """Core execution logic"""

    def run(self, *args, **kwargs) -> ToolResult:
        """Execute with timing and error handling"""
```

### Tool Result

```python
class ToolResult:
    success: bool        # Did the tool execute successfully?
    output: str          # Tool output (empty if error)
    error: Optional[str] # Error message (if failed)
    duration: float      # Execution time in seconds
    metadata: dict       # Additional info (call_count, etc.)
```

## Built-in Tools

### 1. RAG Tool (Document Search)

**File**: [src/agent/tools/rag_tool.py](../src/agent/tools/rag_tool.py)

Search through indexed documents using vector similarity.

#### Properties

```python
name: "document_search"
description: "Search through indexed documents and knowledge base"
```

#### Parameters

```python
def _run(
    query: str,        # Search query
    top_k: int = 3     # Number of results to return
) -> str
```

#### Usage

```python
from src.agent.tools.rag_tool import RAGTool

tool = RAGTool(rag_chain)

result = tool.run(
    query="What is a transformer architecture?",
    top_k=5
)

if result.success:
    print(result.output)
    # Output:
    # Found 5 relevant documents:
    #
    # [Source 1: transformers.pdf (Score: 0.82)]
    # A transformer is a deep learning architecture...
    #
    # [Source 2: attention.pdf (Score: 0.79)]
    # ...
```

#### When to Use

- User asks about topics likely in your documents
- Need to provide context-grounded answers
- Want to cite sources for information

#### Example Queries

- "What does the document say about X?"
- "Find information about Y in the knowledge base"
- "Summarize the key points from document Z"

---

### 2. Web Search Tool

**File**: [src/agent/tools/web_search_tool.py](../src/agent/tools/web_search_tool.py)

Search the internet using DuckDuckGo for current information.

#### Properties

```python
name: "web_search"
description: "Search the web for current information and recent events"
```

#### Parameters

```python
def _run(
    query: str,              # Search query
    num_results: int = 3     # Number of results (1-20)
) -> str
```

#### Features

- **Rate Limiting**: Max 10 searches/minute
- **Timeout Protection**: 30 second timeout per search
- **Result Formatting**: Title, snippet, and URL

#### Usage

```python
from src.agent.tools.web_search_tool import WebSearchTool

tool = WebSearchTool(max_results=3, rate_limit_per_minute=10)

result = tool.run(query="latest news on AI breakthroughs")

# Output:
# Search Results for: latest news on AI breakthroughs
#
# 1. Title: Major AI Breakthrough Announced
#    Snippet: Researchers at... [first 200 chars]
#    URL: https://example.com/article
#
# 2. ...
```

#### When to Use

- Need current/recent information
- Topic not in document collection
- Real-time data (news, weather, stocks)
- User explicitly asks to "search the web"

#### Example Queries

- "What's the latest news on X?"
- "Current price of Y"
- "Recent developments in Z"

---

### 3. Web Agent Tool

**File**: [src/agent/tools/web_agent_tool.py](../src/agent/tools/web_agent_tool.py)

Fetch and extract full content from specific URLs.

#### Properties

```python
name: "web_agent"
description: "Fetch and extract content from specific URLs"
```

#### Parameters

```python
def _run(
    url: str,                # URL to fetch
    extract_links: bool = False,  # Also extract links
    max_length: int = 10000       # Max content length
) -> str
```

#### Features

- **Content Extraction**: Removes HTML, keeps text
- **Link Extraction**: Optional link discovery
- **Safety**: URL validation, timeout protection
- **Format Support**: HTML, plain text

#### Usage

```python
from src.agent.tools.web_agent_tool import WebAgentTool

tool = WebAgentTool()

result = tool.run(url="https://example.com/article")

# Output:
# Content from: https://example.com/article
# Title: Article Title
#
# [Main content extracted...]
#
# Links found: (if extract_links=True)
# - https://...
```

#### When to Use

- User provides specific URL
- Need full article content (not just snippet)
- Following up on web search results
- Extracting structured information from webpage

#### Difference from Web Search

| Web Search | Web Agent |
|-----------|-----------|
| Finds URLs matching query | Fetches specific URL |
| Returns snippets | Returns full content |
| Multiple results | Single page |
| For discovery | For deep reading |

---

### 4. Calculator Tool

**File**: [src/agent/tools/calculator_tool.py](../src/agent/tools/calculator_tool.py)

Perform mathematical calculations and evaluations.

#### Properties

```python
name: "calculator"
description: "Perform mathematical calculations and evaluations"
```

#### Parameters

```python
def _run(
    expression: str  # Math expression to evaluate
) -> str
```

#### Features

- **Safe Evaluation**: Uses `numexpr` for safety
- **Math Functions**: sin, cos, sqrt, log, exp, etc.
- **Constants**: pi, e
- **Operators**: +, -, *, /, **, %

#### Usage

```python
from src.agent.tools.calculator_tool import CalculatorTool

tool = CalculatorTool()

result = tool.run(expression="(123 + 456) * 2")
# Output: "Result: 1158"

result = tool.run(expression="sqrt(16) + log(100)")
# Output: "Result: 8.605..."

result = tool.run(expression="sin(pi/2)")
# Output: "Result: 1.0"
```

#### When to Use

- User asks for calculations
- Need to process numerical data
- Convert units or percentages
- Evaluate complex expressions

#### Example Queries

- "What is 15% of 250?"
- "Calculate the square root of 144"
- "What's (5 + 3) * 2 - 10?"

#### Security

- **Sandboxed**: Uses numexpr (no exec/eval)
- **No side effects**: Read-only operations
- **Timeout**: Prevents infinite loops

---

### 5. Code Executor Tool

**File**: [src/agent/tools/code_executor_tool.py](../src/agent/tools/code_executor_tool.py)

⚠️ **DISABLED BY DEFAULT for safety**

Execute Python code in a sandboxed environment.

#### Properties

```python
name: "code_executor"
description: "Execute Python code in a sandboxed environment"
```

#### Parameters

```python
def _run(
    code: str,           # Python code to execute
    timeout: int = 5     # Execution timeout (seconds)
) -> str
```

#### Features

- **Timeout Protection**: Kills after N seconds
- **Output Capture**: Returns stdout/stderr
- **Error Handling**: Returns exception messages
- **Basic Safety**: No file I/O, network access limited

#### Configuration

```bash
# In .env - DISABLED by default
CODE_EXECUTOR_ENABLED=false

# To enable (use with caution!):
CODE_EXECUTOR_ENABLED=true
CODE_EXECUTION_TIMEOUT=5
```

#### Usage

```python
# Only works if enabled in config
tool = CodeExecutorTool()

result = tool.run(code="""
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

for i in range(10):
    print(fibonacci(i))
""")

# Output:
# Execution Output:
# 0
# 1
# 1
# 2
# 3
# 5
# 8
# 13
# 21
# 34
```

#### When to Use (If Enabled)

- User explicitly requests code execution
- Demonstrating code examples
- Data processing tasks
- Algorithm demonstrations

#### Security Considerations

- **Disabled by default** for good reason
- Can't guarantee complete sandboxing
- Timeout doesn't prevent all resource abuse
- **Use only in trusted environments**

---

### 6. File Operations Tool

**File**: [src/agent/tools/file_ops_tool.py](../src/agent/tools/file_ops_tool.py)

Read and write files in sandboxed workspace.

#### Properties

```python
name: "file_operations"
description: "Read and write files in the workspace directory"
```

#### Parameters

```python
def _run(
    operation: str,      # "read", "write", "list"
    filepath: str = "",  # Relative path in workspace
    content: str = ""    # Content for write operations
) -> str
```

#### Features

- **Sandboxed**: Operations limited to `data/workspace/`
- **Path Validation**: Prevents directory traversal
- **Operations**: read, write, list
- **Safety**: No execution, no system files

#### Usage

```python
from src.agent.tools.file_ops_tool import FileOpsTool

tool = FileOpsTool()

# List files
result = tool.run(operation="list")
# Output: Files in workspace:\n- file1.txt\n- data.csv\n...

# Read file
result = tool.run(operation="read", filepath="notes.txt")
# Output: [content of notes.txt]

# Write file
result = tool.run(
    operation="write",
    filepath="output.txt",
    content="Hello, world!"
)
# Output: Successfully wrote to output.txt
```

#### When to Use

- User wants to save data
- Reading structured data files
- Creating output files
- Managing workspace files

#### Security

- **Workspace Only**: `data/workspace/` directory
- **Path Validation**: Blocks `..`, absolute paths
- **No Execution**: Only read/write, not execute
- **File Size Limits**: Prevents massive files

---

### 7. News API Tool

**File**: [src/agent/tools/news_api_tool.py](../src/agent/tools/news_api_tool.py)

Fetch recent news articles from NewsAPI.

#### Properties

```python
name: "news_api"
description: "Fetch recent news articles by topic or keyword"
```

#### Parameters

```python
def _run(
    query: str,          # Search query or topic
    num_results: int = 5  # Number of articles (1-20)
) -> str
```

#### Configuration

```bash
# In .env
NEWSAPI_KEY=your_newsapi_key_here

# Get free key at: https://newsapi.org/
```

#### Usage

```python
from src.agent.tools.news_api_tool import NewsAPITool

tool = NewsAPITool()

result = tool.run(query="artificial intelligence", num_results=3)

# Output:
# News Articles for: artificial intelligence
#
# 1. Title: AI Breakthrough in Healthcare
#    Source: TechCrunch
#    Published: 2026-02-04T10:00:00Z
#    Description: Researchers have developed...
#    URL: https://...
#
# 2. ...
```

#### When to Use

- User asks for "news"
- Recent events or developments
- Current headlines
- Specific news topics

#### Example Queries

- "What's the latest news on climate change?"
- "Show me tech news from today"
- "Recent articles about space exploration"

---

### 8. Document Management Tool

**File**: [src/agent/tools/doc_management_tool.py](../src/agent/tools/doc_management_tool.py)

Manage the document collection (list, stats, metadata).

#### Properties

```python
name: "document_management"
description: "Manage document collection: list, stats, metadata"
```

#### Parameters

```python
def _run(
    action: str,     # "list", "stats", "info"
    filename: str = ""  # For "info" action
) -> str
```

#### Usage

```python
from src.agent.tools.doc_management_tool import DocManagementTool

tool = DocManagementTool(vector_store_manager)

# List documents
result = tool.run(action="list")
# Output:
# Indexed Documents (42 total):
# 1. transformers.pdf (12 chunks)
# 2. ml_basics.pdf (8 chunks)
# ...

# Get stats
result = tool.run(action="stats")
# Output:
# Document Collection Statistics:
# - Total documents: 42
# - Total chunks: 156
# - Total tokens: ~124,800
# - Topics: ML (15), AI (12), ...

# Get file info
result = tool.run(action="info", filename="transformers.pdf")
# Output:
# Document: transformers.pdf
# - Chunks: 12
# - Topics: Deep Learning, Attention
# - Uploaded: 2026-02-01
# - Size: 2.3 MB
```

#### When to Use

- User asks "what documents do you have?"
- Need to verify document is indexed
- Show collection statistics
- Get metadata about specific document

---

### 9. Relevance Evaluator

**File**: [src/agent/tools/relevance_evaluator.py](../src/agent/tools/relevance_evaluator.py)

Evaluate if retrieved documents are relevant to the query.

#### Properties

```python
name: "relevance_evaluator"
description: "Evaluate relevance of documents to query"
```

#### Usage

Internal tool used by agent to assess retrieval quality.

```python
from src.agent.tools.relevance_evaluator import RelevanceEvaluator

evaluator = RelevanceEvaluator(llm)

score = evaluator.evaluate(
    query="What is machine learning?",
    documents=[doc1, doc2, doc3]
)

# Returns: {"relevance_score": 0.85, "relevant_docs": [doc1, doc3]}
```

#### When Used

- After RAG tool retrieval
- To filter low-quality results
- To decide if web search is needed
- Internal quality control

---

## Tool Selection

The agent selects tools based on:

1. **Tool Descriptions**: Matched to query intent
2. **Memory Context**: Past successful tool usage
3. **Query Type**: Factual, current, computational, etc.

### Selection Examples

| Query | Selected Tool | Reasoning |
|-------|--------------|-----------|
| "What's in the docs about X?" | `document_search` | Explicit document reference |
| "Latest news on Y" | `news_api` or `web_search` | "Latest" indicates current info |
| "Calculate 15% of 250" | `calculator` | Math expression |
| "What does example.com say?" | `web_agent` | Specific URL |
| "Search online for Z" | `web_search` | Explicit web request |

## Creating Custom Tools

### 1. Extend BaseTool

```python
from src.agent.tools.base_tool import BaseTool

class MyCustomTool(BaseTool):
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "my_custom_tool"

    @property
    def description(self) -> str:
        return "Clear description for LLM to understand when to use this tool"

    def _run(self, param1: str, param2: int = 10) -> str:
        """
        Core logic here.

        Args:
            param1: Description
            param2: Description (default: 10)

        Returns:
            String output
        """
        # Implement your logic
        result = self._do_something(param1, param2)

        # Return formatted string
        return f"Result: {result}"
```

### 2. Register Tool

```python
from src.agent.tool_registry import ToolRegistry

# Create registry
registry = ToolRegistry()

# Register your tool
registry.register(MyCustomTool(api_key="..."))

# Now available to agent
tool = registry.get_tool("my_custom_tool")
```

### 3. Best Practices

#### Clear Description

```python
# ❌ BAD
description: "Does stuff"

# ✅ GOOD
description: "Fetches real-time stock prices from Yahoo Finance API. Use this when user asks about current stock prices, market data, or financial quotes."
```

#### Type Hints

```python
def _run(
    self,
    symbol: str,      # Stock symbol (e.g., "AAPL")
    period: str = "1d"  # Time period: "1d", "1wk", "1mo"
) -> str:
```

#### Error Handling

```python
def _run(self, query: str) -> str:
    # Validate input
    if not query or len(query) > 500:
        return "Error: Invalid query"

    try:
        # Main logic
        result = self._api_call(query)

        # Format output
        return self._format_result(result)

    except APIError as e:
        return f"API Error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"
```

#### Return Formatting

```python
def _run(self, city: str) -> str:
    weather = self._get_weather(city)

    # Format for readability
    return f"""
Weather in {city}:
- Temperature: {weather['temp']}°F
- Conditions: {weather['description']}
- Humidity: {weather['humidity']}%
- Wind: {weather['wind_speed']} mph
""".strip()
```

## Tool Configuration

**Settings in `.env`**:

```bash
# Web Search
WEB_SEARCH_ENABLED=true
WEB_SEARCH_PROVIDER=duckduckgo  # or tavily
TAVILY_API_KEY=your_key_here    # Optional

# Calculator
CALCULATOR_ENABLED=true

# Code Executor (DISABLE in production!)
CODE_EXECUTOR_ENABLED=false
CODE_EXECUTION_TIMEOUT=5

# File Operations
FILE_OPS_ENABLED=true

# News API
NEWSAPI_KEY=your_newsapi_key
```

## Tool Performance

### Timing

```python
result = tool.run(query="...")

print(f"Execution time: {result.duration:.2f}s")
print(f"Call count: {result.metadata['call_count']}")
```

### Caching

For expensive operations, implement caching:

```python
from functools import lru_cache

class CachedTool(BaseTool):
    @lru_cache(maxsize=100)
    def _cached_operation(self, query: str) -> str:
        # Expensive operation
        return result

    def _run(self, query: str) -> str:
        return self._cached_operation(query)
```

## Troubleshooting

### Tool Not Being Selected

**Symptom**: Agent doesn't use the appropriate tool

**Solutions**:
1. Make description more explicit
2. Add example queries to description
3. Check if tool is registered
4. Enable verbose mode to see selection reasoning

### Tool Execution Fails

**Symptom**: Tool returns error

**Solutions**:
1. Check tool configuration (API keys, etc.)
2. Verify input parameters
3. Check rate limits
4. Review error message in `result.error`

### Slow Tool Execution

**Symptom**: Tool takes too long

**Solutions**:
1. Add timeout protection
2. Implement caching
3. Use async operations
4. Optimize API calls

## Advanced Topics

### Tool Composition

Chain multiple tools:

```python
# Example: Web search → Web agent → Summarize
search_results = web_search_tool.run(query)
first_url = extract_url(search_results.output)
content = web_agent_tool.run(url=first_url)
summary = summarize(content.output)
```

### Conditional Tool Selection

```python
# In agent routing logic
if "latest" in query or "recent" in query:
    selected_tool = "web_search"
elif any(doc_keyword in query for doc_keyword in ["document", "knowledge base"]):
    selected_tool = "document_search"
else:
    # Let LLM decide
    selected_tool = llm_select_tool(query, tool_descriptions)
```

### Tool Metrics

Track tool usage:

```python
# In SessionManager
tools_used = {'document_search': 5, 'web_search': 2, 'calculator': 1}

session_manager.update_session_stats(
    session_id=session_id,
    tools_used=tools_used
)
```

## Related Documentation

- [Agent System](../architecture/AGENT_SYSTEM.md) - Tool integration and routing
- [Configuration](../CONFIGURATION.md) - Tool settings
- [RAG Core](../architecture/RAG_CORE.md) - RAG Tool details
