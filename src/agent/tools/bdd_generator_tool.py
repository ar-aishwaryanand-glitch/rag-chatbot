"""BDD/Gherkin Generator Tool - Generate executable .feature files."""

from typing import TYPE_CHECKING, Optional
from .base_tool import BaseTool
import re

if TYPE_CHECKING:
    from src.rag_chain import RAGChain


class BDDGeneratorTool(BaseTool):
    """
    Tool for generating BDD/Gherkin .feature files.

    Capabilities:
    - Generate Cucumber/Behave compatible .feature files
    - Create scenarios with Given/When/Then steps
    - Include Background, Scenario Outline, and Examples
    - Support tags for organization
    """

    def __init__(self, rag_chain: 'RAGChain'):
        super().__init__()
        self.rag_chain = rag_chain

    @property
    def name(self) -> str:
        return "bdd_generator"

    @property
    def description(self) -> str:
        return """Generate BDD/Gherkin .feature files from requirements or feature descriptions. \
Use when user wants to: create executable BDD scenarios, generate Cucumber/Behave tests, \
write Given/When/Then specifications, or create behavior-driven test files."""

    def _run(
        self,
        query: str = None,
        feature_description: str = None,
        framework: str = "cucumber",
        include_examples: bool = True
    ) -> str:
        """
        Generate BDD feature file content.

        Args:
            query: Feature description (alias for feature_description)
            feature_description: Description of feature to generate tests for
            framework: "cucumber" (Java/JS) or "behave" (Python)
            include_examples: Include Scenario Outline with Examples tables

        Returns:
            Complete .feature file content
        """
        description = query or feature_description
        if not description or not description.strip():
            return "Error: Please provide a feature description or requirements"

        try:
            # Try to get relevant context from RAG
            context = ""
            try:
                docs = self.rag_chain.retrieve_context(description, k=10)
                if docs:
                    context = self.rag_chain.format_context(docs)
            except Exception:
                pass

            from langchain_core.prompts import ChatPromptTemplate

            framework_notes = self._get_framework_notes(framework)

            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are a BDD Expert specializing in Gherkin syntax.

Generate a complete, executable .feature file.

**GHERKIN RULES:**
1. Start with `Feature:` followed by descriptive title
2. Include feature narrative (As a/I want/So that)
3. Use `Background:` for common preconditions
4. Write `Scenario:` for each test case
5. Use `Scenario Outline:` with `Examples:` for data-driven tests
6. Steps: Given/When/Then/And/But
7. Use @tags for organization

{framework_notes}

**SCENARIO TYPES TO INCLUDE:**
- Happy path (positive scenarios)
- Error handling (negative scenarios)
- Edge cases
- Data-driven tests (Scenario Outline)

**OUTPUT:**
Generate ONLY the .feature file content. No markdown code blocks.

Example:
@feature-tag
Feature: Feature Title
  As a [role]
  I want [feature]
  So that [benefit]

  Background:
    Given common precondition

  @smoke @positive
  Scenario: Happy path
    Given initial state
    When action performed
    Then expected outcome

  @negative
  Scenario: Error case
    Given initial state
    When invalid action
    Then error displayed

  @data-driven
  Scenario Outline: Parameterized test
    Given user has "<role>" permissions
    When user attempts "<action>"
    Then result is "<expected>"

    Examples:
      | role   | action      | expected      |
      | admin  | delete      | success       |
      | viewer | delete      | access_denied |

Make scenarios specific, testable, and use business language."""),
                ("human", """Feature/Requirements:
{description}

Framework: {framework}
Include Scenario Outlines: {include_examples}

{context_section}

Generate the .feature file:""")
            ])

            context_section = f"Additional Context:\n{context[:6000]}" if context else ""

            messages = prompt.format_messages(
                description=description,
                framework=framework,
                include_examples="Yes" if include_examples else "No",
                context_section=context_section
            )

            response = self.rag_chain.llm.invoke(messages)

            # Clean up the output
            feature_content = self._clean_feature_output(response.content)

            # Validate basic Gherkin syntax
            validation_notes = self._validate_gherkin(feature_content)
            if validation_notes:
                feature_content += f"\n\n# Validation Notes: {validation_notes}"

            return feature_content

        except Exception as e:
            return f"Error generating BDD feature file: {str(e)}"

    def _get_framework_notes(self, framework: str) -> str:
        """Get framework-specific notes."""
        if framework.lower() == "behave":
            return """**BEHAVE (Python) Notes:**
- Step definitions in features/steps/*.py
- Use @given, @when, @then decorators
- Context object passed to steps
- Hooks in environment.py"""
        else:
            return """**CUCUMBER Notes:**
- Works with Java, JavaScript, Ruby
- Step definitions use regex/cucumber expressions
- Support for @Before/@After hooks
- Data tables and doc strings supported"""

    def _clean_feature_output(self, content: str) -> str:
        """Clean up LLM output to pure Gherkin."""
        # Remove markdown code blocks
        content = re.sub(r'^```(?:gherkin|feature)?\s*\n?', '', content.strip())
        content = re.sub(r'^```\s*\n?', '', content)
        content = re.sub(r'\n?```\s*$', '', content)
        return content.strip()

    def _validate_gherkin(self, content: str) -> Optional[str]:
        """
        Comprehensive Gherkin validation.

        Validates:
        - Required keywords (Feature, Scenario)
        - Step keywords (Given, When, Then)
        - Scenario Outline has Examples
        - Tag format (@tag)
        - Basic structural rules
        """
        issues = []
        warnings = []
        lines = content.split('\n')

        # 1. Feature keyword validation
        feature_match = re.search(r'^\s*Feature:\s*(.+)$', content, re.MULTILINE)
        if not feature_match:
            issues.append("Missing 'Feature:' keyword")
        elif not feature_match.group(1).strip():
            warnings.append("Feature has no title")

        # 2. Scenario validation
        scenario_count = len(re.findall(r'^\s*Scenario:', content, re.MULTILINE))
        scenario_outline_count = len(re.findall(r'^\s*Scenario Outline:', content, re.MULTILINE))

        if scenario_count == 0 and scenario_outline_count == 0:
            issues.append("No scenarios defined")

        # 3. Step keyword validation
        step_keywords = ['Given', 'When', 'Then', 'And', 'But']
        has_given = bool(re.search(r'^\s*(Given)\s+.+', content, re.MULTILINE))
        has_when = bool(re.search(r'^\s*(When)\s+.+', content, re.MULTILINE))
        has_then = bool(re.search(r'^\s*(Then)\s+.+', content, re.MULTILINE))

        if not has_given:
            warnings.append("No 'Given' steps found")
        if not has_when:
            warnings.append("No 'When' steps found")
        if not has_then:
            issues.append("No 'Then' steps found (required for assertions)")

        # 4. Scenario Outline must have Examples
        if scenario_outline_count > 0:
            examples_count = len(re.findall(r'^\s*Examples:', content, re.MULTILINE))
            if examples_count < scenario_outline_count:
                issues.append("Scenario Outline missing 'Examples:' table")

            # Check for placeholder syntax in Scenario Outline
            outline_sections = re.findall(
                r'Scenario Outline:.*?(?=\n\s*(?:Scenario|Feature|$))',
                content,
                re.DOTALL
            )
            for outline in outline_sections:
                if '<' not in outline or '>' not in outline:
                    warnings.append("Scenario Outline may be missing <placeholder> syntax")
                    break

        # 5. Tag format validation
        tags = re.findall(r'@\S+', content)
        for tag in tags:
            if not re.match(r'^@[a-zA-Z][a-zA-Z0-9_-]*$', tag):
                warnings.append(f"Invalid tag format: {tag}")
                break  # Only report once

        # 6. Check for empty scenarios (scenario with no steps)
        scenario_blocks = re.split(r'^\s*(?:Scenario:|Scenario Outline:)', content, flags=re.MULTILINE)
        for i, block in enumerate(scenario_blocks[1:], 1):  # Skip first element (before first scenario)
            # Get content before next scenario or end
            block_content = block.split('Scenario:')[0].split('Scenario Outline:')[0]
            has_step = any(
                re.search(rf'^\s*{kw}\s+', block_content, re.MULTILINE)
                for kw in step_keywords
            )
            if not has_step:
                warnings.append(f"Scenario {i} has no steps")
                break

        # 7. Check for Background usage
        background_count = len(re.findall(r'^\s*Background:', content, re.MULTILINE))
        if background_count > 1:
            issues.append("Multiple Background sections (only one allowed)")

        # Compile results
        result_parts = []
        if issues:
            result_parts.append(f"ERRORS: {'; '.join(issues)}")
        if warnings:
            result_parts.append(f"WARNINGS: {'; '.join(warnings[:3])}")  # Limit warnings

        return " | ".join(result_parts) if result_parts else None
