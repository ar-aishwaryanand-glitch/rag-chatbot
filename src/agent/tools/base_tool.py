"""Base tool class for all agent tools."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel, Field
import time


class ToolResult(BaseModel):
    """Result from a tool execution."""
    success: bool
    output: str
    error: Optional[str] = None
    duration: float
    metadata: dict = Field(default_factory=dict)


class BaseTool(ABC):
    """
    Base class for all tools in the agentic system.

    Each tool must implement:
    - name: Unique identifier
    - description: What the tool does (used by LLM for selection)
    - _run(): Core execution logic
    """

    def __init__(self):
        """Initialize the tool."""
        self.call_count = 0

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the tool does (for LLM)."""
        pass

    @abstractmethod
    def _run(self, *args, **kwargs) -> str:
        """
        Core execution logic.

        Returns:
            str: Tool output as string
        """
        pass

    def run(self, *args, **kwargs) -> ToolResult:
        """
        Execute the tool with timing and error handling.

        Returns:
            ToolResult: Structured result with success/error info
        """
        self.call_count += 1
        start_time = time.time()

        try:
            output = self._run(*args, **kwargs)
            duration = time.time() - start_time

            return ToolResult(
                success=True,
                output=output,
                duration=duration,
                metadata={'call_count': self.call_count}
            )

        except Exception as e:
            duration = time.time() - start_time

            return ToolResult(
                success=False,
                output="",
                error=str(e),
                duration=duration,
                metadata={'call_count': self.call_count}
            )

    def __str__(self) -> str:
        return f"{self.name}: {self.description}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
