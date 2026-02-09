"""Shared types for the agent system.

This module contains common dataclasses and enums used across
the agent system to avoid duplication and ensure consistency.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class AgentType(Enum):
    """Types of specialized agents."""
    QA = "qa"
    DEVELOPER = "developer"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    PERFORMANCE = "performance"


@dataclass
class AgentCapability:
    """Describes what an agent can do."""
    name: str
    description: str
    tools: List[str]
    keywords: List[str]  # Keywords that trigger this agent


@dataclass
class TaskAssignment:
    """A task assigned to a specific agent."""
    task_id: str
    agent_type: AgentType
    instruction: str
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 1 = highest
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    result: Optional[str] = None


@dataclass
class ExecutionPlan:
    """Plan created by manager for task execution."""
    goal: str
    tasks: List[TaskAssignment]
    execution_order: List[str]  # Task IDs in order
    estimated_steps: int
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    output: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
