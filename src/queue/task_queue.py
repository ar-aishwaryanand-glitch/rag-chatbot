"""
Redis-based task queue for distributed agent coordination.

Features:
- Priority-based task queuing
- Task status tracking
- Result caching
- Dead letter queue for failed tasks
- Pub/sub for real-time updates
"""

import os
import json
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

try:
    import redis
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .task_models import (
    Task,
    TaskStatus,
    TaskPriority,
    TaskResult,
    QueueStats,
    AgentTask
)


class TaskQueue:
    """
    Redis-based task queue manager.

    Features:
    - Priority queues (LOW, NORMAL, HIGH, URGENT)
    - Task status tracking
    - Result caching
    - Pub/sub notifications
    - Dead letter queue
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        queue_prefix: str = "agent_queue",
        result_ttl: int = 3600  # 1 hour
    ):
        """
        Initialize task queue.

        Args:
            redis_url: Redis connection URL
            queue_prefix: Prefix for queue keys
            result_ttl: TTL for cached results (seconds)
        """
        if not REDIS_AVAILABLE:
            raise ImportError("redis package not installed. Run: pip install redis")

        self.redis_url = redis_url or self._get_redis_url()
        self.queue_prefix = queue_prefix
        self.result_ttl = result_ttl
        self.enabled = self._check_enabled()

        self.redis_client: Optional[Redis] = None
        self.pubsub = None

        if self.enabled:
            self._initialize_redis()

    def _check_enabled(self) -> bool:
        """Check if Redis queue is enabled."""
        return os.getenv('USE_REDIS_QUEUE', 'false').lower() == 'true'

    def _get_redis_url(self) -> str:
        """Get Redis connection URL from environment."""
        redis_url = os.getenv('REDIS_URL')

        if redis_url:
            return redis_url

        # Build from components
        host = os.getenv('REDIS_HOST', 'localhost')
        port = os.getenv('REDIS_PORT', '6379')
        db = os.getenv('REDIS_DB', '0')
        password = os.getenv('REDIS_PASSWORD', '')

        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"

    def _initialize_redis(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5
            )

            # Test connection
            self.redis_client.ping()

            # Initialize pub/sub
            self.pubsub = self.redis_client.pubsub()

            print("✅ Redis task queue initialized")

        except Exception as e:
            print(f"⚠️  Failed to connect to Redis: {e}")
            print("📝 Task queue will be disabled")
            self.enabled = False
            self.redis_client = None

    def _get_queue_key(self, priority: TaskPriority) -> str:
        """Get Redis key for priority queue."""
        return f"{self.queue_prefix}:queue:{priority.name.lower()}"

    def _get_task_key(self, task_id: str) -> str:
        """Get Redis key for task data."""
        return f"{self.queue_prefix}:task:{task_id}"

    def _get_result_key(self, task_id: str) -> str:
        """Get Redis key for task result."""
        return f"{self.queue_prefix}:result:{task_id}"

    def _get_status_key(self, status: TaskStatus) -> str:
        """Get Redis key for status set."""
        return f"{self.queue_prefix}:status:{status.value}"

    def submit_task(self, task: Task) -> str:
        """
        Submit a task to the queue.

        Args:
            task: Task to submit

        Returns:
            Task ID
        """
        if not self.is_available():
            raise RuntimeError("Task queue not available")

        # Store task data
        task_key = self._get_task_key(task.task_id)
        self.redis_client.setex(
            task_key,
            24 * 3600,  # 24 hours TTL
            json.dumps(task.to_dict())
        )

        # Add to priority queue
        queue_key = self._get_queue_key(task.priority)
        self.redis_client.rpush(queue_key, task.task_id)

        # Add to pending status set
        status_key = self._get_status_key(TaskStatus.PENDING)
        self.redis_client.sadd(status_key, task.task_id)

        # Publish notification
        self._publish_event('task.submitted', {
            'task_id': task.task_id,
            'task_type': task.task_type.value,
            'priority': task.priority.name
        })

        print(f"📤 Task submitted: {task.task_id} ({task.priority.name} priority)")

        return task.task_id

    def get_next_task(self, priorities: Optional[List[TaskPriority]] = None) -> Optional[Task]:
        """
        Get next task from queue (highest priority first).

        Args:
            priorities: List of priorities to check (default: all, highest first)

        Returns:
            Next task or None
        """
        if not self.is_available():
            return None

        if priorities is None:
            # Check all priorities, highest first
            priorities = [
                TaskPriority.URGENT,
                TaskPriority.HIGH,
                TaskPriority.NORMAL,
                TaskPriority.LOW
            ]

        # Try each priority queue
        for priority in priorities:
            queue_key = self._get_queue_key(priority)

            # Pop from queue (blocking with timeout)
            result = self.redis_client.blpop(queue_key, timeout=1)

            if result:
                _, task_id = result
                return self.get_task(task_id)

        return None

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        if not self.is_available():
            return None

        task_key = self._get_task_key(task_id)
        task_data = self.redis_client.get(task_key)

        if task_data:
            return Task.from_dict(json.loads(task_data))

        return None

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        worker_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Update task status."""
        if not self.is_available():
            return

        task = self.get_task(task_id)
        if not task:
            return

        # Remove from old status set
        old_status_key = self._get_status_key(task.status)
        self.redis_client.srem(old_status_key, task_id)

        # Update task
        task.status = status
        if worker_id:
            task.worker_id = worker_id
        if error:
            task.error = error

        if status == TaskStatus.RUNNING:
            task.started_at = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.now()

        # Save updated task
        task_key = self._get_task_key(task_id)
        self.redis_client.setex(
            task_key,
            24 * 3600,
            json.dumps(task.to_dict())
        )

        # Add to new status set
        new_status_key = self._get_status_key(status)
        self.redis_client.sadd(new_status_key, task_id)

        # Publish notification
        self._publish_event('task.status_changed', {
            'task_id': task_id,
            'status': status.value,
            'worker_id': worker_id
        })

    def save_result(self, task_id: str, result: TaskResult):
        """Save task result."""
        if not self.is_available():
            return

        result_key = self._get_result_key(task_id)
        self.redis_client.setex(
            result_key,
            self.result_ttl,
            json.dumps(result.to_dict())
        )

        # Update task with result
        task = self.get_task(task_id)
        if task:
            task.result = result.result
            task.error = result.error
            task.status = result.status
            task.completed_at = result.completed_at

            task_key = self._get_task_key(task_id)
            self.redis_client.setex(
                task_key,
                24 * 3600,
                json.dumps(task.to_dict())
            )

        # Publish notification
        self._publish_event('task.completed', {
            'task_id': task_id,
            'status': result.status.value,
            'duration': result.duration
        })

    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result."""
        if not self.is_available():
            return None

        result_key = self._get_result_key(task_id)
        result_data = self.redis_client.get(result_key)

        if result_data:
            return TaskResult.from_dict(json.loads(result_data))

        return None

    def cancel_task(self, task_id: str):
        """Cancel a pending task."""
        if not self.is_available():
            return

        task = self.get_task(task_id)
        if not task:
            return

        if task.status == TaskStatus.PENDING:
            # Remove from queue
            queue_key = self._get_queue_key(task.priority)
            self.redis_client.lrem(queue_key, 0, task_id)

            # Update status
            self.update_task_status(task_id, TaskStatus.CANCELLED)

            print(f"🚫 Task cancelled: {task_id}")

    def retry_task(self, task_id: str):
        """Retry a failed task."""
        if not self.is_available():
            return

        task = self.get_task(task_id)
        if not task:
            return

        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.RETRY
            task.error = None

            # Resubmit to queue
            queue_key = self._get_queue_key(task.priority)
            self.redis_client.rpush(queue_key, task.task_id)

            # Update task
            task_key = self._get_task_key(task_id)
            self.redis_client.setex(
                task_key,
                24 * 3600,
                json.dumps(task.to_dict())
            )

            print(f"🔄 Task retry {task.retry_count}/{task.max_retries}: {task_id}")
        else:
            print(f"❌ Max retries reached for task: {task_id}")
            self.update_task_status(task_id, TaskStatus.FAILED)

    def get_queue_stats(self) -> QueueStats:
        """Get queue statistics."""
        if not self.is_available():
            return QueueStats()

        stats = QueueStats()

        # Count tasks by status
        for status in TaskStatus:
            status_key = self._get_status_key(status)
            count = self.redis_client.scard(status_key)

            if status == TaskStatus.PENDING:
                stats.pending_tasks = count
            elif status == TaskStatus.RUNNING:
                stats.running_tasks = count
            elif status == TaskStatus.COMPLETED:
                stats.completed_tasks = count
            elif status == TaskStatus.FAILED:
                stats.failed_tasks = count

        stats.total_tasks = (
            stats.pending_tasks +
            stats.running_tasks +
            stats.completed_tasks +
            stats.failed_tasks
        )

        # Calculate success rate
        if stats.completed_tasks + stats.failed_tasks > 0:
            stats.success_rate = stats.completed_tasks / (stats.completed_tasks + stats.failed_tasks)

        # Get active workers count
        worker_key = f"{self.queue_prefix}:workers"
        stats.active_workers = self.redis_client.scard(worker_key)

        return stats

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[Task]:
        """List tasks by status."""
        if not self.is_available():
            return []

        if status:
            statuses = [status]
        else:
            statuses = list(TaskStatus)

        tasks = []
        for s in statuses:
            status_key = self._get_status_key(s)
            task_ids = self.redis_client.smembers(status_key)

            for task_id in task_ids:
                task = self.get_task(task_id)
                if task:
                    tasks.append(task)

            if len(tasks) >= limit:
                break

        return tasks[:limit]

    def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish event to pub/sub channel."""
        if not self.is_available():
            return

        try:
            channel = f"{self.queue_prefix}:events"
            message = {
                'type': event_type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            self.redis_client.publish(channel, json.dumps(message))
        except Exception as e:
            print(f"⚠️  Failed to publish event: {e}")

    def subscribe_to_events(self, callback):
        """Subscribe to queue events."""
        if not self.is_available():
            return

        channel = f"{self.queue_prefix}:events"
        self.pubsub.subscribe(**{channel: callback})

        # Start listening thread
        self.pubsub.run_in_thread(sleep_time=0.1)

    def register_worker(self, worker_id: str):
        """Register a worker."""
        if not self.is_available():
            return

        worker_key = f"{self.queue_prefix}:workers"
        self.redis_client.sadd(worker_key, worker_id)

        # Set worker heartbeat
        heartbeat_key = f"{self.queue_prefix}:worker:{worker_id}:heartbeat"
        self.redis_client.setex(heartbeat_key, 60, datetime.now().isoformat())

    def unregister_worker(self, worker_id: str):
        """Unregister a worker."""
        if not self.is_available():
            return

        worker_key = f"{self.queue_prefix}:workers"
        self.redis_client.srem(worker_key, worker_id)

    def worker_heartbeat(self, worker_id: str):
        """Update worker heartbeat."""
        if not self.is_available():
            return

        heartbeat_key = f"{self.queue_prefix}:worker:{worker_id}:heartbeat"
        self.redis_client.setex(heartbeat_key, 60, datetime.now().isoformat())

    def cleanup_stale_workers(self, timeout: int = 120):
        """Remove stale workers that haven't sent heartbeat."""
        if not self.is_available():
            return

        worker_key = f"{self.queue_prefix}:workers"
        workers = self.redis_client.smembers(worker_key)

        for worker_id in workers:
            heartbeat_key = f"{self.queue_prefix}:worker:{worker_id}:heartbeat"
            if not self.redis_client.exists(heartbeat_key):
                self.unregister_worker(worker_id)
                print(f"🧹 Removed stale worker: {worker_id}")

    def clear_queue(self):
        """Clear all tasks from queue (use with caution)."""
        if not self.is_available():
            return

        # Clear all priority queues
        for priority in TaskPriority:
            queue_key = self._get_queue_key(priority)
            self.redis_client.delete(queue_key)

        # Clear status sets
        for status in TaskStatus:
            status_key = self._get_status_key(status)
            self.redis_client.delete(status_key)

        print("🧹 Queue cleared")

    def is_available(self) -> bool:
        """Check if task queue is available."""
        return self.enabled and self.redis_client is not None

    def close(self):
        """Close Redis connections."""
        if self.pubsub:
            self.pubsub.close()
        if self.redis_client:
            self.redis_client.close()


# Global task queue instance
_task_queue = None


def get_task_queue() -> TaskQueue:
    """Get the global task queue instance."""
    global _task_queue

    if _task_queue is None:
        try:
            _task_queue = TaskQueue()
        except Exception as e:
            print(f"⚠️  Could not initialize task queue: {e}")
            # Create disabled queue
            _task_queue = TaskQueue.__new__(TaskQueue)
            _task_queue.enabled = False
            _task_queue.redis_client = None

    return _task_queue
