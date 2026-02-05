"""
Task scheduler for delayed and recurring tasks.

Simple scheduler using Redis sorted sets for time-based task execution.
"""

import time
from typing import Optional
from datetime import datetime, timedelta

from .task_queue import TaskQueue, get_task_queue
from .task_models import Task


class TaskScheduler:
    """
    Simple task scheduler for delayed tasks.

    Features:
    - Schedule tasks for future execution
    - Delayed task submission
    - Check and submit due tasks
    """

    def __init__(self, task_queue: Optional[TaskQueue] = None):
        """
        Initialize task scheduler.

        Args:
            task_queue: TaskQueue instance
        """
        self.task_queue = task_queue or get_task_queue()
        self.scheduled_key = f"{self.task_queue.queue_prefix}:scheduled"

    def schedule_task(
        self,
        task: Task,
        execute_at: datetime
    ) -> str:
        """
        Schedule a task for future execution.

        Args:
            task: Task to schedule
            execute_at: When to execute the task

        Returns:
            Task ID
        """
        if not self.task_queue.is_available():
            raise RuntimeError("Task queue not available")

        # Store task
        task_key = self.task_queue._get_task_key(task.task_id)
        import json
        self.task_queue.redis_client.setex(
            task_key,
            24 * 3600,
            json.dumps(task.to_dict())
        )

        # Add to scheduled sorted set (score = timestamp)
        score = execute_at.timestamp()
        self.task_queue.redis_client.zadd(
            self.scheduled_key,
            {task.task_id: score}
        )

        print(f"⏰ Task {task.task_id} scheduled for {execute_at}")

        return task.task_id

    def schedule_task_in(
        self,
        task: Task,
        delay_seconds: int
    ) -> str:
        """
        Schedule a task to execute after a delay.

        Args:
            task: Task to schedule
            delay_seconds: Delay in seconds

        Returns:
            Task ID
        """
        execute_at = datetime.now() + timedelta(seconds=delay_seconds)
        return self.schedule_task(task, execute_at)

    def check_and_submit_due_tasks(self) -> int:
        """
        Check for due tasks and submit them to the queue.

        Returns:
            Number of tasks submitted
        """
        if not self.task_queue.is_available():
            return 0

        now = datetime.now().timestamp()
        submitted = 0

        # Get all tasks with score <= now
        due_tasks = self.task_queue.redis_client.zrangebyscore(
            self.scheduled_key,
            0,
            now
        )

        for task_id in due_tasks:
            # Get task
            task = self.task_queue.get_task(task_id)

            if task:
                # Submit to queue
                self.task_queue.submit_task(task)
                submitted += 1

            # Remove from scheduled set
            self.task_queue.redis_client.zrem(self.scheduled_key, task_id)

        if submitted > 0:
            print(f"📤 Submitted {submitted} scheduled task(s)")

        return submitted

    def get_scheduled_tasks_count(self) -> int:
        """Get count of scheduled tasks."""
        if not self.task_queue.is_available():
            return 0

        return self.task_queue.redis_client.zcard(self.scheduled_key)

    def cancel_scheduled_task(self, task_id: str):
        """Cancel a scheduled task."""
        if not self.task_queue.is_available():
            return

        # Remove from scheduled set
        self.task_queue.redis_client.zrem(self.scheduled_key, task_id)

        # Delete task data
        task_key = self.task_queue._get_task_key(task_id)
        self.task_queue.redis_client.delete(task_key)

        print(f"🚫 Cancelled scheduled task: {task_id}")

    def run_scheduler_loop(self, check_interval: int = 10):
        """
        Run scheduler loop to check and submit due tasks.

        Args:
            check_interval: How often to check for due tasks (seconds)
        """
        print("⏰ Task scheduler starting...")

        try:
            while True:
                self.check_and_submit_due_tasks()
                time.sleep(check_interval)

        except KeyboardInterrupt:
            print("\n⏰ Task scheduler stopped")
