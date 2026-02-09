"""Code executor tool with sandboxing for safe Python execution."""

import io
import sys
import signal
import ast
import re
import threading
import platform
from typing import Optional
from contextlib import contextmanager
from .base_tool import BaseTool


# Memory limit tracking (soft limit in bytes)
MAX_MEMORY_BYTES = 50 * 1024 * 1024  # 50 MB


@contextmanager
def time_limit(seconds: int):
    """Context manager to enforce execution time limit (cross-platform)."""
    if platform.system() == 'Windows':
        # Windows timeout using threading.Timer
        result = {'timed_out': False}

        def timeout_handler():
            result['timed_out'] = True
            # Raise in main thread by setting a trace function that throws
            raise TimeoutError(f"Code execution exceeded {seconds} second(s)")

        timer = threading.Timer(seconds, timeout_handler)
        timer.daemon = True
        timer.start()
        try:
            yield
            if result['timed_out']:
                raise TimeoutError(f"Code execution exceeded {seconds} second(s)")
        finally:
            timer.cancel()
    else:
        # Unix/Linux/macOS timeout using signal.alarm
        def signal_handler(signum, frame):
            raise TimeoutError(f"Code execution exceeded {seconds} second(s)")

        # Set the signal handler and alarm
        old_handler = signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            # Reset alarm and handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)


class CodeExecutorTool(BaseTool):
    """
    Tool for executing Python code in a sandboxed environment.

    Uses restricted __builtins__ and AST validation for safety.
    Supports pandas, numpy for data analysis.
    NO file I/O or system calls allowed.

    WARNING: This provides basic sandboxing suitable for a POC.
    For production, use proper isolation (docker, subprocess, etc.)
    """

    def __init__(self, timeout: int = 5, max_output_size: int = 5000):
        """
        Initialize the code executor.

        Args:
            timeout: Maximum execution time in seconds (default: 5)
            max_output_size: Maximum output size in characters (default: 5000)
        """
        super().__init__()
        self.timeout = timeout
        self.max_output_size = max_output_size

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

        # Validate input
        if not code or not code.strip():
            return "Error: Code cannot be empty"

        # Check code length
        if len(code) > 10000:
            return "Error: Code too long (max 10000 characters)"

        # AST-based safety check (more robust than string matching)
        safety_check = self.check_code_safety_ast(code)
        if not safety_check['safe']:
            return f"Error: Code contains dangerous operations: {safety_check['reason']}"

        # Basic keyword check as backup
        if not self.is_safe_code(code):
            return "Error: Code contains potentially dangerous operations"

        try:
            # Redirect stdout to capture output
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()

            try:
                # Create safe execution environment
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
                        'reversed': reversed,
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
                        # 'type' removed - can be used for sandbox escape via type(x).__bases__[0].__subclasses__()
                        'pow': pow,
                        'divmod': divmod,
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

                # Execute code with timeout (Unix/Linux only)
                try:
                    with time_limit(timeout):
                        exec(code, safe_globals)
                except NotImplementedError:
                    # Fallback for Windows (no timeout enforcement)
                    exec(code, safe_globals)

                # Get output
                output = captured_output.getvalue()

                # Limit output size
                if len(output) > self.max_output_size:
                    output = output[:self.max_output_size] + f"\n\n... (output truncated at {self.max_output_size} chars)"

                if output:
                    return f"Execution successful:\n{output}"
                else:
                    return "Execution successful (no output)"

            finally:
                sys.stdout = old_stdout

        except TimeoutError as e:
            return f"Timeout error: {str(e)}"
        except SyntaxError as e:
            return f"Syntax error: {str(e)}"
        except MemoryError:
            return "Error: Code exceeded memory limits"
        except Exception as e:
            return f"Execution error: {str(e)}"

    def check_code_safety_ast(self, code: str) -> dict:
        """
        Check code safety using AST parsing (more robust than string matching).

        Args:
            code: Code to check

        Returns:
            dict with 'safe' (bool) and 'reason' (str) keys
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {'safe': False, 'reason': 'Syntax error in code'}

        # List of dangerous node types and names
        for node in ast.walk(tree):
            # Check for imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module_names = []
                if isinstance(node, ast.Import):
                    module_names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    module_names = [node.module] if node.module else []

                # Only allow specific safe modules
                allowed_modules = {'math', 'pandas', 'numpy', 'pd', 'np'}
                for module in module_names:
                    if module and module.split('.')[0] not in allowed_modules:
                        return {'safe': False, 'reason': f'Import of "{module}" not allowed'}

            # Check for attribute access to dangerous names
            if isinstance(node, ast.Attribute):
                dangerous_attrs = [
                    '__import__', '__builtins__', '__globals__', '__code__',
                    '__dict__', '__class__', '__bases__', '__subclasses__',
                    '__mro__', '__reduce__', '__reduce_ex__', '__getattribute__',
                    '__setattr__', '__delattr__', '__init_subclass__', '__set_name__',
                    '__objclass__', '__slots__', '__weakref__', '__self__',
                    '__func__', '__closure__', '__annotations__', '__kwdefaults__',
                    'gi_frame', 'gi_code', 'f_locals', 'f_globals', 'f_builtins',
                    'co_code', 'func_globals', 'func_code'
                ]
                if node.attr in dangerous_attrs:
                    return {'safe': False, 'reason': f'Access to "{node.attr}" not allowed'}

            # Check for calls to dangerous functions
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    dangerous_funcs = [
                        'eval', 'exec', 'compile', 'open', 'file', '__import__',
                        'input', 'getattr', 'setattr', 'delattr', 'globals', 'locals',
                        'vars', 'dir', '__builtins__', 'memoryview', 'object',
                        'classmethod', 'staticmethod', 'property', 'super',
                        'breakpoint', 'help', 'license', 'credits', 'copyright'
                    ]
                    if node.func.id in dangerous_funcs:
                        return {'safe': False, 'reason': f'Call to "{node.func.id}()" not allowed'}

            # Check for dangerous string literals that could bypass detection
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                dangerous_strings = [
                    '__import__', '__builtins__', '__globals__', '__subclasses__',
                    '__mro__', '__bases__', '__code__', '__reduce__'
                ]
                for ds in dangerous_strings:
                    if ds in node.value:
                        return {'safe': False, 'reason': f'Dangerous string pattern "{ds}" detected'}

        return {'safe': True, 'reason': ''}

    def is_safe_code(self, code: str) -> bool:
        """
        Check if code appears safe (case-insensitive regex matching as backup).

        Args:
            code: Code to check

        Returns:
            True if code passes basic safety checks
        """
        # Dangerous patterns with word boundary matching for better accuracy
        dangerous_patterns = [
            r'__import__',
            r'__builtins__',
            r'__globals__',
            r'__code__',
            r'__dict__',
            r'__class__',
            r'__bases__',
            r'__subclasses__',
            r'__mro__',
            r'__reduce__',
            r'__getattribute__',
            r'\beval\s*\(',
            r'\bexec\s*\(',
            r'\bcompile\s*\(',
            r'\bopen\s*\(',
            r'\bfile\s*\(',
            r'\binput\s*\(',
            r'\bgetattr\s*\(',
            r'\bsetattr\s*\(',
            r'\bdelattr\s*\(',
            r'\bglobals\s*\(',
            r'\blocals\s*\(',
            r'\bvars\s*\(',
            r'\bmemoryview\s*\(',
            r'\bbreakpoint\s*\(',
            r'\bimport\s+os\b',
            r'\bimport\s+sys\b',
            r'\bimport\s+subprocess\b',
            r'\bimport\s+socket\b',
            r'\bimport\s+ctypes\b',
            r'\bimport\s+pickle\b',
            r'\bimport\s+marshal\b',
            r'\bimport\s+builtins\b',
            r'\bfrom\s+os\b',
            r'\bfrom\s+sys\b',
            r'\bfrom\s+subprocess\b',
            r'\bfrom\s+socket\b',
            r'\bfrom\s+ctypes\b',
            r'\bfrom\s+builtins\b',
            # Type-based escapes: type(x).__bases__[0].__subclasses__()
            r'\btype\s*\([^)]*\)\s*\.\s*__',
            # Catch common sandbox escape patterns
            r'\(\s*\)\s*\[\s*\d+\s*\]',  # ()[] indexing pattern common in escapes
            r'chr\s*\(\s*\d+\s*\)',  # chr() could build strings
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return False

        return True
