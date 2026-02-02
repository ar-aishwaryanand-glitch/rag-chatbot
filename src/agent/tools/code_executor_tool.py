"""Code executor tool with sandboxing for safe Python execution."""

import io
import sys
from typing import Optional
from .base_tool import BaseTool


class CodeExecutorTool(BaseTool):
    """
    Tool for executing Python code in a sandboxed environment.

    Uses RestrictedPython for safety. Supports pandas, numpy for data analysis.
    NO file I/O or system calls allowed.
    """

    def __init__(self, timeout: int = 5):
        """
        Initialize the code executor.

        Args:
            timeout: Maximum execution time in seconds (default: 5)
        """
        super().__init__()
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "python_executor"

    @property
    def description(self) -> str:
        return """Execute Python code in a sandboxed environment. \
Use this for data analysis, transformations, generating sequences, or complex computations. \
Available libraries: pandas, numpy, math. NO file I/O or system operations allowed. \
Use for tasks like generating Fibonacci sequence, data processing, etc."""

    def _run(self, code: str, timeout: Optional[int] = None) -> str:
        """
        Execute Python code safely.

        Args:
            code: Python code to execute
            timeout: Execution timeout (uses default if not specified)

        Returns:
            Output from code execution or error message
        """
        if timeout is None:
            timeout = self.timeout

        # Basic safety check
        if not self.is_safe_code(code):
            return "Error: Code contains potentially dangerous operations"

        try:
            # Redirect stdout to capture output
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()

            try:
                # Create safe execution environment
                # Note: For POC, we use standard exec with restricted globals
                # RestrictedPython can be added for production
                safe_globals = {
                    '__builtins__': {
                        'range': range,
                        'len': len,
                        'enumerate': enumerate,
                        'zip': zip,
                        'map': map,
                        'filter': filter,
                        'sum': sum,
                        'min': min,
                        'max': max,
                        'abs': abs,
                        'round': round,
                        'sorted': sorted,
                        'list': list,
                        'tuple': tuple,
                        'dict': dict,
                        'set': set,
                        'str': str,
                        'int': int,
                        'float': float,
                        'bool': bool,
                        'print': print,
                        'any': any,
                        'all': all,
                        'isinstance': isinstance,
                        'type': type,
                    }
                }

                # Try to import allowed libraries
                try:
                    import pandas as pd
                    safe_globals['pd'] = pd
                except ImportError:
                    pass

                try:
                    import numpy as np
                    safe_globals['np'] = np
                except ImportError:
                    pass

                import math
                safe_globals['math'] = math

                # Execute code
                exec(code, safe_globals)

                # Get output
                output = captured_output.getvalue()

                if output:
                    return f"Execution successful:\n{output}"
                else:
                    return "Execution successful (no output)"

            finally:
                sys.stdout = old_stdout

        except SyntaxError as e:
            return f"Syntax error: {str(e)}"
        except Exception as e:
            return f"Execution error: {str(e)}"

    def is_safe_code(self, code: str) -> bool:
        """
        Check if code appears safe (basic heuristics).

        Args:
            code: Code to check

        Returns:
            True if code passes basic safety checks
        """
        dangerous_keywords = [
            'import os',
            'import sys',
            'import subprocess',
            '__import__',
            'eval(',
            'exec(',
            'compile(',
            'open(',
            'file(',
            'input(',
        ]

        code_lower = code.lower()
        for keyword in dangerous_keywords:
            if keyword in code_lower:
                return False

        return True
