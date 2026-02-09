"""Requirements Extractor Tool - Extract structured requirements from documents."""

from typing import Optional, List, Dict
from .base_tool import BaseTool


class RequirementsExtractorTool(BaseTool):
    """
    Tool for extracting structured requirements from indexed documents.

    Parses Confluence docs, requirement specs, user stories, and other
    documentation to identify and structure requirements.
    """

    def __init__(self, rag_chain):
        """
        Initialize the requirements extractor.

        Args:
            rag_chain: RAGChain instance for document retrieval and LLM access
        """
        super().__init__()
        self.rag_chain = rag_chain

    @property
    def name(self) -> str:
        return "requirements_extractor"

    @property
    def description(self) -> str:
        return """Extract and structure requirements from indexed documents. \
Use when user wants to: identify requirements from documentation, create a requirements list, \
parse user stories into testable requirements, or prepare requirements for test case generation. \
Outputs structured requirements with IDs, descriptions, and acceptance criteria."""

    def _run(
        self,
        query: str = None,
        topic: str = None,
        document_filter: Optional[str] = None,
        output_format: str = "structured"
    ) -> str:
        """
        Extract requirements from indexed documents.

        Args:
            query: Topic or feature to extract requirements for
            topic: Alias for query (used by agent)
            document_filter: Optional filter for specific documents
            output_format: "structured", "user_stories", or "acceptance_criteria"

        Returns:
            Structured requirements extracted from documents
        """
        search_topic = query or topic
        if not search_topic or not search_topic.strip():
            return "Error: Please provide a topic or feature to extract requirements for"

        try:
            # Retrieve relevant documents
            docs = self.rag_chain.retrieve_context(search_topic, k=10)

            if not docs:
                return f"No documents found related to '{search_topic}'. Please import documents first using Confluence import or file upload."

            # Format document content
            doc_content = self._format_documents(docs, document_filter)

            if not doc_content.strip():
                return f"No relevant content found for '{search_topic}' in indexed documents."

            # Extract requirements using LLM
            from langchain_core.prompts import ChatPromptTemplate

            format_instructions = self._get_format_instructions(output_format)

            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are a Requirements Analyst expert. Your task is to extract clear, testable requirements from documentation.

**Guidelines:**
1. **Identify Requirements**: Look for:
   - Functional requirements (what the system should do)
   - Non-functional requirements (performance, security, usability)
   - Business rules and constraints
   - User stories and acceptance criteria

2. **Structure Each Requirement**:
   - Give each a unique ID (REQ-001, REQ-002, etc.)
   - Write a clear, concise title
   - Provide detailed description
   - Extract or infer acceptance criteria
   - Note any dependencies or constraints

3. **Make Requirements Testable**:
   - Use specific, measurable language
   - Avoid vague terms like "fast", "user-friendly", "easy"
   - Include specific values where mentioned (e.g., "response time < 2 seconds")

4. **Prioritize**: If priority is mentioned or can be inferred, include it (High/Medium/Low)

{format_instructions}

Be thorough but avoid duplicating requirements. Group related requirements together."""),
                ("human", """Extract requirements from the following documentation about: {topic}

**SOURCE DOCUMENTATION:**
{content}

**Instructions:**
1. Identify ALL requirements (functional and non-functional)
2. Structure them clearly with IDs
3. Include acceptance criteria for each
4. Note any assumptions or dependencies

Extract the requirements now:""")
            ])

            messages = prompt.format_messages(
                topic=search_topic,
                content=doc_content[:8000]  # Limit content size
            )

            response = self.rag_chain.llm.invoke(messages)

            # Add summary header
            result = f"## Requirements Extracted for: {search_topic}\n\n"
            result += f"*Source: {len(docs)} document chunks analyzed*\n\n"
            result += "---\n\n"
            result += response.content

            return result

        except Exception as e:
            return f"Error extracting requirements: {str(e)}"

    def _format_documents(self, docs: List, document_filter: Optional[str] = None) -> str:
        """Format retrieved documents for analysis."""
        formatted_parts = []

        for i, doc in enumerate(docs, 1):
            # Apply filter if specified
            if document_filter:
                source = doc.metadata.get('source', '')
                title = doc.metadata.get('title', '')
                if document_filter.lower() not in source.lower() and document_filter.lower() not in title.lower():
                    continue

            source = doc.metadata.get('source', 'Unknown')
            title = doc.metadata.get('title', 'Untitled')
            content = doc.page_content.strip()

            if content:
                formatted_parts.append(f"### Document {i}: {title}\n*Source: {source}*\n\n{content}\n")

        return "\n---\n".join(formatted_parts)

    def _get_format_instructions(self, output_format: str) -> str:
        """Get format-specific instructions."""
        formats = {
            "structured": """**Output Format:**
For each requirement:

### REQ-XXX: [Title]
**Priority:** [High/Medium/Low]
**Type:** [Functional/Non-Functional/Business Rule]
**Description:** [Detailed description]
**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
**Dependencies:** [Any dependencies or related requirements]
**Notes:** [Additional context or assumptions]""",

            "user_stories": """**Output Format:**
For each requirement, use User Story format:

### US-XXX: [Title]
**As a** [user role]
**I want** [feature/capability]
**So that** [benefit/value]

**Acceptance Criteria:**
- Given [context], When [action], Then [expected result]
- Given [context], When [action], Then [expected result]

**Priority:** [High/Medium/Low]
**Story Points:** [Estimate if possible]""",

            "acceptance_criteria": """**Output Format:**
For each requirement, focus on testable acceptance criteria:

### AC-XXX: [Feature/Requirement Title]
**Acceptance Criteria:**

1. **Scenario:** [Name]
   - **Given:** [Initial context/state]
   - **When:** [Action taken]
   - **Then:** [Expected outcome]
   - **And:** [Additional outcomes if any]

2. **Scenario:** [Name]
   - **Given:** [Initial context/state]
   - **When:** [Action taken]
   - **Then:** [Expected outcome]

**Edge Cases to Test:**
- [Edge case 1]
- [Edge case 2]

**Out of Scope:**
- [What is NOT included]"""
        }

        return formats.get(output_format, formats["structured"])
