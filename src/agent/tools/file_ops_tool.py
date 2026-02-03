"""File operations tool with workspace restrictions."""

from pathlib import Path
from typing import List, Optional
from .base_tool import BaseTool


class FileOpsTool(BaseTool):
    """
    Tool for file operations within a restricted workspace.

    Operations: read, list, search
    Security: All paths must be within workspace directory
    """

    def __init__(self, workspace_root: Path):
        """
        Initialize file operations tool.

        Args:
            workspace_root: Root directory for file operations (must exist)
        """
        super().__init__()
        self.workspace_root = Path(workspace_root).resolve()

        # Create workspace if it doesn't exist
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "file_operations"

    @property
    def description(self) -> str:
        return """Perform file operations within the workspace directory. \
Available operations: 'read' (read file content), 'list' (list files in directory), \
'search' (search for files by pattern). All paths must be relative to workspace. \
Use for exploring files, reading documents, or finding specific files."""

    def _run(self, operation: str, path: str = ".") -> str:
        """
        Execute file operation.

        Args:
            operation: Operation to perform (read, list, search)
            path: Relative path within workspace

        Returns:
            Result of operation or error message
        """
        # Validate operation parameter
        if not operation or not operation.strip():
            return "Error: Operation cannot be empty"

        operation = operation.lower().strip()

        try:
            # Resolve and validate path
            full_path = (self.workspace_root / path).resolve()

            if not self._is_safe_path(full_path):
                return f"Error: Access denied - path '{path}' is outside workspace"

            # Execute operation
            if operation == "read":
                return self._read_file(full_path)
            elif operation == "list":
                return self._list_directory(full_path)
            elif operation == "search":
                return self._search_files(full_path)
            else:
                return f"Error: Unknown operation '{operation}'. Use: read, list, or search"

        except Exception as e:
            return f"File operation error: {str(e)}"

    def _is_safe_path(self, path: Path) -> bool:
        """
        Check if path is within workspace.

        Args:
            path: Path to check

        Returns:
            True if path is safe
        """
        try:
            path.relative_to(self.workspace_root)
            return True
        except ValueError:
            return False

    def _read_file(self, file_path: Path) -> str:
        """Read file contents with multiple encoding attempts."""
        if not file_path.exists():
            return f"Error: File not found: {file_path.name}"

        # Check for broken symlinks
        if file_path.is_symlink() and not file_path.resolve().exists():
            return f"Error: Broken symlink: {file_path.name}"

        if not file_path.is_file():
            return f"Error: Not a file: {file_path.name}"

        # Try multiple encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

        for encoding in encodings:
            try:
                content = file_path.read_text(encoding=encoding)

                # Limit output size
                max_chars = 5000
                if len(content) > max_chars:
                    content = content[:max_chars] + f"\n\n... (truncated, {len(content)} total chars)"

                return f"File: {file_path.name}\n\n{content}"

            except UnicodeDecodeError:
                continue  # Try next encoding
            except PermissionError:
                return f"Error: Permission denied: {file_path.name}"
            except Exception as e:
                return f"Error reading file: {str(e)}"

        # If all encodings failed, it's likely a binary file
        return f"Error: Cannot read file (appears to be binary or unknown encoding): {file_path.name}"

    def _list_directory(self, dir_path: Path) -> str:
        """List files in directory."""
        if not dir_path.exists():
            # Default to workspace root
            dir_path = self.workspace_root

        if not dir_path.is_dir():
            return f"Error: Not a directory: {dir_path.name}"

        try:
            items = sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))

            if not items:
                return f"Directory '{dir_path.name}' is empty"

            lines = [f"Contents of '{dir_path.name}':\n"]

            for item in items:
                if item.is_dir():
                    lines.append(f"  📁 {item.name}/")
                else:
                    size = item.stat().st_size
                    size_str = self._format_size(size)
                    lines.append(f"  📄 {item.name} ({size_str})")

            return "\n".join(lines)

        except PermissionError:
            return f"Error: Permission denied: {dir_path.name}"

    def _search_files(self, pattern: Path) -> str:
        """Search for files matching pattern."""
        pattern_str = str(pattern)

        # Validate pattern
        if not pattern_str or not pattern_str.strip():
            return "Error: Search pattern cannot be empty"

        try:
            # Escape special glob characters for literal matching
            # But preserve * and ? for wildcards if user intentionally included them
            # For now, use the pattern as-is but catch any errors

            # Use glob from workspace root
            matches = list(self.workspace_root.glob(f"**/*{pattern_str}*"))

            if not matches:
                return f"No files found matching: {pattern_str}"

            lines = [f"Files matching '{pattern_str}':\n"]

            for match in matches[:20]:  # Limit to 20 results
                rel_path = match.relative_to(self.workspace_root)
                if match.is_dir():
                    lines.append(f"  📁 {rel_path}/")
                else:
                    lines.append(f"  📄 {rel_path}")

            if len(matches) > 20:
                lines.append(f"\n... and {len(matches) - 20} more")

            return "\n".join(lines)

        except ValueError as e:
            # Invalid glob pattern
            return f"Search error: Invalid pattern '{pattern_str}'"
        except PermissionError as e:
            return f"Search error: Permission denied while searching"
        except Exception as e:
            return f"Search error: {str(e)}"

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
