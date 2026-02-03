# Redis Message Queue Guide

This guide explains how to use Redis Message Queue for distributed agent coordination and async task processing.

---

## 🎯 What is the Redis Message Queue?

The **Redis Message Queue** enables distributed, asynchronous execution of agent tasks. It provides:

- ✅ **Async Execution** - Submit tasks for background processing
- ✅ **Priority Queues** - LOW, NORMAL, HIGH, URGENT task prioritization
- ✅ **Worker Pool** - Multiple workers for parallel execution
- ✅ **Task Tracking** - Real-time status monitoring
- ✅ **Auto Retry** - Configurable retry logic for failures
- ✅ **Task Scheduling** - Schedule tasks for future execution
- ✅ **Queue Stats** - Monitor performance and throughput
- ✅ **Pub/Sub Events** - Real-time task notifications

---

## 📋 Prerequisites

1. **Redis Server** - Running Redis instance
2. **Python Packages** - Redis client installed
3. **Configuration** - Environment variables configured

---

## ⚙️ Configuration

### Install Redis

**Mac (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
```

**Docker:**
```bash
docker run --name redis -p 6379:6379 -d redis:7-alpine
```

### Install Dependencies

```bash
pip install redis>=5.0.0
```

### Enable Message Queue

Edit `.env`:
```bash
# Enable Redis queue
USE_REDIS_QUEUE=true

# Redis connection
REDIS_URL=redis://localhost:6379/0
# Or with password:
# REDIS_URL=redis://:password@localhost:6379/0

# Or individual parameters:
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_DB=0
# REDIS_PASSWORD=
```

---

## 🚀 Quick Start

### 1. Start Redis

```bash
redis-server
# Or with Docker:
docker start redis
```

### 2. Start Worker

Open a terminal and run:

```bash
python queue_worker.py
```

Output:
```
================================================================================
Task Queue Worker
================================================================================

📝 Initializing configuration...
🤖 Initializing LLM...
🛠️  Initializing tools...
🧠 Initializing agent executor...
📦 Connecting to task queue...
✅ Redis task queue initialized
👷 Creating worker...

================================================================================
🚀 Worker worker-a1b2c3d4 starting...
✅ Worker worker-a1b2c3d4 ready
```

### 3. Submit Tasks

In Python:

```python
from src.agent.agent_executor_v3 import AgentExecutorV3

# Initialize agent
agent = AgentExecutorV3(llm, tool_registry, config)

# Submit async task
task_id = agent.execute_async(
    query="What is machine learning?",
    priority="normal"
)

print(f"Task submitted: {task_id}")

# Check status
status = agent.get_task_status(task_id)
print(f"Status: {status['status']}")  # pending, running, completed

# Get result (when completed)
result = agent.get_task_result(task_id)
if result:
    print(f"Answer: {result['result']['answer']}")
```

---

## 📦 Task Types

### 1. Agent Query (Default)

Execute agent with a query:

```python
task_id = agent.execute_async(
    query="Explain quantum computing",
    session_id="user-123",
    priority="high"
)
```

### 2. Batch Queries

Process multiple queries:

```python
from src.queue import Task, TaskType, TaskPriority, get_task_queue

task = Task(
    task_type=TaskType.BATCH_QUERY,
    payload={
        'queries': [
            "What is AI?",
            "What is ML?",
            "What is DL?"
        ]
    },
    priority=TaskPriority.NORMAL
)

task_queue = get_task_queue()
task_id = task_queue.submit_task(task)
```

### 3. Scheduled Tasks

Execute tasks at a specific time:

```python
from src.queue import TaskScheduler, AgentTask
from datetime import datetime, timedelta

scheduler = TaskScheduler()

task = AgentTask(
    payload={'query': "Daily news summary"}
)

# Schedule for 9 AM tomorrow
execute_time = datetime.now().replace(hour=9, minute=0) + timedelta(days=1)
task_id = scheduler.schedule_task(task, execute_time)

# Or schedule with delay
task_id = scheduler.schedule_task_in(task, delay_seconds=3600)  # 1 hour
```

---

## ⚡ Priority Levels

Tasks are processed in priority order:

| Priority | Value | Use Case |
|----------|-------|----------|
| **URGENT** | 15 | Critical operations, system alerts |
| **HIGH** | 10 | Important user requests, paid tier |
| **NORMAL** | 5 | Regular user requests (default) |
| **LOW** | 0 | Background tasks, maintenance |

```python
# Submit with priority
task_id = agent.execute_async(
    query="Fix critical bug",
    priority="urgent"  # Processed first
)
```

---

## 👷 Worker Management

### Start Multiple Workers

For parallel processing, run multiple workers:

**Terminal 1:**
```bash
python queue_worker.py
# Worker worker-a1b2c3d4 ready
```

**Terminal 2:**
```bash
python queue_worker.py
# Worker worker-x9y8z7w6 ready
```

**Terminal 3:**
```bash
python queue_worker.py
# Worker worker-m5n4o3p2 ready
```

Now you have 3 workers processing tasks in parallel!

### Worker Features

- **Auto Heartbeat** - Workers send heartbeat every 30s
- **Graceful Shutdown** - Ctrl+C stops worker after current task
- **Task Stats** - Shows tasks processed on shutdown
- **Auto Reconnect** - Reconnects to Redis if connection lost

---

## 📊 Task Monitoring

### Check Task Status

```python
task_id = agent.execute_async("Query...")

# Check status
status = agent.get_task_status(task_id)

print(status)
# {
#     'task_id': 'abc123...',
#     'status': 'running',
#     'created_at': '2026-02-03T14:23:45',
#     'started_at': '2026-02-03T14:23:48',
#     'worker_id': 'worker-a1b2c3d4'
# }
```

### Get Task Result

```python
# Wait for completion
import time

while True:
    status = agent.get_task_status(task_id)
    if status['status'] in ['completed', 'failed']:
        break
    time.sleep(1)

# Get result
result = agent.get_task_result(task_id)

if result['status'] == 'completed':
    print(f"Answer: {result['result']['answer']}")
    print(f"Duration: {result['duration']:.2f}s")
else:
    print(f"Error: {result['error']}")
```

### Queue Statistics

```python
from src.queue import get_task_queue

task_queue = get_task_queue()
stats = task_queue.get_queue_stats()

print(f"Pending: {stats.pending_tasks}")
print(f"Running: {stats.running_tasks}")
print(f"Completed: {stats.completed_tasks}")
print(f"Failed: {stats.failed_tasks}")
print(f"Workers: {stats.active_workers}")
print(f"Success Rate: {stats.success_rate * 100:.1f}%")
```

---

## 🔁 Retry Logic

Failed tasks are automatically retried:

```python
from src.queue import AgentTask

task = AgentTask(
    payload={'query': "Complex query"},
    max_retries=3,        # Retry up to 3 times
    retry_delay=60        # Wait 60s between retries
)

task_id = task_queue.submit_task(task)
```

**Retry Behavior:**
1. Task fails → Status: FAILED
2. If retry_count < max_retries → Status: RETRY
3. Task resubmitted to queue
4. Worker picks up retry
5. After max retries → Status: FAILED (permanent)

---

## 📈 UI Integration

### Sidebar Dashboard

Add to your Streamlit app:

```python
from src.ui.components import render_task_queue_dashboard

# In sidebar
render_task_queue_dashboard()
```

Shows:
- Pending, Running, Completed, Failed counts
- Active workers
- Success rate

### Full Task Monitor

```python
from src.ui.components import render_task_monitor

# In main content
render_task_monitor(agent_executor)
```

Features:
- Submit tasks with priority
- View task list with filters
- Real-time status updates
- Task result viewing

---

## 🔍 Advanced Usage

### Custom Task Handlers

Add custom task types:

```python
from src.queue import TaskWorker, TaskType

def custom_handler(task):
    """Custom task handler."""
    data = task.payload.get('data')
    # Process data...
    return {'processed': True}

# Register handler
worker = TaskWorker()
worker.register_handler(TaskType.CUSTOM, custom_handler)
worker.start()
```

### Task Events (Pub/Sub)

Subscribe to task events:

```python
from src.queue import get_task_queue

task_queue = get_task_queue()

def event_callback(message):
    event = json.loads(message['data'])
    print(f"Event: {event['type']}")
    print(f"Data: {event['data']}")

task_queue.subscribe_to_events(event_callback)
```

Events:
- `task.submitted` - Task added to queue
- `task.status_changed` - Status updated
- `task.completed` - Task finished

### Scheduled Task Monitoring

Run scheduler in background:

```python
from src.queue import TaskScheduler

scheduler = TaskScheduler()

# Start scheduler loop (blocking)
scheduler.run_scheduler_loop(check_interval=10)  # Check every 10s
```

Or in a separate process:

```python
# schedule_worker.py
from src.queue import TaskScheduler

scheduler = TaskScheduler()
scheduler.run_scheduler_loop()
```

Then run:
```bash
python schedule_worker.py &
```

---

## 🔧 Redis Commands

Useful Redis commands for debugging:

```bash
# Connect to Redis
redis-cli

# Check queue length
LLEN agent_queue:queue:normal
LLEN agent_queue:queue:high

# View pending tasks
SMEMBERS agent_queue:status:pending

# View running tasks
SMEMBERS agent_queue:status:running

# Get task data
GET agent_queue:task:abc123...

# Get result
GET agent_queue:result:abc123...

# Active workers
SMEMBERS agent_queue:workers

# Clear all queues (DANGEROUS!)
FLUSHDB
```

---

## 💡 Production Deployment

### Use Redis Cluster

For high availability:

```bash
# Connect to Redis cluster
REDIS_URL=redis://redis-cluster:6379/0
```

### Monitor with Redis Insights

Install Redis Insights for visual monitoring:
```bash
# Download from: https://redis.com/redis-enterprise/redis-insight/
```

### Set Resource Limits

Limit memory usage:

```bash
# In redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### Scale Workers

Run workers on multiple machines:

```bash
# Machine 1
REDIS_URL=redis://redis-server:6379/0 python queue_worker.py

# Machine 2
REDIS_URL=redis://redis-server:6379/0 python queue_worker.py

# Machine 3
REDIS_URL=redis://redis-server:6379/0 python queue_worker.py
```

---

## 🆘 Troubleshooting

### Redis Connection Failed

```
Error: Connection refused
```

**Solution:**
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Start Redis
redis-server

# Or Docker
docker start redis
```

### Tasks Not Processing

```bash
# Check active workers
redis-cli
SMEMBERS agent_queue:workers

# Should show at least one worker
# If empty, start a worker:
python queue_worker.py
```

### Tasks Stuck in Pending

```bash
# Check queue lengths
redis-cli
LLEN agent_queue:queue:normal

# If tasks in queue but no workers:
python queue_worker.py
```

### Memory Issues

```bash
# Check Redis memory usage
redis-cli INFO memory

# Clear old results
redis-cli
KEYS agent_queue:result:*
# Manually delete old keys
```

---

## 📊 Performance Benchmarks

Typical performance with Redis Queue:

| Metric | Without Queue | With Queue (1 Worker) | With Queue (4 Workers) |
|--------|---------------|----------------------|------------------------|
| **Throughput** | 1 req/sec | 1 req/sec | 4 req/sec |
| **Latency** | Immediate | +100ms overhead | +100ms overhead |
| **Concurrency** | 1 | 1 | 4 |
| **Scalability** | Limited | Linear | Linear with workers |

**Benefits:**
- Async execution frees up main thread
- Priority handling for important tasks
- Automatic retries improve reliability
- Horizontal scaling with more workers

---

## 🎯 Use Cases

### 1. High-Volume API

Handle thousands of requests:

```python
# API endpoint
@app.post("/api/query")
async def query(request):
    task_id = agent.execute_async(
        query=request.query,
        priority="normal"
    )
    return {"task_id": task_id}

@app.get("/api/result/{task_id}")
async def get_result(task_id):
    result = agent.get_task_result(task_id)
    return result
```

### 2. Batch Processing

Process CSV of queries:

```python
import pandas as pd

df = pd.read_csv("queries.csv")

task_ids = []
for query in df['query']:
    task_id = agent.execute_async(query, priority="low")
    task_ids.append(task_id)

# Wait for all to complete
results = []
for task_id in task_ids:
    result = agent.get_task_result(task_id)
    results.append(result)

df['answer'] = [r['result']['answer'] for r in results]
df.to_csv("results.csv")
```

### 3. Scheduled Reports

Daily summary reports:

```python
from src.queue import TaskScheduler, AgentTask
from datetime import datetime, timedelta

scheduler = TaskScheduler()

# Schedule daily at 9 AM
task = AgentTask(
    payload={'query': "Generate daily analytics report"}
)

tomorrow_9am = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0)
scheduler.schedule_task(task, tomorrow_9am)
```

---

## 🔒 Security Considerations

### Redis Authentication

Enable password:

```bash
# In redis.conf
requirepass your-strong-password
```

```bash
# In .env
REDIS_URL=redis://:your-strong-password@localhost:6379/0
```

### Network Security

Bind to localhost only:

```bash
# In redis.conf
bind 127.0.0.1
protected-mode yes
```

### Task Data Encryption

Encrypt sensitive payloads:

```python
from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt before submitting
encrypted_query = cipher.encrypt(query.encode())

task_id = agent.execute_async(query=encrypted_query.decode())
```

---

## 📚 Additional Resources

- **Redis Documentation:** [https://redis.io/docs/](https://redis.io/docs/)
- **Redis Python Client:** [https://redis-py.readthedocs.io/](https://redis-py.readthedocs.io/)
- **Task Queue Code:** [src/queue/](src/queue/)
- **Worker Script:** [queue_worker.py](queue_worker.py)

---

*Last updated: 2026-02-03*
