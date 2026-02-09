# OpenTelemetry Observability Guide

This guide explains how to enable and use OpenTelemetry observability for monitoring, tracing, and metrics in your RAG system.

---

## 🎯 Why Observability?

### Without Observability
- ❌ **No visibility** - Can't see what's happening inside your system
- ❌ **Debugging is hard** - Guessing where problems occur
- ❌ **No performance insights** - Don't know which operations are slow
- ❌ **No error tracking** - Errors disappear without a trace
- ❌ **No user insights** - Can't see usage patterns

### With OpenTelemetry Observability
- ✅ **Full visibility** - See every operation with distributed tracing
- ✅ **Easy debugging** - Trace requests from start to finish
- ✅ **Performance monitoring** - Track latency, throughput, and bottlenecks
- ✅ **Error tracking** - Capture and analyze all errors
- ✅ **Usage analytics** - Understand how users interact with your system
- ✅ **Proactive alerts** - Get notified before users complain

**When to enable:**
- Production deployment
- Performance optimization
- Debugging complex issues
- Usage analytics
- SLA monitoring

---

## 📋 Prerequisites

1. **Python packages** - OpenTelemetry libraries
2. **Observability backend** (optional) - Jaeger, Honeycomb, DataDog, etc.
3. **Basic understanding** - Traces, spans, and metrics

---

## ⚙️ Step 1: Install Dependencies

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-exporter-jaeger
```

Or update from requirements.txt:

```bash
pip install -r requirements.txt
```

---

## 🔧 Step 2: Configure Observability

### 1. Update .env

Add to your `.env` file:

```bash
# Enable Observability
ENABLE_OBSERVABILITY=true

# Service Configuration
OTEL_SERVICE_NAME=rag-agent
OTEL_ENVIRONMENT=development  # development, staging, production

# Exporter Configuration
OTEL_EXPORTER_TYPE=console  # console, otlp, jaeger

# For OTLP exporters (Jaeger, Honeycomb, DataDog, etc.)
# OTEL_EXPORTER_ENDPOINT=http://localhost:4317
# OTEL_EXPORTER_HEADERS=  # Optional: x-honeycomb-team=YOUR_API_KEY

# For Jaeger exporter
# JAEGER_HOST=localhost
# JAEGER_PORT=6831

# Tracing Options
TRACE_RAG_OPERATIONS=true
TRACE_AGENT_OPERATIONS=true
TRACE_TOOL_CALLS=true
TRACE_LLM_CALLS=true

# Metrics Options
COLLECT_METRICS=true
METRIC_EXPORT_INTERVAL=60  # seconds
```

### 2. Choose Exporter Type

**Console Exporter** (Development)
```bash
OTEL_EXPORTER_TYPE=console
```
- Outputs traces and metrics to console
- Good for development and debugging
- No additional setup needed

**OTLP Exporter** (Production)
```bash
OTEL_EXPORTER_TYPE=otlp
OTEL_EXPORTER_ENDPOINT=http://localhost:4317
```
- Sends data to OTLP-compatible backends
- Works with: Jaeger, Honeycomb, DataDog, Grafana Tempo, etc.
- Most flexible option

**Jaeger Exporter** (Direct to Jaeger)
```bash
OTEL_EXPORTER_TYPE=jaeger
JAEGER_HOST=localhost
JAEGER_PORT=6831
```
- Direct integration with Jaeger
- Good for self-hosted Jaeger installations

---

## 🚀 Step 3: Choose Observability Backend

### Option 1: Jaeger (Self-Hosted)

**Quick Start with Docker:**

```bash
# Start Jaeger all-in-one
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest

# Access UI: http://localhost:16686
```

**Configure:**
```bash
ENABLE_OBSERVABILITY=true
OTEL_EXPORTER_TYPE=otlp
OTEL_EXPORTER_ENDPOINT=http://localhost:4317
```

**Benefits:**
- ✅ Free and open source
- ✅ Full control over data
- ✅ No external dependencies
- ✅ Great UI for trace visualization

### Option 2: Honeycomb (Cloud SaaS)

**Sign up:** [https://honeycomb.io](https://honeycomb.io)

**Configure:**
```bash
ENABLE_OBSERVABILITY=true
OTEL_EXPORTER_TYPE=otlp
OTEL_EXPORTER_ENDPOINT=https://api.honeycomb.io:443
OTEL_EXPORTER_HEADERS=x-honeycomb-team=YOUR_API_KEY
```

**Benefits:**
- ✅ No infrastructure to maintain
- ✅ Advanced querying and visualization
- ✅ Generous free tier
- ✅ Excellent for production

### Option 3: DataDog (Enterprise)

**Sign up:** [https://www.datadoghq.com](https://www.datadoghq.com)

**Configure:**
```bash
ENABLE_OBSERVABILITY=true
OTEL_EXPORTER_TYPE=otlp
OTEL_EXPORTER_ENDPOINT=http://localhost:4317
# Install DataDog agent locally
```

**Benefits:**
- ✅ Full APM solution
- ✅ Advanced alerting
- ✅ Log correlation
- ✅ Enterprise features

### Option 4: Grafana Cloud (Hybrid)

**Sign up:** [https://grafana.com/products/cloud/](https://grafana.com/products/cloud/)

**Configure:**
```bash
ENABLE_OBSERVABILITY=true
OTEL_EXPORTER_TYPE=otlp
OTEL_EXPORTER_ENDPOINT=https://otlp-gateway-prod-us-central-0.grafana.net/otlp
OTEL_EXPORTER_HEADERS=Authorization=Basic YOUR_TOKEN
```

**Benefits:**
- ✅ Includes Tempo (traces), Loki (logs), Mimir (metrics)
- ✅ Powerful Grafana dashboards
- ✅ Free tier available

---

## 📊 Step 4: Run Your Application

```bash
# Start your application
streamlit run main_v3.py

# With observability enabled, you'll see:
🔭 OpenTelemetry initialized: rag-agent
   Environment: development
   Exporter: console
```

---

## 🔍 What Gets Traced?

### RAG Operations

**1. Query Processing** (`rag_query`)
- **Duration:** Total time for end-to-end RAG pipeline
- **Attributes:**
  - `query` - First 100 characters of the question
  - `llm` - LLM provider and model
  - `vector_store` - FAISS or Pinecone
  - `num_sources` - Number of documents retrieved
  - `answer_length` - Length of generated answer

**2. Context Retrieval** (`retrieve_context`)
- **Duration:** Time to retrieve relevant documents
- **Attributes:**
  - `query` - Search query
  - `top_k` - Number of documents requested
  - `vector_store` - Backend used
  - `documents_retrieved` - Actual number retrieved
  - `avg_score` - Average relevance score

**3. Answer Generation** (`generate_answer`)
- **Duration:** Time for LLM to generate response
- **Attributes:**
  - `query` - User question
  - `context_length` - Size of context provided
  - `llm` - LLM provider
  - `answer_length` - Response length

### Agent Operations

**1. Tool Execution** (`agent_tool_execution`)
- **Duration:** Time to execute agent tool
- **Attributes:**
  - `tool_name` - Name of tool executed
  - `query` - User request
  - `iteration` - Agent iteration number
  - `success` - Whether tool succeeded

### Metrics Collected

**Counters:**
- `rag.queries.total` - Total queries processed
- `rag.documents.indexed` - Documents indexed
- `rag.errors.total` - Total errors
- `rag.agent.actions.total` - Agent actions executed

**Histograms (Latency):**
- `rag.query.duration` - End-to-end query latency
- `rag.retrieval.duration` - Document retrieval latency
- `rag.generation.duration` - Answer generation latency
- `rag.agent.action.duration` - Agent action latency

**Gauges:**
- `rag.queries.active` - Currently active queries

---

## 📈 Visualizing Traces

### Jaeger UI

1. Open [http://localhost:16686](http://localhost:16686)
2. Select service: `rag-agent`
3. Click "Find Traces"

**Example Trace:**
```
rag_query (500ms)
├── retrieve_context (200ms)
│   └── similarity_search (180ms)
└── generate_answer (280ms)
    └── llm_invoke (270ms)
```

**What you can see:**
- Total latency breakdown
- Which operations are slow
- Error locations with stack traces
- Request attributes and metadata

### Honeycomb UI

1. Go to Honeycomb dashboard
2. Select dataset: `rag-agent`
3. Query: `duration_ms > 1000` to find slow requests

**Advanced Queries:**
```sql
-- Find slow RAG queries
WHERE name = "rag_query" AND duration_ms > 1000

-- Find errors
WHERE status_code = "ERROR"

-- Find queries with low retrieval
WHERE documents_retrieved < 3

-- Agent tool performance
WHERE name = "agent_tool_execution"
GROUP BY tool_name
CALC AVG(duration_ms)
```

---

## 🚨 Setting Up Alerts

### Honeycomb Alerts

```yaml
# Alert: Slow RAG Queries
trigger:
  query: WHERE name = "rag_query" AND duration_ms > 2000
  frequency: 5 minutes
  threshold: 10 requests
action:
  notify: slack, email
```

### DataDog Monitors

```yaml
# Monitor: Error Rate
metric: rag.errors.total
threshold: > 10 errors/minute
severity: high
notify: pagerduty
```

### Grafana Alerts

```promql
# Alert: High Latency
rate(rag_query_duration_sum[5m]) / rate(rag_query_duration_count[5m]) > 2000
```

---

## 🔧 Advanced Usage

### Custom Instrumentation

**Decorator Approach:**

```python
from src.observability import traced, measured, instrumented

# Trace function calls
@traced("my_custom_operation")
def process_data(data):
    return data.upper()

# Measure latency
@measured("custom_metric")
def slow_operation():
    time.sleep(1)
    return "done"

# Both tracing and metrics
@instrumented("important_operation", "operation")
def critical_function():
    return "result"
```

**Context Manager Approach:**

```python
from src.observability import get_observability

observability = get_observability()

# Manual tracing
with observability.trace_operation("custom_work", {"user": "john"}) as span:
    # Do work
    result = perform_work()

    # Add dynamic attributes
    span.set_attribute("result_size", len(result))

# Manual metrics
observability.record_metric("custom_metric", value=123, attributes={"type": "test"})
```

### Adding Custom Attributes

```python
# In your code
with observability.trace_operation("process_documents") as span:
    for doc in documents:
        process(doc)

    # Add custom attributes
    if span:
        span.set_attribute("documents_processed", len(documents))
        span.set_attribute("total_size", sum(len(d) for d in documents))
```

### Error Tracking

```python
with observability.trace_operation("risky_operation", record_exception=True) as span:
    try:
        dangerous_work()
    except Exception as e:
        # Exception automatically recorded in span
        # Also record metric
        observability.record_metric("error", 0, {"error_type": type(e).__name__})
        raise
```

---

## 📊 Example Dashboards

### Grafana Dashboard Example

```json
{
  "dashboard": {
    "title": "RAG System Overview",
    "panels": [
      {
        "title": "Query Latency",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(rag_query_duration_bucket[5m]))",
          "legendFormat": "p95"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "rate(rag_errors_total[5m])",
          "legendFormat": "errors/s"
        }]
      },
      {
        "title": "Throughput",
        "targets": [{
          "expr": "rate(rag_queries_total[5m])",
          "legendFormat": "queries/s"
        }]
      }
    ]
  }
}
```

---

## 🧪 Testing Observability

### 1. Test Console Output

```bash
# Enable console exporter
ENABLE_OBSERVABILITY=true
OTEL_EXPORTER_TYPE=console

# Run application
streamlit run main_v3.py

# You should see trace output in console:
{
  "name": "rag_query",
  "kind": "INTERNAL",
  "attributes": {
    "query": "What is machine learning?",
    "llm": "Groq (llama-3.3-70b-versatile)"
  },
  "status": {
    "status_code": "OK"
  }
}
```

### 2. Test with Sample Query

```python
# test_observability.py
from src.rag_chain import RAGChain
from src.document_manager import get_document_manager
from src.config import Config

# Enable observability
Config.ENABLE_OBSERVABILITY = True

# Create RAG chain
doc_manager = get_document_manager()
rag_chain = RAGChain(doc_manager)

# Run query (will generate traces)
result = rag_chain.ask("What is machine learning?")

print(f"Answer: {result['answer']}")
# Check Jaeger UI for traces
```

---

## 🔒 Security & Privacy

### 1. Sensitive Data

**By default, we truncate sensitive data:**

```python
# Only first 100 chars of queries
span.set_attribute("query", query[:100])

# Only first 100 chars of errors
span.set_attribute("error", str(e)[:100])
```

**Disable query logging:**

```python
# In config
TRACE_SENSITIVE_DATA = False
```

### 2. Production Considerations

**Sampling:**
```python
# Sample only 10% of traces in production
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1
```

**Filtering:**
```python
# Filter out health check traces
# Custom processor in observability.py
```

---

## 💰 Cost Estimation

### Honeycomb Pricing (2026)

| Traces/Month | Storage | Cost/Month |
|--------------|---------|------------|
| 100K | 2 weeks | Free |
| 1M | 30 days | ~$50 |
| 10M | 30 days | ~$200 |

### DataDog Pricing

| Spans/Month | Logs | Cost/Month |
|-------------|------|------------|
| 1M | 1GB | ~$100 |
| 10M | 10GB | ~$500 |

### Self-Hosted (Jaeger)

**Infrastructure costs only:**
- Small: $20/month (2GB RAM, 1 CPU)
- Medium: $50/month (4GB RAM, 2 CPU)
- Large: $100/month (8GB RAM, 4 CPU)

---

## 🆘 Troubleshooting

### Traces not appearing

**Issue:** No traces in backend

**Solutions:**
1. Check configuration:
   ```bash
   echo $ENABLE_OBSERVABILITY  # Should be "true"
   echo $OTEL_EXPORTER_TYPE    # Should match your backend
   ```

2. Test console exporter first:
   ```bash
   OTEL_EXPORTER_TYPE=console streamlit run main_v3.py
   ```

3. Check backend connectivity:
   ```bash
   # For OTLP
   curl http://localhost:4317

   # For Jaeger UI
   curl http://localhost:16686
   ```

### High overhead

**Issue:** Application is slow with observability enabled

**Solutions:**
1. Enable sampling:
   ```bash
   OTEL_TRACES_SAMPLER=parentbased_traceidratio
   OTEL_TRACES_SAMPLER_ARG=0.1  # Sample 10%
   ```

2. Reduce metric export frequency:
   ```bash
   METRIC_EXPORT_INTERVAL=300  # Export every 5 minutes
   ```

3. Disable specific tracing:
   ```bash
   TRACE_LLM_CALLS=false  # Most expensive operations
   ```

### Missing metrics

**Issue:** Traces work but metrics don't appear

**Solutions:**
1. Wait for export interval (default 60s)
2. Check metric exporter configuration
3. Verify backend supports metrics (Jaeger needs OTLP)

---

## 📚 Additional Resources

- **OpenTelemetry Docs:** [https://opentelemetry.io/docs/](https://opentelemetry.io/docs/)
- **Jaeger Docs:** [https://www.jaegertracing.io/docs/](https://www.jaegertracing.io/docs/)
- **Honeycomb Docs:** [https://docs.honeycomb.io/](https://docs.honeycomb.io/)
- **Observability Guide:** [src/observability.py](src/observability.py)
- **Configuration:** [src/config.py](src/config.py)

---

## 🎓 Best Practices

1. **Start Simple:** Begin with console exporter, then move to cloud
2. **Use Sampling:** Don't trace 100% in production
3. **Set Alerts:** Monitor error rates and latency
4. **Review Regularly:** Check traces weekly to find issues
5. **Clean Up:** Delete old data to control costs
6. **Correlate:** Link traces with logs and metrics
7. **Document:** Add span attributes to make traces searchable

---

*Last updated: 2026-02-03*
