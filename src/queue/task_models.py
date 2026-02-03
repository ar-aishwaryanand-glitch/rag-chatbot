"""
Task models and definitions for the message queue system.

Defines task types, status, priorities, and data structures.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"           # Waiting in queue
    RUNNING = "running"           # Currently executing
    COMPLETED = "completed"       # Successfully completed
    FAILED = "failed"             # Failed with error
    CANCELLED = "cancelled"       # Cancelled by user
    RETRY = "retry"               # Waiting for retry


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 0
    NORMAL = 5
    HIGH = 10
    URGENT = 15


class TaskType(Enum):
    """Types of tasks."""
    AGENT_QUERY = "agent_query"           # Execute agent query
    DOCUMENT_INDEX = "document_index"     # Index document
    BATCH_QUERY = "batch_query"           # Batch of queries
    SCHEDULED = "scheduled"               # Scheduled task
    WEBHOOK = "webhook"                   # Webhook callback


@dataclass
class Task:
    """Base task definition."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType = TaskType.AGENT_QUERY
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING

    # Retry configuration
    max_retries: int = 3
    retry_count: int = 0
    retry_delay: int = 60  # seconds

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Execution info
    worker_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    # Metadata
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        data = asdict(self)
        # Convert enums to strings
        data['task_type'] = self.task_type.value
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        # Convert datetimes to ISO format
        data['created_at'] = self.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary."""
        # Convert string enums back
        if isinstance(data.get('task_type'), str):
            data['task_type'] = TaskType(data['task_type'])
        if isinstance(data.get('priority'), (str, int)):
            data['priority'] = TaskPriority(data['priority']) if isinstance(data['priority'], str) else TaskPriority(data['priority'])
        if isinstance(data.get('status'), str):
            data['status'] = TaskStatus(data['status'])

        # Convert ISO strings back to datetime
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('started_at'):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])

        return cls(**data)


@dataclass
class AgentTask(Task):
    """Specialized task for agent query execution."""
    task_type: TaskType = TaskType.AGENT_QUERY

    def __post_init__(self):
        """Validate agent task payload."""
        if 'query' not in self.payload:
            raise ValueError("AgentTask requires 'query' in payload")


@dataclass
class TaskResult:
    """Task execution result."""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    duration: float = 0.0
    worker_id: Optional[str] = None
    completed_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'task_id': self.task_id,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'duration': self.duration,
            'worker_id': self.worker_id,
            'completed_at': self.completed_at.isoformat(),
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskResult':
        """Create result from dictionary."""
        if isinstance(data.get('status'), str):
            data['status'] = TaskStatus(data['status'])
        if isinstance(data.get('completed_at'), str):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**data)


@dataclass
class QueueStats:
    """Queue statistics."""
    pending_tasks: int = 0
    running_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_tasks: int = 0
    active_workers: int = 0
    avg_execution_time: float = 0.0
    success_rate: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            'pending_tasks': self.pending_tasks,
            'running_tasks': self.running_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'total_tasks': self.total_tasks,
            'active_workers': self.active_workers,
            'avg_execution_time': self.avg_execution_time,
            'success_rate': self.success_rate,
            'timestamp': self.timestamp.isoformat()
        }
