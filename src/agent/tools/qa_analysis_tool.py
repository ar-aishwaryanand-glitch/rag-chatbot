"""QA Analysis tool for test case gap analysis and improvements."""

from typing import TYPE_CHECKING, Optional
from .base_tool import BaseTool
from src.logging_config import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from src.rag_chain import RAGChain


class QAAnalysisTool(BaseTool):
    """
    Tool for analyzing test cases to find coverage gaps and suggest improvements.

    Capabilities:
    - Analyze test cases against requirements
    - Identify missing scenarios (edge cases, negative, boundary)
    - Suggest improvements to existing test cases
    - Highlight risk areas without adequate test coverage
    """

    def __init__(self, rag_chain: 'RAGChain'):
        """
        Initialize the QA Analysis tool.

        Args:
            rag_chain: Instance of RAGChain for document retrieval and LLM access
        """
        super().__init__()
        self.rag_chain = rag_chain

    @property
    def name(self) -> str:
        return "qa_analysis"

    @property
    def description(self) -> str:
        return """Analyze test cases to find coverage gaps, missing scenarios, and suggest improvements. \
Use when user wants to: review test cases, find gaps in test coverage, identify missing edge cases, \
or improve existing test cases. Provide test cases as input for analysis."""

    def _run(self, query: str = None, test_cases: str = None, requirements: Optional[str] = None) -> str:
        """
        Analyze test cases and provide gap analysis.

        Args:
            query: Test cases to analyze (alias for test_cases, used by agent)
            test_cases: Test cases to analyze (pasted text or description)
            requirements: Optional requirements context for comparison

        Returns:
            Formatted analysis with gaps, missing scenarios, and improvements
        """
        # Support both 'query' (from agent) and 'test_cases' (direct call)
        cases = query or test_cases
        if not cases or not cases.strip():
            return "Error: Please provide test cases to analyze"

        try:
            # Build the analysis prompt
            analysis_prompt = self._build_analysis_prompt(cases, requirements)

            # If requirements provided, try to get context from RAG
            context = ""
            if requirements:
                try:
                    docs = self.rag_chain.retrieve_context(requirements, k=5)
                    if docs:
                        context = self.rag_chain.format_context(docs)
                except Exception as e:
                    logger.debug(f"RAG context retrieval failed, continuing without context: {e}")

            # Use LLM to analyze
            from langchain_core.prompts import ChatPromptTemplate

            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert QA Engineer specializing in test case analysis and quality assurance.

Your task is to analyze the provided test cases and identify:
1. **Coverage Gaps** - Requirements or features not covered by tests
2. **Missing Scenarios** - Edge cases, negative tests, boundary conditions not tested
3. **Improvement Suggestions** - How to make existing tests more robust
4. **Risk Areas** - High-risk functionality with inadequate testing

OUTPUT FORMAT:
## Test Coverage Analysis

### Coverage Gaps
- [List areas not covered by current tests]

### Missing Scenarios
- **Edge Cases:** [List missing edge case tests]
- **Negative Tests:** [List missing error/failure scenarios]
- **Boundary Conditions:** [List missing boundary tests]

### Improvement Suggestions
- [Specific improvements for existing test cases]

### Risk Assessment
| Area | Risk Level | Recommendation |
|------|------------|----------------|
| [Feature] | High/Medium/Low | [What to test] |

### Recommended Additional Test Cases
1. [New test case suggestion with Given/When/Then]
2. [Another suggestion]

Be specific and actionable in your recommendations.""" + (f"\n\nRequirements Context:\n{context}" if context else "")),
                ("human", "{test_cases}")
            ])

            messages = prompt.format_messages(test_cases=analysis_prompt)
            response = self.rag_chain.llm.invoke(messages)

            return response.content

        except Exception as e:
            return f"Error analyzing test cases: {str(e)}"

    def _build_analysis_prompt(self, test_cases: str, requirements: Optional[str] = None) -> str:
        """Build the analysis prompt from inputs."""
        prompt_parts = [f"Test Cases to Analyze:\n{test_cases}"]

        if requirements:
            prompt_parts.append(f"\nRequirements/Feature Context:\n{requirements}")

        prompt_parts.append("\nPlease analyze these test cases for coverage gaps and improvements.")

        return "\n".join(prompt_parts)
