"""Reflection module for agent self-evaluation."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


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


class ReflectionModule:
    """
    Evaluates agent performance and generates insights.

    Features:
    - Tool selection evaluation
    - Answer quality assessment
    - Error analysis and recovery
    - Performance tracking
    """

    def __init__(self, llm=None):
        """
        Initialize reflection module.

        Args:
            llm: Optional LLM for generating reflections (can work without)
        """
        self.llm = llm
        self.reflections: List[Reflection] = []

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
            suggestions.append(f"Consider trying alternative tools for similar queries")

        reflection = Reflection(
            type=ReflectionType.TOOL_SELECTION,
            timestamp=datetime.now(),
            context=context,
            evaluation=evaluation,
            insights=insights,
            suggestions=suggestions
        )

        self.reflections.append(reflection)
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

        # Simple heuristic evaluation
        quality_score = 3.0  # Default: moderate

        # Adjust based on answer characteristics
        if len(answer) < 20:
            quality_score -= 1.0
        elif len(answer) > 100:
            quality_score += 0.5

        if sources and len(sources) > 0:
            quality_score += 0.5

        if "error" in answer.lower() or "failed" in answer.lower():
            quality_score -= 1.0

        quality_score = max(1.0, min(5.0, quality_score))  # Clamp to 1-5

        evaluation = {
            "quality_score": quality_score,
            "has_sources": bool(sources),
            "answer_length_category": self._categorize_length(len(answer))
        }

        insights = []

        if quality_score >= 4.0:
            insights.append("High-quality answer with good detail")
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
        self.reflections.clear()
