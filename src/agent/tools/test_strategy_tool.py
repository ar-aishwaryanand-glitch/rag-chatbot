"""Test Strategy tool for recommending testing approaches."""

from typing import TYPE_CHECKING, Optional
from .base_tool import BaseTool
from src.logging_config import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from src.rag_chain import RAGChain


class TestStrategyTool(BaseTool):
    """
    Tool for recommending testing strategies and approaches for features.

    Capabilities:
    - Analyze feature/requirement complexity
    - Recommend testing types (unit, integration, E2E, performance)
    - Suggest testing tools and frameworks
    - Identify risk areas and prioritize testing efforts
    - Provide effort estimates for test coverage
    """

    def __init__(self, rag_chain: 'RAGChain'):
        """
        Initialize the Test Strategy tool.

        Args:
            rag_chain: Instance of RAGChain for document retrieval and LLM access
        """
        super().__init__()
        self.rag_chain = rag_chain

    @property
    def name(self) -> str:
        return "test_strategy"

    @property
    def description(self) -> str:
        return """Recommend testing strategies for features or requirements. \
Use when user needs help planning how to test a feature, what types of tests to write, \
or wants to understand testing priorities. Provides testing pyramid recommendations, \
tool suggestions, and risk-based prioritization."""

    def _run(
        self,
        query: str = None,
        feature_description: str = None,
        app_type: Optional[str] = None,
        existing_stack: Optional[str] = None
    ) -> str:
        """
        Generate testing strategy recommendations.

        Args:
            query: Feature description (alias for feature_description, used by agent)
            feature_description: Description of the feature to test
            app_type: Type of application (web, mobile, API, desktop)
            existing_stack: Existing tech stack or testing tools in use

        Returns:
            Comprehensive testing strategy with recommendations
        """
        # Support both 'query' (from agent) and 'feature_description' (direct call)
        description = query or feature_description
        if not description or not description.strip():
            return "Error: Please provide a feature description"

        try:
            # Try to get relevant context from RAG if available
            context = ""
            try:
                docs = self.rag_chain.retrieve_context(description, k=5)
                if docs:
                    context = self.rag_chain.format_context(docs)
            except Exception as e:
                logger.debug(f"RAG context retrieval failed, continuing without context: {e}")

            from langchain_core.prompts import ChatPromptTemplate

            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a Senior QA Architect with expertise in test strategy and quality assurance.

Your task is to create a comprehensive testing strategy for the described feature.

OUTPUT FORMAT:

## Testing Strategy: [Feature Name]

### 1. Feature Analysis
- **Complexity:** Low / Medium / High
- **Risk Level:** Low / Medium / High / Critical
- **Integration Points:** [List systems/components this feature interacts with]
- **User Impact:** [How many users affected, business criticality]

### 2. Testing Pyramid Recommendation

```
        /\\
       /  \\     E2E Tests (10%)
      /----\\    [X tests]
     /      \\
    /--------\\  Integration Tests (20%)
   /          \\ [X tests]
  /------------\\
 /              \\ Unit Tests (70%)
/________________\\ [X tests]
```

### 3. Test Types Required

| Test Type | Priority | Coverage Areas | Estimated Count |
|-----------|----------|----------------|-----------------|
| Unit Tests | High | [Areas] | ~X tests |
| Integration Tests | Medium | [Areas] | ~X tests |
| E2E Tests | Medium | [Areas] | ~X tests |
| API Tests | [Priority] | [Areas] | ~X tests |
| Performance Tests | [Priority] | [Areas] | ~X tests |
| Security Tests | [Priority] | [Areas] | ~X tests |

### 4. Risk-Based Test Prioritization

| Risk Area | Impact | Likelihood | Test Priority |
|-----------|--------|------------|---------------|
| [Area 1] | High/Med/Low | High/Med/Low | P0/P1/P2/P3 |

### 5. Recommended Tools & Frameworks

| Purpose | Recommended Tool | Alternative |
|---------|-----------------|-------------|
| Unit Testing | [Tool] | [Alt] |
| Integration | [Tool] | [Alt] |
| E2E/UI | [Tool] | [Alt] |
| API Testing | [Tool] | [Alt] |
| Performance | [Tool] | [Alt] |

### 6. Test Data Requirements
- [List test data needs]
- [Environment requirements]
- [Mock/stub needs]

### 7. Testing Timeline Estimate

| Phase | Duration | Activities |
|-------|----------|------------|
| Planning | X days | [Activities] |
| Test Development | X days | [Activities] |
| Execution | X days | [Activities] |
| Bug Fixes | X days | [Activities] |

### 8. Key Test Scenarios (High Priority)
1. **[Scenario Name]** - [Brief description]
2. **[Scenario Name]** - [Brief description]
3. **[Scenario Name]** - [Brief description]

### 9. Automation Recommendations
- **Automate:** [What to automate]
- **Keep Manual:** [What to keep manual and why]
- **ROI Consideration:** [Brief automation ROI note]

### 10. Definition of Done (Testing)
- [ ] Unit test coverage >= X%
- [ ] All critical paths have E2E tests
- [ ] Performance benchmarks met
- [ ] Security scan passed
- [ ] No P0/P1 bugs open

Be practical and specific in your recommendations. Consider the application type and existing stack if provided.""" + (f"\n\nAdditional Context from Documentation:\n{context}" if context else "")),
                ("human", """Feature to Test: {description}

Application Type: {app_type}

Existing Tech Stack/Tools: {existing_stack}

Please provide a comprehensive testing strategy.""")
            ])

            messages = prompt.format_messages(
                description=description,
                app_type=app_type if app_type else "Not specified - provide general recommendations",
                existing_stack=existing_stack if existing_stack else "Not specified - suggest common tools"
            )
            response = self.rag_chain.llm.invoke(messages)

            return response.content

        except Exception as e:
            return f"Error generating test strategy: {str(e)}"
