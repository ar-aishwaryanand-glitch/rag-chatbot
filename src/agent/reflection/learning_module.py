"""Learning module for extracting patterns from reflections."""

from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
from pathlib import Path
import pickle
from .reflection_module import Reflection, ReflectionType


class LearningModule:
    """
    Learns from reflections to improve future performance.

    Tracks:
    - Tool performance metrics
    - Success/failure patterns
    - Common errors
    - Optimal routing strategies
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize learning module with persistence.

        Args:
            storage_path: Path to store learning data (default: data/learning)
        """
        # Set up storage
        if storage_path is None:
            storage_path = Path(__file__).parent.parent.parent.parent / "data" / "learning"

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.data_file = self.storage_path / "learning_data.pkl"

        # Tool performance tracking
        self.tool_usage = Counter()  # tool_name -> count
        self.tool_success = defaultdict(list)  # tool_name -> [success_bools]
        self.tool_response_times = defaultdict(list)  # tool_name -> [durations]

        # Query patterns
        self.query_tool_mapping = defaultdict(Counter)  # query_type -> {tool: count}

        # Error tracking
        self.error_patterns = Counter()  # error_category -> count
        self.tool_errors = defaultdict(Counter)  # tool_name -> {error_category: count}

        # Quality metrics
        self.quality_scores = []  # List of quality scores

        # Load existing data if available
        self._load_data()

    def _load_data(self) -> None:
        """Load learning data from disk."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'rb') as f:
                    data = pickle.load(f)

                # Restore Counter objects
                self.tool_usage = Counter(data.get('tool_usage', {}))
                self.error_patterns = Counter(data.get('error_patterns', {}))

                # Restore defaultdicts
                self.tool_success = defaultdict(list, data.get('tool_success', {}))
                self.tool_response_times = defaultdict(list, data.get('tool_response_times', {}))
                self.tool_errors = defaultdict(Counter, {
                    k: Counter(v) for k, v in data.get('tool_errors', {}).items()
                })

                # Restore query_tool_mapping
                self.query_tool_mapping = defaultdict(Counter, {
                    k: Counter(v) for k, v in data.get('query_tool_mapping', {}).items()
                })

                # Restore simple list
                self.quality_scores = data.get('quality_scores', [])

                tools_count = len(self.tool_usage)
                total_actions = sum(self.tool_usage.values())
                print(f"📊 Loaded learning data: {tools_count} tools tracked, {total_actions} total actions")

            except Exception as e:
                print(f"⚠️  Warning: Could not load learning data: {e}")
                print("   Starting with fresh learning data")

    def _save_data(self) -> None:
        """Save learning data to disk."""
        try:
            # Convert data structures to serializable format
            data = {
                'tool_usage': dict(self.tool_usage),
                'tool_success': dict(self.tool_success),
                'tool_response_times': dict(self.tool_response_times),
                'query_tool_mapping': {k: dict(v) for k, v in self.query_tool_mapping.items()},
                'error_patterns': dict(self.error_patterns),
                'tool_errors': {k: dict(v) for k, v in self.tool_errors.items()},
                'quality_scores': self.quality_scores
            }

            with open(self.data_file, 'wb') as f:
                pickle.dump(data, f)

        except Exception as e:
            print(f"⚠️  Warning: Could not save learning data: {e}")

    def learn_from_reflection(self, reflection: Reflection) -> None:
        """
        Extract learning from a reflection.

        Args:
            reflection: Reflection to learn from
        """
        if reflection.type == ReflectionType.TOOL_SELECTION:
            self._learn_tool_selection(reflection)

        elif reflection.type == ReflectionType.ANSWER_QUALITY:
            self._learn_answer_quality(reflection)

        elif reflection.type == ReflectionType.ERROR_ANALYSIS:
            self._learn_from_error(reflection)

        # Save data after learning
        self._save_data()

    def learn_from_reflections(self, reflections: List[Reflection]) -> None:
        """Learn from multiple reflections."""
        for reflection in reflections:
            self.learn_from_reflection(reflection)

    def _learn_tool_selection(self, reflection: Reflection) -> None:
        """Learn from tool selection reflection."""
        context = reflection.context
        tool = context.get("selected_tool")
        success = context.get("tool_success", False)

        if tool:
            self.tool_usage[tool] += 1
            self.tool_success[tool].append(success)

            # Extract query type (simple keyword-based for now)
            query = context.get("query", "").lower()
            query_type = self._categorize_query(query)
            self.query_tool_mapping[query_type][tool] += 1

    def _learn_answer_quality(self, reflection: Reflection) -> None:
        """Learn from answer quality reflection."""
        evaluation = reflection.evaluation
        quality_score = evaluation.get("quality_score")

        if quality_score is not None:
            self.quality_scores.append(quality_score)

    def _learn_from_error(self, reflection: Reflection) -> None:
        """Learn from error reflection."""
        context = reflection.context
        evaluation = reflection.evaluation

        error_category = evaluation.get("error_category", "unknown")
        tool = context.get("tool")

        self.error_patterns[error_category] += 1

        if tool:
            self.tool_errors[tool][error_category] += 1

    def get_tool_performance(self, tool_name: str) -> Dict[str, Any]:
        """
        Get performance metrics for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Dictionary with performance metrics
        """
        usage_count = self.tool_usage.get(tool_name, 0)
        successes = self.tool_success.get(tool_name, [])
        response_times = self.tool_response_times.get(tool_name, [])

        success_rate = sum(successes) / len(successes) if successes else 0.0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0

        return {
            "usage_count": usage_count,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "total_errors": sum(self.tool_errors[tool_name].values())
        }

    def get_best_tool_for_query_type(self, query_type: str) -> str:
        """
        Get the tool that performs best for a query type.

        Args:
            query_type: Type of query

        Returns:
            Name of best tool for this query type
        """
        if query_type not in self.query_tool_mapping:
            return None

        # Get tool with highest success rate for this query type
        tool_counts = self.query_tool_mapping[query_type]

        if not tool_counts:
            return None

        # Simple heuristic: most used tool
        return tool_counts.most_common(1)[0][0]

    def get_common_errors(self, top_n: int = 5) -> List[tuple]:
        """
        Get the most common error categories.

        Args:
            top_n: Number of top errors to return

        Returns:
            List of (error_category, count) tuples
        """
        return self.error_patterns.most_common(top_n)

    def get_tool_error_profile(self, tool_name: str) -> Dict[str, int]:
        """
        Get error profile for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Dictionary of error categories and counts
        """
        return dict(self.tool_errors.get(tool_name, {}))

    def get_overall_performance(self) -> Dict[str, Any]:
        """Get overall system performance metrics."""
        total_actions = sum(self.tool_usage.values())
        total_successes = sum(sum(successes) for successes in self.tool_success.values())
        total_failures = sum(len(successes) for successes in self.tool_success.values()) - total_successes

        avg_quality = sum(self.quality_scores) / len(self.quality_scores) if self.quality_scores else 0.0

        return {
            "total_actions": total_actions,
            "total_successes": total_successes,
            "total_failures": total_failures,
            "success_rate": total_successes / (total_successes + total_failures) if (total_successes + total_failures) > 0 else 0.0,
            "avg_quality_score": avg_quality,
            "unique_tools_used": len(self.tool_usage),
            "total_error_types": len(self.error_patterns),
            "most_common_error": self.error_patterns.most_common(1)[0] if self.error_patterns else None
        }

    def get_tool_ranking(self) -> List[tuple]:
        """
        Rank tools by performance (usage * success_rate).

        Returns:
            List of (tool_name, score) tuples, sorted by score
        """
        rankings = []

        for tool_name in self.tool_usage.keys():
            metrics = self.get_tool_performance(tool_name)
            score = metrics["usage_count"] * metrics["success_rate"]
            rankings.append((tool_name, score))

        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get comprehensive learning summary."""
        return {
            "overall_performance": self.get_overall_performance(),
            "tool_rankings": self.get_tool_ranking(),
            "common_errors": self.get_common_errors(top_n=3),
            "avg_quality_score": sum(self.quality_scores) / len(self.quality_scores) if self.quality_scores else 0.0,
            "query_types_learned": len(self.query_tool_mapping)
        }

    @staticmethod
    def _categorize_query(query: str) -> str:
        """
        Categorize query type based on keywords.

        Args:
            query: User query

        Returns:
            Query type category
        """
        query_lower = query.lower()

        # Math/calculation
        if any(word in query_lower for word in ["calculate", "compute", "multiply", "divide", "add", "subtract"]):
            return "calculation"

        # Programming/code
        if any(word in query_lower for word in ["python", "code", "execute", "run", "script", "program"]):
            return "code_execution"

        # File operations
        if any(word in query_lower for word in ["file", "read", "list", "directory", "folder"]):
            return "file_operation"

        # Web search
        if any(word in query_lower for word in ["current", "latest", "today", "weather", "news", "recent"]):
            return "web_search"

        # Document management
        if any(word in query_lower for word in ["documents", "indexed", "stats", "collection"]):
            return "document_management"

        # Default to document search
        return "document_search"

    def clear(self) -> None:
        """Clear all learning data."""
        self.tool_usage.clear()
        self.tool_success.clear()
        self.tool_response_times.clear()
        self.query_tool_mapping.clear()
        self.error_patterns.clear()
        self.tool_errors.clear()
        self.quality_scores.clear()

        # Delete saved data file
        if self.data_file.exists():
            try:
                self.data_file.unlink()
                print("🗑️  Cleared learning data from disk")
            except Exception as e:
                print(f"⚠️  Warning: Could not delete learning data file: {e}")
