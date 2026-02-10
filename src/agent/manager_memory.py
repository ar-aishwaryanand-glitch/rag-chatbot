"""Manager Agent Memory - Persistent storage for execution history and learning.

This module provides memory capabilities for the Manager Agent:
- Persistent execution history
- Learning from past executions
- Context retrieval for similar tasks
- Performance analytics
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import json
from collections import defaultdict

from src.logging_config import get_logger
from src.config import Config

logger = get_logger(__name__)

# Default storage path
DEFAULT_MEMORY_PATH = Config.MANAGER_MEMORY_PATH


@dataclass
class ExecutionRecord:
    """Record of a single execution."""
    id: str
    goal: str
    timestamp: str
    success: bool
    tasks_completed: int
    tasks_total: int
    duration_seconds: float
    agents_used: List[str]
    tools_used: List[str]
    summary: str
    full_results: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    user_feedback: Optional[str] = None
    rating: Optional[int] = None  # 1-5 scale

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'ExecutionRecord':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class AgentPerformance:
    """Performance metrics for an agent."""
    agent_name: str
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_duration: float = 0.0
    avg_duration: float = 0.0
    success_rate: float = 0.0
    common_task_types: Dict[str, int] = field(default_factory=dict)


class ManagerMemory:
    """
    Persistent memory for Manager Agent.

    Features:
    - Save/load execution history
    - Search similar past executions
    - Track agent and tool performance
    - Learn from feedback
    """

    def __init__(self, storage_path: Path = None):
        """
        Initialize manager memory.

        Args:
            storage_path: Path to store memory files
        """
        self.storage_path = storage_path or DEFAULT_MEMORY_PATH
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.history_file = self.storage_path / "execution_history.jsonl"
        self.performance_file = self.storage_path / "agent_performance.json"
        self.patterns_file = self.storage_path / "learned_patterns.json"

        # In-memory cache
        self._history: List[ExecutionRecord] = []
        self._performance: Dict[str, AgentPerformance] = {}
        self._patterns: Dict[str, Any] = {}

        # Load existing data
        self._load_history()
        self._load_performance()
        self._load_patterns()

    def _load_history(self):
        """Load execution history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            self._history.append(ExecutionRecord.from_dict(data))
                logger.info(f"Loaded {len(self._history)} execution records")
            except (json.JSONDecodeError, OSError, KeyError) as e:
                logger.error(f"Error loading history: {e}")

    def _load_performance(self):
        """Load performance metrics from file."""
        if self.performance_file.exists():
            try:
                with open(self.performance_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for name, metrics in data.items():
                        self._performance[name] = AgentPerformance(**metrics)
            except (json.JSONDecodeError, OSError, KeyError, TypeError) as e:
                logger.error(f"Error loading performance: {e}")

    def _load_patterns(self):
        """Load learned patterns from file."""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    self._patterns = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Error loading patterns: {e}")

    def _save_history_record(self, record: ExecutionRecord):
        """Append a single record to history file."""
        try:
            with open(self.history_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record.to_dict()) + '\n')
        except OSError as e:
            logger.error(f"Error saving history record: {e}")

    def _save_performance(self):
        """Save performance metrics to file."""
        try:
            data = {
                name: asdict(perf)
                for name, perf in self._performance.items()
            }
            with open(self.performance_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            logger.error(f"Error saving performance: {e}")

    def _save_patterns(self):
        """Save learned patterns to file."""
        try:
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self._patterns, f, indent=2)
        except OSError as e:
            logger.error(f"Error saving patterns: {e}")

    def record_execution(
        self,
        goal: str,
        result: Dict[str, Any],
        duration_seconds: float
    ) -> ExecutionRecord:
        """
        Record an execution in memory.

        Args:
            goal: The goal that was executed
            result: Execution result from manager
            duration_seconds: Total execution time

        Returns:
            The created ExecutionRecord
        """
        import uuid

        # Extract info from result
        plan = result.get('plan')
        results = result.get('results', {})

        tasks_completed = sum(1 for r in results.values() if r.get('success', False))
        tasks_total = len(results)

        agents_used = list(set(
            r.get('metadata', {}).get('agent', 'qa')
            for r in results.values()
        ))

        tools_used = list(set(
            r.get('tool_used', 'unknown')
            for r in results.values()
            if r.get('tool_used')
        ))

        # Extract tags from goal
        tags = self._extract_tags(goal)

        record = ExecutionRecord(
            id=str(uuid.uuid4())[:8],
            goal=goal,
            timestamp=datetime.now().isoformat(),
            success=result.get('success', False),
            tasks_completed=tasks_completed,
            tasks_total=tasks_total,
            duration_seconds=duration_seconds,
            agents_used=agents_used,
            tools_used=tools_used,
            summary=result.get('summary', ''),
            full_results=results,
            tags=tags
        )

        # Add to memory
        self._history.append(record)
        self._save_history_record(record)

        # Update performance metrics
        self._update_performance(record)

        # Learn patterns
        self._learn_from_execution(record)

        return record

    def _extract_tags(self, goal: str) -> List[str]:
        """Extract relevant tags from goal text."""
        tags = []
        goal_lower = goal.lower()

        tag_keywords = {
            "testing": ["test", "qa", "quality"],
            "security": ["security", "vulnerability", "owasp"],
            "documentation": ["document", "doc", "readme", "guide"],
            "code": ["code", "implement", "function", "class"],
            "api": ["api", "endpoint", "rest"],
            "authentication": ["auth", "login", "password"],
            "performance": ["performance", "load", "stress"],
            "bdd": ["bdd", "gherkin", "cucumber", "behave"]
        }

        for tag, keywords in tag_keywords.items():
            if any(kw in goal_lower for kw in keywords):
                tags.append(tag)

        return tags

    def _update_performance(self, record: ExecutionRecord):
        """Update agent performance metrics."""
        for agent in record.agents_used:
            if agent not in self._performance:
                self._performance[agent] = AgentPerformance(agent_name=agent)

            perf = self._performance[agent]
            perf.total_tasks += record.tasks_total

            if record.success:
                perf.successful_tasks += record.tasks_completed
            perf.failed_tasks += record.tasks_total - record.tasks_completed

            perf.total_duration += record.duration_seconds

            if perf.total_tasks > 0:
                perf.avg_duration = perf.total_duration / perf.total_tasks
                perf.success_rate = perf.successful_tasks / perf.total_tasks

            # Track task types
            for tag in record.tags:
                perf.common_task_types[tag] = perf.common_task_types.get(tag, 0) + 1

        self._save_performance()

    def _learn_from_execution(self, record: ExecutionRecord):
        """Learn patterns from successful executions."""
        if not record.success:
            return

        # Store successful patterns
        for tag in record.tags:
            if tag not in self._patterns:
                self._patterns[tag] = {
                    "successful_tools": {},
                    "successful_agents": {},
                    "avg_tasks": 0,
                    "count": 0
                }

            pattern = self._patterns[tag]
            pattern["count"] += 1

            # Update tool success
            for tool in record.tools_used:
                pattern["successful_tools"][tool] = \
                    pattern["successful_tools"].get(tool, 0) + 1

            # Update agent success
            for agent in record.agents_used:
                pattern["successful_agents"][agent] = \
                    pattern["successful_agents"].get(agent, 0) + 1

            # Update average tasks
            old_avg = pattern["avg_tasks"]
            pattern["avg_tasks"] = (old_avg * (pattern["count"] - 1) + record.tasks_total) / pattern["count"]

        self._save_patterns()

    def find_similar_executions(
        self,
        goal: str,
        limit: int = 5
    ) -> List[ExecutionRecord]:
        """
        Find similar past executions.

        Args:
            goal: Current goal
            limit: Maximum results to return

        Returns:
            List of similar ExecutionRecords
        """
        goal_lower = goal.lower()
        goal_words = set(goal_lower.split())
        current_tags = set(self._extract_tags(goal))

        scored_records = []
        for record in self._history:
            score = 0

            # Tag overlap
            record_tags = set(record.tags)
            tag_overlap = len(current_tags & record_tags)
            score += tag_overlap * 10

            # Word overlap in goals
            record_words = set(record.goal.lower().split())
            word_overlap = len(goal_words & record_words)
            score += word_overlap * 2

            # Boost successful executions
            if record.success:
                score += 5

            # Boost recent executions
            try:
                record_time = datetime.fromisoformat(record.timestamp)
                days_ago = (datetime.now() - record_time).days
                if days_ago < 7:
                    score += 3
                elif days_ago < 30:
                    score += 1
            except ValueError:
                logger.debug(f"Invalid timestamp format: {record.timestamp}")

            if score > 0:
                scored_records.append((score, record))

        # Sort by score and return top results
        scored_records.sort(key=lambda x: x[0], reverse=True)
        return [record for _, record in scored_records[:limit]]

    def get_recommendations_for_goal(self, goal: str) -> Dict[str, Any]:
        """
        Get recommendations based on past executions.

        Args:
            goal: Current goal

        Returns:
            Dict with recommended agents, tools, and estimated tasks
        """
        tags = self._extract_tags(goal)
        similar = self.find_similar_executions(goal, limit=10)

        recommendations = {
            "suggested_agents": [],
            "suggested_tools": [],
            "estimated_tasks": 3,
            "estimated_duration": 30.0,
            "similar_successful_goals": [],
            "tips": []
        }

        # Aggregate from patterns
        agent_scores = defaultdict(int)
        tool_scores = defaultdict(int)
        task_counts = []
        durations = []

        for tag in tags:
            if tag in self._patterns:
                pattern = self._patterns[tag]

                for agent, count in pattern.get("successful_agents", {}).items():
                    agent_scores[agent] += count

                for tool, count in pattern.get("successful_tools", {}).items():
                    tool_scores[tool] += count

                task_counts.append(pattern.get("avg_tasks", 3))

        # Aggregate from similar executions
        for record in similar:
            if record.success:
                for agent in record.agents_used:
                    agent_scores[agent] += 5
                for tool in record.tools_used:
                    tool_scores[tool] += 3
                task_counts.append(record.tasks_total)
                durations.append(record.duration_seconds)

                recommendations["similar_successful_goals"].append({
                    "goal": record.goal[:100],
                    "tasks": record.tasks_total,
                    "duration": record.duration_seconds
                })

        # Sort and get top recommendations
        recommendations["suggested_agents"] = sorted(
            agent_scores.keys(),
            key=lambda x: agent_scores[x],
            reverse=True
        )[:3]

        recommendations["suggested_tools"] = sorted(
            tool_scores.keys(),
            key=lambda x: tool_scores[x],
            reverse=True
        )[:5]

        if task_counts:
            recommendations["estimated_tasks"] = int(sum(task_counts) / len(task_counts))

        if durations:
            recommendations["estimated_duration"] = sum(durations) / len(durations)

        # Generate tips
        if similar:
            success_rate = sum(1 for r in similar if r.success) / len(similar)
            if success_rate < 0.5:
                recommendations["tips"].append(
                    "Similar goals have had mixed success. Consider being more specific."
                )
            else:
                recommendations["tips"].append(
                    f"Similar goals have {success_rate:.0%} success rate."
                )

        return recommendations

    def get_history(
        self,
        limit: int = 50,
        success_only: bool = False,
        tags: List[str] = None
    ) -> List[ExecutionRecord]:
        """
        Get execution history.

        Args:
            limit: Maximum records to return
            success_only: Only return successful executions
            tags: Filter by tags

        Returns:
            List of ExecutionRecords
        """
        records = self._history.copy()

        if success_only:
            records = [r for r in records if r.success]

        if tags:
            tag_set = set(tags)
            records = [r for r in records if set(r.tags) & tag_set]

        # Sort by timestamp descending
        records.sort(
            key=lambda x: x.timestamp,
            reverse=True
        )

        return records[:limit]

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary."""
        total_executions = len(self._history)
        successful = sum(1 for r in self._history if r.success)

        return {
            "total_executions": total_executions,
            "successful_executions": successful,
            "success_rate": successful / total_executions if total_executions > 0 else 0,
            "agent_performance": {
                name: asdict(perf)
                for name, perf in self._performance.items()
            },
            "common_tags": self._get_common_tags(),
            "recent_activity": self._get_recent_activity()
        }

    def _get_common_tags(self) -> Dict[str, int]:
        """Get most common tags."""
        tag_counts = defaultdict(int)
        for record in self._history:
            for tag in record.tags:
                tag_counts[tag] += 1
        return dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10])

    def _get_recent_activity(self) -> Dict[str, int]:
        """Get activity in recent time periods."""
        now = datetime.now()
        activity = {"today": 0, "this_week": 0, "this_month": 0}

        for record in self._history:
            try:
                record_time = datetime.fromisoformat(record.timestamp)
                days_ago = (now - record_time).days

                if days_ago == 0:
                    activity["today"] += 1
                if days_ago < 7:
                    activity["this_week"] += 1
                if days_ago < 30:
                    activity["this_month"] += 1
            except ValueError:
                logger.debug(f"Invalid timestamp format: {record.timestamp}")

        return activity

    def add_feedback(self, execution_id: str, feedback: str, rating: int = None):
        """
        Add user feedback to an execution.

        Args:
            execution_id: ID of the execution
            feedback: User's feedback text
            rating: Optional 1-5 rating
        """
        for record in self._history:
            if record.id == execution_id:
                record.user_feedback = feedback
                record.rating = rating

                # Re-learn patterns with feedback
                if rating and rating >= 4:
                    self._learn_from_execution(record)

                # Save updated history
                self._rewrite_history()
                break

    def _rewrite_history(self):
        """Rewrite entire history file (for updates)."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                for record in self._history:
                    f.write(json.dumps(record.to_dict()) + '\n')
        except OSError as e:
            logger.error(f"Error rewriting history: {e}")

    def clear_history(self):
        """Clear all history (use with caution)."""
        self._history = []
        self._performance = {}
        self._patterns = {}

        if self.history_file.exists():
            self.history_file.unlink()
        if self.performance_file.exists():
            self.performance_file.unlink()
        if self.patterns_file.exists():
            self.patterns_file.unlink()

        logger.info("Memory cleared")
