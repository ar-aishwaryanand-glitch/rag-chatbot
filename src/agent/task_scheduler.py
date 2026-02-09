"""Task Scheduler - Schedule and run manager agent tasks periodically.

This module provides scheduling capabilities for the Manager Agent:
- Schedule recurring tasks (daily, weekly, hourly)
- One-time scheduled tasks
- Task queue management
- Execution history tracking

Usage:
    scheduler = TaskScheduler(manager_agent)
    scheduler.schedule_recurring(
        "Run QA analysis for auth module",
        schedule_type="daily",
        time="09:00"
    )
    scheduler.start()
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import json
import threading
import time
import uuid

from src.logging_config import get_logger
from src.config import Config

logger = get_logger(__name__)


class ScheduleType(Enum):
    """Types of schedules."""
    ONCE = "once"           # Run once at specified time
    HOURLY = "hourly"       # Run every hour
    DAILY = "daily"         # Run every day at specified time
    WEEKLY = "weekly"       # Run every week on specified day
    INTERVAL = "interval"   # Run every N minutes


@dataclass
class ScheduledTask:
    """A scheduled task."""
    id: str
    goal: str
    schedule_type: str
    next_run: str  # ISO format datetime
    created_at: str
    enabled: bool = True
    last_run: Optional[str] = None
    last_result: Optional[str] = None  # success/failure
    run_count: int = 0
    config: Dict[str, Any] = field(default_factory=dict)
    # Config can include: time, day_of_week, interval_minutes

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'ScheduledTask':
        return cls(**data)


class TaskScheduler:
    """
    Task scheduler for Manager Agent.

    Features:
    - Schedule one-time and recurring tasks
    - Persistent task storage
    - Background execution
    - Task management (enable/disable/delete)
    """

    def __init__(
        self,
        manager_agent=None,
        storage_path: Path = None,
        on_task_complete: Callable[[str, Dict], None] = None
    ):
        """
        Initialize task scheduler.

        Args:
            manager_agent: ManagerAgent instance
            storage_path: Path to store scheduled tasks
            on_task_complete: Callback when task completes
        """
        self.manager_agent = manager_agent
        self.storage_path = storage_path or Config.SCHEDULED_TASKS_PATH
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.tasks_file = self.storage_path / "scheduled_tasks.json"
        self.history_file = self.storage_path / "execution_history.jsonl"

        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._on_task_complete = on_task_complete

        # Load existing tasks
        self._load_tasks()

    def _load_tasks(self):
        """Load scheduled tasks from file."""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for task_id, task_data in data.items():
                        self._tasks[task_id] = ScheduledTask.from_dict(task_data)
                logger.info(f"Loaded {len(self._tasks)} scheduled tasks")
            except Exception as e:
                logger.error(f"Error loading tasks: {e}")

    def _save_tasks(self):
        """Save scheduled tasks to file."""
        try:
            data = {
                task_id: task.to_dict()
                for task_id, task in self._tasks.items()
            }
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")

    def _log_execution(self, task: ScheduledTask, result: Dict):
        """Log task execution to history."""
        try:
            with open(self.history_file, 'a', encoding='utf-8') as f:
                log_entry = {
                    "task_id": task.id,
                    "goal": task.goal,
                    "executed_at": datetime.now().isoformat(),
                    "success": result.get("success", False),
                    "summary": result.get("summary", "")[:500]
                }
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Error logging execution: {e}")

    def schedule_once(
        self,
        goal: str,
        run_at: datetime
    ) -> str:
        """
        Schedule a one-time task.

        Args:
            goal: Goal to execute
            run_at: When to run

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())[:8]
        task = ScheduledTask(
            id=task_id,
            goal=goal,
            schedule_type=ScheduleType.ONCE.value,
            next_run=run_at.isoformat(),
            created_at=datetime.now().isoformat()
        )

        self._tasks[task_id] = task
        self._save_tasks()

        logger.info(f"Scheduled one-time task {task_id} for {run_at}")
        return task_id

    def schedule_recurring(
        self,
        goal: str,
        schedule_type: str,
        time: str = "09:00",
        day_of_week: int = 0,  # 0=Monday
        interval_minutes: int = 60
    ) -> str:
        """
        Schedule a recurring task.

        Args:
            goal: Goal to execute
            schedule_type: "hourly", "daily", "weekly", "interval"
            time: Time to run (HH:MM) for daily/weekly
            day_of_week: Day for weekly (0=Monday)
            interval_minutes: Minutes for interval type

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())[:8]

        config = {
            "time": time,
            "day_of_week": day_of_week,
            "interval_minutes": interval_minutes
        }

        next_run = self._calculate_next_run(schedule_type, config)

        task = ScheduledTask(
            id=task_id,
            goal=goal,
            schedule_type=schedule_type,
            next_run=next_run.isoformat(),
            created_at=datetime.now().isoformat(),
            config=config
        )

        self._tasks[task_id] = task
        self._save_tasks()

        logger.info(f"Scheduled recurring task {task_id} ({schedule_type}) next run: {next_run}")
        return task_id

    def _calculate_next_run(
        self,
        schedule_type: str,
        config: Dict
    ) -> datetime:
        """Calculate next run time based on schedule type."""
        now = datetime.now()

        if schedule_type == ScheduleType.HOURLY.value:
            # Next hour
            return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

        elif schedule_type == ScheduleType.DAILY.value:
            # Today or tomorrow at specified time
            time_parts = config.get("time", "09:00").split(":")
            hour, minute = int(time_parts[0]), int(time_parts[1]) if len(time_parts) > 1 else 0
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
            return target

        elif schedule_type == ScheduleType.WEEKLY.value:
            # Next occurrence of day_of_week at specified time
            time_parts = config.get("time", "09:00").split(":")
            hour, minute = int(time_parts[0]), int(time_parts[1]) if len(time_parts) > 1 else 0
            target_day = config.get("day_of_week", 0)

            days_ahead = target_day - now.weekday()
            if days_ahead <= 0:  # Target day already passed this week
                days_ahead += 7

            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            target += timedelta(days=days_ahead)
            return target

        elif schedule_type == ScheduleType.INTERVAL.value:
            # After N minutes
            interval = config.get("interval_minutes", 60)
            return now + timedelta(minutes=interval)

        else:
            # Default: 1 hour from now
            return now + timedelta(hours=1)

    def enable_task(self, task_id: str):
        """Enable a scheduled task."""
        if task_id in self._tasks:
            self._tasks[task_id].enabled = True
            self._save_tasks()

    def disable_task(self, task_id: str):
        """Disable a scheduled task."""
        if task_id in self._tasks:
            self._tasks[task_id].enabled = False
            self._save_tasks()

    def delete_task(self, task_id: str):
        """Delete a scheduled task."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            self._save_tasks()

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[ScheduledTask]:
        """Get all scheduled tasks."""
        return list(self._tasks.values())

    def get_pending_tasks(self) -> List[ScheduledTask]:
        """Get tasks ready to run."""
        now = datetime.now()
        pending = []

        for task in self._tasks.values():
            if not task.enabled:
                continue

            try:
                next_run = datetime.fromisoformat(task.next_run)
                if next_run <= now:
                    pending.append(task)
            except Exception:
                pass

        return pending

    def run_task(self, task: ScheduledTask) -> Dict[str, Any]:
        """
        Run a scheduled task immediately.

        Args:
            task: Task to run

        Returns:
            Execution result
        """
        if not self.manager_agent:
            return {
                "success": False,
                "error": "No manager agent configured"
            }

        logger.info(f"Running scheduled task {task.id}: {task.goal[:50]}...")

        try:
            # Execute through manager agent
            result = self.manager_agent.execute(task.goal)

            # Update task
            task.last_run = datetime.now().isoformat()
            task.last_result = "success" if result.get("success") else "failure"
            task.run_count += 1

            # Calculate next run for recurring tasks
            if task.schedule_type != ScheduleType.ONCE.value:
                task.next_run = self._calculate_next_run(
                    task.schedule_type,
                    task.config
                ).isoformat()
            else:
                # Disable one-time tasks after running
                task.enabled = False

            self._save_tasks()

            # Log execution
            self._log_execution(task, result)

            # Callback
            if self._on_task_complete:
                self._on_task_complete(task.id, result)

            return result

        except Exception as e:
            logger.error(f"Error running task {task.id}: {e}")
            task.last_run = datetime.now().isoformat()
            task.last_result = "error"
            self._save_tasks()

            return {
                "success": False,
                "error": str(e)
            }

    def _scheduler_loop(self):
        """Background scheduler loop."""
        logger.info("Scheduler started")

        while self._running:
            try:
                # Check for pending tasks
                pending = self.get_pending_tasks()

                for task in pending:
                    logger.info(f"Executing pending task: {task.id}")
                    self.run_task(task)

            except Exception as e:
                logger.error(f"Scheduler error: {e}")

            # Sleep for check interval (1 minute)
            time.sleep(60)

        logger.info("Scheduler stopped")

    def start(self):
        """Start the background scheduler."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()
        logger.info("Background scheduler started")

    def stop(self):
        """Stop the background scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Background scheduler stopped")

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running

    def get_execution_history(self, limit: int = 50) -> List[Dict]:
        """Get recent execution history."""
        history = []

        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-limit:]:
                        if line.strip():
                            history.append(json.loads(line))
            except Exception as e:
                logger.error(f"Error reading history: {e}")

        return list(reversed(history))

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status summary."""
        tasks = self.get_all_tasks()
        enabled = sum(1 for t in tasks if t.enabled)
        pending = len(self.get_pending_tasks())

        return {
            "running": self._running,
            "total_tasks": len(tasks),
            "enabled_tasks": enabled,
            "pending_tasks": pending,
            "next_scheduled": self._get_next_scheduled()
        }

    def _get_next_scheduled(self) -> Optional[str]:
        """Get next scheduled task time."""
        enabled_tasks = [t for t in self._tasks.values() if t.enabled]
        if not enabled_tasks:
            return None

        try:
            next_task = min(
                enabled_tasks,
                key=lambda t: datetime.fromisoformat(t.next_run)
            )
            return next_task.next_run
        except Exception:
            return None


# ============================================================================
# Helper functions for easy scheduling
# ============================================================================

def create_daily_qa_schedule(
    manager_agent,
    topic: str,
    time: str = "09:00"
) -> str:
    """
    Create a daily QA schedule for a topic.

    Args:
        manager_agent: Manager agent instance
        topic: Topic to analyze daily
        time: Time to run (HH:MM)

    Returns:
        Task ID
    """
    scheduler = TaskScheduler(manager_agent)
    return scheduler.schedule_recurring(
        goal=f"Run comprehensive QA analysis for {topic}",
        schedule_type="daily",
        time=time
    )


def create_weekly_coverage_report(
    manager_agent,
    topics: List[str],
    day_of_week: int = 0,  # Monday
    time: str = "08:00"
) -> List[str]:
    """
    Create weekly coverage reports for multiple topics.

    Args:
        manager_agent: Manager agent instance
        topics: List of topics to report on
        day_of_week: Day to run (0=Monday)
        time: Time to run

    Returns:
        List of task IDs
    """
    scheduler = TaskScheduler(manager_agent)
    task_ids = []

    for topic in topics:
        task_id = scheduler.schedule_recurring(
            goal=f"Generate traceability matrix and coverage report for {topic}",
            schedule_type="weekly",
            day_of_week=day_of_week,
            time=time
        )
        task_ids.append(task_id)

    return task_ids
