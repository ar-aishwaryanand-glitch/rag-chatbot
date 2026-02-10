"""Test Data Generator Tool - Generate comprehensive test data with edge cases."""

from typing import TYPE_CHECKING, Optional
from .base_tool import BaseTool
from src.logging_config import get_logger
import re
import json

logger = get_logger(__name__)

if TYPE_CHECKING:
    from src.rag_chain import RAGChain


class TestDataGeneratorTool(BaseTool):
    """
    Tool for generating comprehensive test data.

    Capabilities:
    - Generate valid, invalid, and boundary test data
    - Support JSON and CSV output formats
    - Include edge cases and special characters
    - Create data for specific field types
    """

    def __init__(self, rag_chain: 'RAGChain'):
        super().__init__()
        self.rag_chain = rag_chain

    @property
    def name(self) -> str:
        return "test_data_generator"

    @property
    def description(self) -> str:
        return """Generate comprehensive test data including valid, invalid, and boundary values. \
Use when user needs: test data for form fields, API payloads, database testing, \
edge case data, or boundary value analysis. Outputs JSON or CSV format."""

    def _run(
        self,
        query: str = None,
        field_definitions: str = None,
        output_format: str = "json",
        num_records: int = 5
    ) -> str:
        """
        Generate test data based on field definitions.

        Args:
            query: Field definitions (alias for field_definitions)
            field_definitions: Description of fields/data needed
            output_format: "json" or "csv"
            num_records: Number of records per category

        Returns:
            Generated test data in specified format
        """
        definitions = query or field_definitions
        if not definitions or not definitions.strip():
            return "Error: Please provide field definitions or data requirements"

        try:
            # Try to get relevant context from RAG
            context = ""
            try:
                docs = self.rag_chain.retrieve_context(definitions, k=5)
                if docs:
                    context = self.rag_chain.format_context(docs)
            except Exception as e:
                logger.debug(f"RAG context retrieval failed, continuing without context: {e}")

            from langchain_core.prompts import ChatPromptTemplate

            format_instructions = self._get_format_instructions(output_format)

            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are a Test Data Expert. Generate comprehensive test datasets.

**DATA CATEGORIES:**
1. **valid** - Normal values that pass validation
2. **invalid** - Values that trigger validation errors
3. **boundary** - Min/max values, limits
4. **edge_cases** - Special chars, unicode, injection attempts

**EDGE CASES TO INCLUDE:**
- Empty/whitespace: "", " ", null
- Special chars: !@#$%^&*()
- Unicode: emojis, Chinese, Arabic
- Long strings: 1000+ characters
- SQL injection: ' OR '1'='1
- XSS: <script>alert('xss')</script>
- Numeric: 0, -1, MAX_INT, decimals
- Dates: past, future, leap years

**FIELD TYPE GUIDELINES:**
- String: empty, max length, special chars, unicode
- Number: 0, negative, max int, decimals
- Email: valid formats, missing @, unicode
- Phone: formats, country codes, letters
- Date: past, future, invalid formats
- Boolean: true, false, null, "true"

{format_instructions}

Generate {num_records} records per category. Include description explaining each test case."""),
                ("human", """Field Definitions:
{definitions}

Output Format: {output_format}
Records per Category: {num_records}

{context_section}

Generate comprehensive test data:""")
            ])

            context_section = f"Context:\n{context[:4000]}" if context else ""

            messages = prompt.format_messages(
                definitions=definitions,
                output_format=output_format,
                num_records=num_records,
                context_section=context_section
            )

            response = self.rag_chain.llm.invoke(messages)

            # Clean and format output
            output = self._clean_output(response.content, output_format)

            return output

        except Exception as e:
            return f"Error generating test data: {str(e)}"

    def _get_format_instructions(self, output_format: str) -> str:
        """Get format-specific instructions."""
        if output_format.lower() == "csv":
            return """**OUTPUT FORMAT (CSV):**
Headers: category,description,field1,field2,...

Example:
category,description,username,email,age
valid,Standard user,john_doe,john@example.com,25
invalid,Missing @ in email,jane,janeexample.com,30
boundary,Min age,min_user,min@test.com,0
edge_case,SQL injection,'; DROP TABLE;--,test@test.com,25"""
        else:
            # Note: Double curly braces escape them in Python format strings
            return """**OUTPUT FORMAT (JSON):**
{{
  "valid": [
    {{"description": "Standard user", "data": {{"username": "john_doe", "email": "john@example.com"}}}}
  ],
  "invalid": [
    {{"description": "Missing @", "data": {{"email": "invalid"}}, "expected_error": "Invalid email"}}
  ],
  "boundary": [
    {{"description": "Max length", "data": {{"username": "aaaa..."}}, "test_type": "max_length"}}
  ],
  "edge_cases": [
    {{"description": "SQL injection", "data": {{"username": "'; DROP TABLE;--"}}, "security_test": true}}
  ]
}}"""

    def _clean_output(self, content: str, output_format: str) -> str:
        """Clean and format the output."""
        # Remove markdown code blocks (handles ```json, ```csv, ``` with newline, etc.)
        content = content.strip()
        # Remove opening code fence (``` optionally followed by language identifier and newline)
        content = re.sub(r'^```\w*\n?', '', content)
        # Remove closing code fence
        content = re.sub(r'\n?```$', '', content)
        content = content.strip()

        if output_format.lower() == "json":
            try:
                # First try to parse the whole content as JSON
                parsed = json.loads(content)
                return json.dumps(parsed, indent=2)
            except json.JSONDecodeError:
                # Try to find JSON object in content
                try:
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        parsed = json.loads(json_match.group())
                        return json.dumps(parsed, indent=2)
                except json.JSONDecodeError:
                    pass

        # Return content as-is if parsing fails
        return content.strip()
