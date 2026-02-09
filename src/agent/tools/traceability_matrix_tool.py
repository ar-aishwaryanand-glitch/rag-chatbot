"""Traceability Matrix Tool - Generate REQ to TC mapping with coverage analysis."""

from typing import TYPE_CHECKING, Optional
from .base_tool import BaseTool
import re

if TYPE_CHECKING:
    from src.rag_chain import RAGChain


class TraceabilityMatrixTool(BaseTool):
    """
    Tool for generating requirements-to-test-cases traceability matrix.

    Capabilities:
    - Map requirements (REQ-XXX) to test cases (TC-XXX)
    - Calculate coverage percentage
    - Highlight unmapped requirements
    - Generate tabular output (markdown, CSV, JSON)
    """

    def __init__(self, rag_chain: 'RAGChain'):
        super().__init__()
        self.rag_chain = rag_chain

    @property
    def name(self) -> str:
        return "traceability_matrix"

    @property
    def description(self) -> str:
        return """Generate a requirements-to-test-cases traceability matrix. \
Use when user wants to: see which requirements have test coverage, \
identify unmapped requirements, analyze test coverage percentage, \
or create a mapping between REQ-XXX and TC-XXX identifiers."""

    def _run(
        self,
        query: str = None,
        topic: str = None,
        output_format: str = "markdown"
    ) -> str:
        """
        Generate traceability matrix.

        Args:
            query: Topic/feature area (alias for topic)
            topic: Feature area to analyze
            output_format: "markdown", "csv", or "json"

        Returns:
            Traceability matrix with coverage analysis
        """
        search_topic = query or topic
        if not search_topic or not search_topic.strip():
            return "Error: Please provide a topic or feature area to analyze"

        try:
            # Retrieve documents related to the topic
            docs = self.rag_chain.retrieve_context(search_topic, k=15)

            if not docs:
                return f"No documents found for '{search_topic}'. Please import documents first."

            # Build context from documents
            context = self.rag_chain.format_context(docs)

            from langchain_core.prompts import ChatPromptTemplate

            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a QA Traceability Expert. Create a requirements-to-test-cases traceability matrix.

**TASK:**
1. Identify all requirements (REQ-XXX format or infer from content)
2. Identify all test cases (TC-XXX format or infer from content)
3. Map each requirement to covering test cases
4. Calculate coverage percentage

**OUTPUT FORMAT:**

## Traceability Matrix: [Topic]

### Summary
- **Total Requirements:** X
- **Total Test Cases:** Y
- **Mapped Requirements:** Z
- **Coverage:** XX%

### Matrix

| Requirement ID | Requirement Title | Test Cases | Status |
|----------------|-------------------|------------|--------|
| REQ-001 | [Title] | TC-001, TC-002 | Covered |
| REQ-002 | [Title] | TC-003 | Covered |
| REQ-003 | [Title] | - | Not Covered |

### Unmapped Requirements
List requirements without test coverage:
1. **REQ-XXX**: [Title] - Needs test cases

### Orphan Test Cases
List test cases not linked to requirements:
1. **TC-XXX**: [Title] - Consider linking

### Coverage Analysis
- **Full Coverage (2+ TCs):** X requirements
- **Partial Coverage (1 TC):** X requirements
- **No Coverage:** X requirements

### Recommendations
1. Priority gaps to address
2. Suggested test cases to add

Be thorough. If no explicit REQ/TC IDs exist, infer them from the content."""),
                ("human", """Topic: {topic}

Documentation:
{context}

Generate the traceability matrix:""")
            ])

            messages = prompt.format_messages(
                topic=search_topic,
                context=context[:12000]
            )

            response = self.rag_chain.llm.invoke(messages)
            matrix_output = response.content

            # Convert format if needed
            if output_format == "csv":
                matrix_output = self._convert_to_csv(response.content)
            elif output_format == "json":
                matrix_output = self._convert_to_json(response.content)

            return matrix_output

        except Exception as e:
            return f"Error generating traceability matrix: {str(e)}"

    def _convert_to_csv(self, markdown_content: str) -> str:
        """Convert markdown table to CSV format."""
        lines = ["Requirement ID,Requirement Title,Test Cases,Status"]

        # Parse markdown table rows
        table_pattern = r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|'
        matches = re.findall(table_pattern, markdown_content)

        for match in matches:
            col1 = match[0].strip()
            # Skip header and separator rows
            if col1.startswith('-') or col1 == 'Requirement ID':
                continue
            row = ','.join([f'"{cell.strip()}"' for cell in match])
            lines.append(row)

        return '\n'.join(lines)

    def _convert_to_json(self, markdown_content: str) -> str:
        """Convert to JSON format."""
        import json

        result = {
            "topic": "",
            "requirements": [],
            "coverage_percent": 0
        }

        # Extract coverage percentage
        coverage_match = re.search(r'Coverage:\s*(\d+)%', markdown_content)
        if coverage_match:
            result["coverage_percent"] = int(coverage_match.group(1))

        # Parse table rows
        table_pattern = r'\|\s*(REQ-\d+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|'
        matches = re.findall(table_pattern, markdown_content)

        for match in matches:
            test_cases = [tc.strip() for tc in match[2].split(',') if tc.strip() and tc.strip() != '-']
            result["requirements"].append({
                "id": match[0].strip(),
                "title": match[1].strip(),
                "test_cases": test_cases,
                "status": "covered" if test_cases else "not_covered"
            })

        return json.dumps(result, indent=2)
