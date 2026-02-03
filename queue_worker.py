"""
Task queue worker entry point.

Usage:
    python queue_worker.py

This starts a worker process that consumes tasks from the Redis queue
and executes them using the agent.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.queue import TaskWorker, get_task_queue
from src.agent.agent_executor_v3 import AgentExecutorV3
from src.agent.tool_registry import ToolRegistry
from src.config import Config


def main():
    """Start the task worker."""
    print("=" * 80)
    print("Task Queue Worker")
    print("=" * 80)

    # Check if Redis is enabled
    use_redis = os.getenv('USE_REDIS_QUEUE', 'false').lower() == 'true'

    if not use_redis:
        print("❌ Redis queue is disabled")
        print("💡 Set USE_REDIS_QUEUE=true in .env to enable")
        sys.exit(1)

    # Initialize config
    print("\n📝 Initializing configuration...")
    config = Config()

    # Initialize LLM
    print("🤖 Initializing LLM...")
    from langchain_groq import ChatGroq

    llm = ChatGroq(
        model=config.LLM_MODEL,
        temperature=config.TEMPERATURE,
        groq_api_key=os.getenv('GROQ_API_KEY')
    )

    # Initialize tool registry
    print("🛠️  Initializing tools...")
    tool_registry = ToolRegistry(config=config)

    # Initialize agent executor
    print("🧠 Initializing agent executor...")
    agent_executor = AgentExecutorV3(
        llm=llm,
        tool_registry=tool_registry,
        config=config
    )

    # Get task queue
    print("📦 Connecting to task queue...")
    task_queue = get_task_queue()

    if not task_queue.is_available():
        print("❌ Task queue not available")
        print("💡 Check Redis connection in .env")
        sys.exit(1)

    # Create worker
    print("👷 Creating worker...")
    worker = TaskWorker(
        task_queue=task_queue,
        agent_executor=agent_executor
    )

    # Start worker
    print("\n" + "=" * 80)
    worker.start()


if __name__ == "__main__":
    main()
