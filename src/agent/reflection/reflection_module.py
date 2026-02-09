"""Reflection module for agent self-evaluation."""

import atexit
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import json

from src.logging_config import get_logger

logger = get_logger(__name__)


class ReflectionType(Enum):
    """Types of reflections."""
    TOOL_SELECTION = "tool_selection"
    TOOL_EXECUTION = "tool_execution"
    ANSWER_QUALITY = "answer_quality"
    ERROR_ANALYSIS = "error_analysis"
    SESSION_SUMMARY = "session_summary"


@dataclass
class Reflection:
    """Represents a single reflection on agent behavior."""
    type: ReflectionType
    timestamp: datetime
    context: Dict[str, Any]  # Query, tool, result, etc.
    evaluation: Dict[str, Any]  # Scores, ratings, analysis
    insights: List[str] = field(default_factory=list)  # Key takeaways
    suggestions: List[str] = field(default_factory=list)  # Improvements
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "evaluation": self.evaluation,
            "insights": self.insights,
            "suggestions": self.suggestions,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Reflection':
        """Create reflection from dictionary."""
        return cls(
            type=ReflectionType(data["type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            context=data["context"],
            evaluation=data["evaluation"],
            insights=data.get("insights", []),
            suggestions=data.get("suggestions", []),
            metadata=data.get("metadata", {})
        )


class ReflectionModule:
    """
    Evaluates agent performance and generates insights.

    Features:
    - Tool selection evaluation
    - Answer quality assessment
    - Error analysis and recovery
    - Performance tracking
    """

    def __init__(self, llm=None, storage_path: Optional[Path] = None, buffer_size: int = 10, flush_interval: float = 30.0):
        """
        Initialize reflection module with persistence and write batching.

        Args:
            llm: Optional LLM for generating reflections (can work without)
            storage_path: Path to store reflection history (default: data/reflections)
            buffer_size: Number of reflections to buffer before flush (default: 10)
            flush_interval: Seconds between background flushes (default: 30)
        """
        self.llm = llm

        # Set up storage
        if storage_path is None:
            storage_path = Path(__file__).parent.parent.parent.parent / "data" / "reflections"

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.reflections_file = self.storage_path / "reflections.jsonl"  # JSONL for easy appending

        # Write batching configuration
        self._buffer_size = buffer_size
        self._flush_interval = flush_interval
        self._write_buffer: List[Reflection] = []
        self._buffer_lock = threading.Lock()

        # Background flush timer
        self._flush_timer: Optional[threading.Timer] = None
        self._start_flush_timer()

        # Register cleanup on exit
        atexit.register(self.flush)

        # Load existing reflections
        self.reflections: List[Reflection] = []
        self._load_reflections()

    def _load_reflections(self) -> None:
        """Load reflection history from disk."""
        if self.reflections_file.exists():
            try:
                with open(self.reflections_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            reflection = Reflection.from_dict(data)
                            self.reflections.append(reflection)

                logger.info(f"Loaded {len(self.reflections)} reflections from history")

            except Exception as e:
                logger.warning(f"Could not load reflection history: {e}. Starting with fresh reflection history")

    def _start_flush_timer(self) -> None:
        """Start the background flush timer."""
        if self._flush_timer is not None:
            self._flush_timer.cancel()

        self._flush_timer = threading.Timer(self._flush_interval, self._background_flush)
        self._flush_timer.daemon = True
        self._flush_timer.start()

    def _background_flush(self) -> None:
        """Background timer callback to flush the buffer."""
        self.flush()
        # Restart timer
        self._start_flush_timer()

    def _save_reflection(self, reflection: Reflection) -> None:
        """Buffer a reflection for batched writing."""
        with self._buffer_lock:
            self._write_buffer.append(reflection)

            # Flush if buffer is full
            if len(self._write_buffer) >= self._buffer_size:
                self._flush_buffer()

    def _flush_buffer(self) -> None:
        """Flush the write buffer to disk (must hold _buffer_lock)."""
        if not self._write_buffer:
            return

        try:
            # Append all buffered reflections at once
            with open(self.reflections_file, 'a', encoding='utf-8') as f:
                for reflection in self._write_buffer:
                    json.dump(reflection.to_dict(), f)
                    f.write('\n')

            self._write_buffer.clear()

        except Exception as e:
            logger.warning(f"Could not flush reflections: {e}")

    def flush(self) -> None:
        """Force flush any buffered reflections to disk."""
        with self._buffer_lock:
            self._flush_buffer()

    def reflect_on_tool_selection(
        self,
        query: str,
        selected_tool: str,
        available_tools: List[str],
        tool_result: Dict[str, Any]
    ) -> Reflection:
        """
        Evaluate whether the correct tool was selected.

        Args:
            query: User query
            selected_tool: Tool that was selected
            available_tools: List of all available tools
            tool_result: Result from tool execution

        Returns:
            Reflection on tool selection
        """
        context = {
            "query": query,
            "selected_tool": selected_tool,
            "available_tools": available_tools,
            "tool_success": tool_result.get("success", False)
        }

        # Simple heuristic-based evaluation
        evaluation = {
            "tool_succeeded": tool_result.get("success", False),
            "confidence": 0.8 if tool_result.get("success", False) else 0.4
        }

        insights = []
        suggestions = []

        if tool_result.get("success"):
            insights.append(f"Tool '{selected_tool}' successfully handled query type")
        else:
            error = tool_result.get("error", "Unknown error")
            insights.append(f"Tool '{selected_tool}' failed: {error}")
            suggestions.append("Consider trying alternative tools for similar queries")

        reflection = Reflection(
            type=ReflectionType.TOOL_SELECTION,
            timestamp=datetime.now(),
            context=context,
            evaluation=evaluation,
            insights=insights,
            suggestions=suggestions
        )

        self.reflections.append(reflection)
        self._save_reflection(reflection)
        return reflection

    def reflect_on_answer_quality(
        self,
        query: str,
        answer: str,
        sources: Optional[List[Dict]] = None,
        tools_used: Optional[List[str]] = None
    ) -> Reflection:
        """
        Evaluate the quality of the generated answer.

        Args:
            query: User query
            answer: Generated answer
            sources: Retrieved sources (for RAG)
            tools_used: Tools used to generate answer

        Returns:
            Reflection on answer quality
        """
        context = {
            "query": query,
            "answer_length": len(answer),
            "has_sources": sources is not None and len(sources) > 0,
            "tools_used": tools_used or []
        }

        # Improved adaptive quality scoring
        quality_score = 3.5  # Higher base score

        # Length-based scoring (more nuanced)
        answer_len = len(answer)
        if answer_len < 20:
            quality_score -= 1.5  # Very short = problem
        elif answer_len < 50:
            quality_score -= 0.5  # Short
        elif answer_len > 200:
            quality_score += 0.5  # Good detail
        elif answer_len > 500:
            quality_score += 0.75  # Very detailed

        # Source grounding bonus
        if sources and len(sources) > 0:
            quality_score += 0.3
            if len(sources) >= 2:
                quality_score += 0.2  # Multiple sources = better

        # Tool usage bonus (successful tool use indicates good routing)
        if tools_used and len(tools_used) > 0:
            quality_score += 0.3
            # Bonus for specialized tools (QA tools, web search)
            specialized_tools = {'qa_analysis', 'bug_report', 'test_strategy', 'web_search', 'news_api'}
            if any(t in specialized_tools for t in tools_used):
                quality_score += 0.2

        # Content quality checks
        answer_lower = answer.lower()
        if "error" in answer_lower or "failed" in answer_lower:
            quality_score -= 1.0
        if "sorry" in answer_lower and "couldn't" in answer_lower:
            quality_score -= 0.5

        # Positive content indicators
        if any(word in answer_lower for word in ['because', 'therefore', 'specifically', 'for example']):
            quality_score += 0.2  # Explanatory language
        if 'sources:' in answer_lower:
            quality_score += 0.2  # Properly cited

        quality_score = max(1.0, min(5.0, quality_score))  # Clamp to 1-5

        evaluation = {
            "quality_score": quality_score,
            "has_sources": bool(sources),
            "answer_length_category": self._categorize_length(len(answer)),
            "tools_used_count": len(tools_used) if tools_used else 0
        }

        insights = []

        if quality_score >= 4.5:
            insights.append("Excellent answer with comprehensive detail")
        elif quality_score >= 4.0:
            insights.append("High-quality answer with good detail")
        elif quality_score >= 3.5:
            insights.append("Good answer meeting expectations")
        elif quality_score <= 2.0:
            insights.append("Answer may lack detail or have issues")

        if sources:
            insights.append(f"Answer grounded in {len(sources)} source(s)")
        else:
            insights.append("Answer not grounded in retrieved sources")

        reflection = Reflection(
            type=ReflectionType.ANSWER_QUALITY,
            timestamp=datetime.now(),
            context=context,
            evaluation=evaluation,
            insights=insights
        )

        self.reflections.append(reflection)
        self._save_reflection(reflection)
        return reflection

    def reflect_on_error(
        self,
        query: str,
        error: str,
        tool: Optional[str] = None,
        attempted_actions: Optional[List[Dict]] = None
    ) -> Reflection:
        """
        Analyze an error and suggest recovery strategies.

        Args:
            query: User query that caused error
            error: Error message
            tool: Tool that caused the error (if applicable)
            attempted_actions: Actions tried before error

        Returns:
            Reflection on error
        """
        context = {
            "query": query,
            "error": error,
            "tool": tool,
            "attempted_actions": attempted_actions or []
        }

        # Categorize error
        error_category = self._categorize_error(error)

        evaluation = {
            "error_category": error_category,
            "severity": self._assess_error_severity(error),
            "recoverable": self._is_recoverable(error)
        }

        insights = [f"Error category: {error_category}"]
        suggestions = self._suggest_error_recovery(error_category, tool)

        reflection = Reflection(
            type=ReflectionType.ERROR_ANALYSIS,
            timestamp=datetime.now(),
            context=context,
            evaluation=evaluation,
            insights=insights,
            suggestions=suggestions
        )

        self.reflections.append(reflection)
        self._save_reflection(reflection)
        return reflection

    def reflect_on_session(
        self,
        total_queries: int,
        tools_used: Dict[str, int],
        success_rate: float,
        avg_response_time: float
    ) -> Reflection:
        """
        Generate end-of-session performance summary.

        Args:
            total_queries: Number of queries processed
            tools_used: Dictionary of tool usage counts
            success_rate: Percentage of successful interactions
            avg_response_time: Average response time in seconds

        Returns:
            Session summary reflection
        """
        context = {
            "total_queries": total_queries,
            "tools_used": tools_used,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time
        }

        evaluation = {
            "overall_performance": "good" if success_rate >= 0.8 else "needs_improvement",
            "efficiency": "fast" if avg_response_time < 2.0 else "slow",
            "tool_diversity": len(tools_used)
        }

        insights = []

        if success_rate >= 0.9:
            insights.append("Excellent session performance")
        elif success_rate < 0.7:
            insights.append("Several failed interactions - review error patterns")

        if len(tools_used) == 1:
            insights.append("Only one tool used - may need better routing")
        elif len(tools_used) >= 3:
            insights.append("Good tool diversity and routing")

        # Find most used tool
        if tools_used:
            most_used = max(tools_used.items(), key=lambda x: x[1])
            insights.append(f"Most used tool: {most_used[0]} ({most_used[1]} times)")

        reflection = Reflection(
            type=ReflectionType.SESSION_SUMMARY,
            timestamp=datetime.now(),
            context=context,
            evaluation=evaluation,
            insights=insights
        )

        self.reflections.append(reflection)
        self._save_reflection(reflection)
        return reflection

    def get_recent_reflections(self, n: int = 5) -> List[Reflection]:
        """Get the N most recent reflections."""
        return self.reflections[-n:] if len(self.reflections) >= n else self.reflections

    def get_reflections_by_type(self, reflection_type: ReflectionType) -> List[Reflection]:
        """Get all reflections of a specific type."""
        return [r for r in self.reflections if r.type == reflection_type]

    def get_insights_summary(self) -> Dict[str, Any]:
        """Get a summary of all insights learned."""
        tool_selection_insights = []
        answer_quality_insights = []
        error_insights = []

        for reflection in self.reflections:
            if reflection.type == ReflectionType.TOOL_SELECTION:
                tool_selection_insights.extend(reflection.insights)
            elif reflection.type == ReflectionType.ANSWER_QUALITY:
                answer_quality_insights.extend(reflection.insights)
            elif reflection.type == ReflectionType.ERROR_ANALYSIS:
                error_insights.extend(reflection.insights)

        return {
            "total_reflections": len(self.reflections),
            "tool_selection": tool_selection_insights[-5:],  # Last 5
            "answer_quality": answer_quality_insights[-5:],
            "errors": error_insights[-5:]
        }

    # ===== Helper Methods =====

    @staticmethod
    def _categorize_length(length: int) -> str:
        """Categorize answer length."""
        if length < 50:
            return "very_short"
        elif length < 150:
            return "short"
        elif length < 500:
            return "medium"
        elif length < 1000:
            return "long"
        else:
            return "very_long"

    @staticmethod
    def _categorize_error(error: str) -> str:
        """Categorize error type."""
        error_lower = error.lower()

        if "not found" in error_lower or "does not exist" in error_lower:
            return "not_found"
        elif "timeout" in error_lower:
            return "timeout"
        elif "permission" in error_lower or "denied" in error_lower:
            return "permission"
        elif "invalid" in error_lower or "syntax" in error_lower:
            return "invalid_input"
        elif "api" in error_lower or "rate limit" in error_lower:
            return "api_error"
        else:
            return "unknown"

    @staticmethod
    def _assess_error_severity(error: str) -> str:
        """Assess how severe an error is."""
        error_lower = error.lower()

        if any(word in error_lower for word in ["critical", "fatal", "crash"]):
            return "high"
        elif any(word in error_lower for word in ["warning", "deprecated"]):
            return "low"
        else:
            return "medium"

    @staticmethod
    def _is_recoverable(error: str) -> bool:
        """Determine if an error is recoverable."""
        error_lower = error.lower()

        non_recoverable = ["fatal", "crash", "permission denied", "unauthorized"]
        return not any(word in error_lower for word in non_recoverable)

    @staticmethod
    def _suggest_error_recovery(error_category: str, tool: Optional[str]) -> List[str]:
        """Suggest recovery strategies based on error category."""
        suggestions = []

        if error_category == "not_found":
            suggestions.append("Verify the resource exists before accessing")
            suggestions.append("Use file_operations tool to list available resources")

        elif error_category == "timeout":
            suggestions.append("Reduce scope of operation")
            suggestions.append("Implement pagination for large results")

        elif error_category == "permission":
            suggestions.append("Check access permissions")
            suggestions.append("May require user authorization")

        elif error_category == "invalid_input":
            suggestions.append("Validate input format before tool execution")
            suggestions.append("Use LLM to extract and format parameters correctly")

        elif error_category == "api_error":
            suggestions.append("Implement retry with exponential backoff")
            suggestions.append("Check API rate limits and quotas")

        else:
            suggestions.append("Log error details for analysis")
            suggestions.append(f"Review {tool} tool configuration" if tool else "Review tool configuration")

        return suggestions

    def clear(self) -> None:
        """Clear all reflections."""
        with self._buffer_lock:
            self.reflections.clear()
            self._write_buffer.clear()

        # Delete saved reflections file
        if self.reflections_file.exists():
            try:
                self.reflections_file.unlink()
                logger.info("Cleared reflection history from disk")
            except Exception as e:
                logger.warning(f"Could not delete reflections file: {e}")

    def stop(self) -> None:
        """Stop background timer and flush remaining data."""
        if self._flush_timer is not None:
            self._flush_timer.cancel()
            self._flush_timer = None

        self.flush()
