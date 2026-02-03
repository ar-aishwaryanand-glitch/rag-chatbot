"""
Task worker for processing queued tasks.

Workers consume tasks from the Redis queue and execute them.
"""

import os
import time
import signal
import uuid
from typing import Optional, Callable
from datetime import datetime

from .task_queue import TaskQueue, get_task_queue
from .task_models import (
    Task,
    TaskStatus,
    TaskType,
    TaskResult,
    AgentTask
)


class TaskWorker:
    """
    Worker process for executing queued tasks.

    Features:
    - Consumes tasks from priority queues
    - Executes agent queries
    - Handles retries and failures
    - Sends heartbeats
    - Graceful shutdown
    """

    def __init__(
        self,
        worker_id: Optional[str] = None,
        task_queue: Optional[TaskQueue] = None,
        agent_executor = None
    ):
        """
        Initialize task worker.

        Args:
            worker_id: Unique worker identifier
            task_queue: TaskQueue instance
            agent_executor: AgentExecutorV3 instance for executing tasks
        """
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.task_queue = task_queue or get_task_queue()
        self.agent_executor = agent_executor

        self.running = False
        self.current_task: Optional[Task] = None
        self.tasks_processed = 0
        self.tasks_failed = 0

        # Task type handlers
        self.handlers = {
            TaskType.AGENT_QUERY: self._handle_agent_query,
            TaskType.DOCUMENT_INDEX: self._handle_document_index,
            TaskType.BATCH_QUERY: self._handle_batch_query,
        }

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Worker {self.worker_id} received shutdown signal")
        self.stop()

    def start(self):
        """Start the worker."""
        if not self.task_queue.is_available():
            print("❌ Task queue not available. Worker cannot start.")
            return

        print(f"🚀 Worker {self.worker_id} starting...")
        self.running = True

        # Register worker
        self.task_queue.register_worker(self.worker_id)

        print(f"✅ Worker {self.worker_id} ready")

        try:
            self._work_loop()
        finally:
            self._cleanup()

    def stop(self):
        """Stop the worker gracefully."""
        print(f"🛑 Worker {self.worker_id} stopping...")
        self.running = False

    def _work_loop(self):
        """Main work loop."""
        last_heartbeat = time.time()
        heartbeat_interval = 30  # seconds

        while self.running:
            try:
                # Send heartbeat periodically
                if time.time() - last_heartbeat > heartbeat_interval:
                    self.task_queue.worker_heartbeat(self.worker_id)
                    last_heartbeat = time.time()

                # Get next task
                task = self.task_queue.get_next_task()

                if task:
                    self._process_task(task)
                else:
                    # No tasks available, wait a bit
                    time.sleep(1)

            except KeyboardInterrupt:
                print(f"\n⚠️  Worker {self.worker_id} interrupted")
                break
            except Exception as e:
                print(f"❌ Worker error: {e}")
                time.sleep(5)  # Wait before retrying

    def _process_task(self, task: Task):
        """Process a single task."""
        self.current_task = task
        start_time = time.time()

        print(f"📝 Worker {self.worker_id} processing task {task.task_id}")

        # Update task status to running
        self.task_queue.update_task_status(
            task.task_id,
            TaskStatus.RUNNING,
            worker_id=self.worker_id
        )

        try:
            # Get handler for task type
            handler = self.handlers.get(task.task_type)

            if not handler:
                raise ValueError(f"No handler for task type: {task.task_type}")

            # Execute handler
            result = handler(task)

            # Calculate duration
            duration = time.time() - start_time

            # Save successful result
            task_result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                result=result,
                duration=duration,
                worker_id=self.worker_id
            )

            self.task_queue.save_result(task.task_id, task_result)
            self.task_queue.update_task_status(task.task_id, TaskStatus.COMPLETED)

            self.tasks_processed += 1

            print(f"✅ Task {task.task_id} completed in {duration:.2f}s")

        except Exception as e:
            # Handle failure
            duration = time.time() - start_time
            error_msg = str(e)

            print(f"❌ Task {task.task_id} failed: {error_msg}")

            # Save failed result
            task_result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                error=error_msg,
                duration=duration,
                worker_id=self.worker_id
            )

            self.task_queue.save_result(task.task_id, task_result)

            # Retry if possible
            if task.retry_count < task.max_retries:
                self.task_queue.retry_task(task.task_id)
            else:
                self.task_queue.update_task_status(
                    task.task_id,
                    TaskStatus.FAILED,
                    error=error_msg
                )

            self.tasks_failed += 1

        finally:
            self.current_task = None

    def _handle_agent_query(self, task: Task) -> dict:
        """Handle agent query task."""
        if not self.agent_executor:
            raise RuntimeError("Agent executor not configured")

        # Extract query from payload
        query = task.payload.get('query')
        if not query:
            raise ValueError("No query in task payload")

        # Get optional parameters
        session_id = task.session_id or task.task_id
        thread_id = task.payload.get('thread_id')

        # Execute agent
        result = self.agent_executor.execute(
            query=query,
            session_id=session_id,
            thread_id=thread_id
        )

        return {
            'query': query,
            'answer': result.get('final_answer', ''),
            'tools_used': result.get('tools_used', []),
            'execution_time': result.get('execution_metadata', {}).get('total_duration', 0)
        }

    def _handle_document_index(self, task: Task) -> dict:
        """Handle document indexing task."""
        # Placeholder for document indexing
        # Would integrate with document manager

        document_path = task.payload.get('document_path')
        if not document_path:
            raise ValueError("No document_path in task payload")

        # TODO: Implement document indexing
        return {
            'document_path': document_path,
            'indexed': True,
            'chunks': 0
        }

    def _handle_batch_query(self, task: Task) -> dict:
        """Handle batch query task."""
        if not self.agent_executor:
            raise RuntimeError("Agent executor not configured")

        queries = task.payload.get('queries', [])
        if not queries:
            raise ValueError("No queries in task payload")

        results = []

        for query in queries:
            try:
                result = self.agent_executor.execute(
                    query=query,
                    session_id=task.session_id or task.task_id
                )

                results.append({
                    'query': query,
                    'answer': result.get('final_answer', ''),
                    'success': True
                })
            except Exception as e:
                results.append({
                    'query': query,
                    'error': str(e),
                    'success': False
                })

        return {
            'total': len(queries),
            'successful': sum(1 for r in results if r.get('success')),
            'failed': sum(1 for r in results if not r.get('success')),
            'results': results
        }

    def register_handler(self, task_type: TaskType, handler: Callable):
        """Register a custom task handler."""
        self.handlers[task_type] = handler

    def _cleanup(self):
        """Cleanup on shutdown."""
        print(f"🧹 Worker {self.worker_id} cleaning up...")

        # Unregister worker
        if self.task_queue.is_available():
            self.task_queue.unregister_worker(self.worker_id)

        print(f"📊 Worker {self.worker_id} stats:")
        print(f"   Tasks processed: {self.tasks_processed}")
        print(f"   Tasks failed: {self.tasks_failed}")

        if self.tasks_processed > 0:
            success_rate = (
                (self.tasks_processed - self.tasks_failed) / self.tasks_processed * 100
            )
            print(f"   Success rate: {success_rate:.1f}%")

        print(f"👋 Worker {self.worker_id} stopped")

    def get_status(self) -> dict:
        """Get worker status."""
        return {
            'worker_id': self.worker_id,
            'running': self.running,
            'current_task': self.current_task.task_id if self.current_task else None,
            'tasks_processed': self.tasks_processed,
            'tasks_failed': self.tasks_failed,
            'success_rate': (
                (self.tasks_processed - self.tasks_failed) / self.tasks_processed
                if self.tasks_processed > 0 else 0
            )
        }
