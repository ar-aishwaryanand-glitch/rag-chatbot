"""Calculator tool for mathematical computations."""

import math
from .base_tool import BaseTool


class CalculatorTool(BaseTool):
    """
    Tool for performing mathematical calculations.

    Supports basic arithmetic, algebra, and common math functions.
    Uses numexpr for safe evaluation.
    """

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return """Perform mathematical calculations and evaluate expressions. \
Supports basic arithmetic (+, -, *, /, **), algebra, and math functions (sqrt, sin, cos, tan, log). \
Use this for numerical computations, math problems, or when the question involves calculations."""

    def _run(self, expression: str) -> str:
        """
        Evaluate a mathematical expression.

        Args:
            expression: Mathematical expression to evaluate

        Returns:
            Result of the calculation or error message
        """
        try:
            import numexpr

            # Create safe context with math functions
            safe_dict = {
                'sqrt': math.sqrt,
                'log': math.log,
                'log10': math.log10,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'asin': math.asin,
                'acos': math.acos,
                'atan': math.atan,
                'sinh': math.sinh,
                'cosh': math.cosh,
                'tanh': math.tanh,
                'exp': math.exp,
                'abs': abs,
                'pi': math.pi,
                'e': math.e,
            }

            # Clean the expression
            expression = expression.strip()

            # Evaluate using numexpr
            result = numexpr.evaluate(expression, local_dict=safe_dict)

            return f"Result: {result}"

        except ImportError:
            return "Error: numexpr package not installed. Install with: pip install numexpr"
        except Exception as e:
            return f"Calculation error: {str(e)}\nPlease check the expression syntax."

    def test_expression(self, expression: str) -> bool:
        """
        Test if an expression is valid without evaluating.

        Args:
            expression: Expression to test

        Returns:
            True if valid, False otherwise
        """
        try:
            import numexpr
            numexpr.validate(expression)
            return True
        except:
            return False
