"""Tool registry for managing available tools in the agent."""

from typing import Dict, List, Optional
from .tools.base_tool import BaseTool


class ToolRegistry:
    """
    Registry for managing all tools available to the agent.

    Provides methods to register, retrieve, and list tools.
    """

    def __init__(self):
        """Initialize empty tool registry."""
        self.tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Register a new tool.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If tool with same name already exists
        """
        if tool.name in self.tools:
            raise ValueError(f"Tool with name '{tool.name}' already registered")

        self.tools[tool.name] = tool
        print(f"✓ Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self.tools.get(name)

    def get_all_tools(self) -> List[BaseTool]:
        """
        Get list of all registered tools.

        Returns:
            List of all tool instances
        """
        return list(self.tools.values())

    def get_tool_names(self) -> List[str]:
        """
        Get list of all tool names.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())

    def get_tool_descriptions(self) -> str:
        """
        Get formatted descriptions of all tools for LLM prompt.

        Returns:
            Formatted string with tool names and descriptions
        """
        descriptions = []
        for tool in self.tools.values():
            descriptions.append(f"- {tool.name}: {tool.description}")

        return "\n".join(descriptions)

    def clear(self) -> None:
        """Remove all registered tools."""
        self.tools.clear()

    def __len__(self) -> int:
        """Get number of registered tools."""
        return len(self.tools)

    def __contains__(self, name: str) -> bool:
        """Check if tool name is registered."""
        return name in self.tools

    def __repr__(self) -> str:
        tool_names = ", ".join(self.tools.keys())
        return f"<ToolRegistry(tools=[{tool_names}])>"
