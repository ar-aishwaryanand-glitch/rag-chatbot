"""Specialized Agents - Dev Agent, Doc Agent, and more.

This module provides specialized agent interfaces that can be registered
with the Manager Agent for multi-agent orchestration.

Available Agents:
    - DevAgentInterface: Code generation and analysis
    - DocAgentInterface: Documentation generation
    - SecurityAgentInterface: Security analysis and testingães
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
import logging
import re

from src.agent.types import AgentCapability

if TYPE_CHECKING:
    from src.rag_chain import RAGChain

logger = logging.getLogger(__name__)


class DevAgentInterface:
    """
    Developer Agent - Handles code generation and analysis tasks.

    Capabilities:
    - Generate code from requirements
    - Analyze existing code
    - Suggest refactoring
    - Create code documentation
    - Generate unit test stubs
    """

    def __init__(self, rag_chain: 'RAGChain'):
        """
        Initialize Dev Agent.

        Args:
            rag_chain: RAGChain for context retrieval and LLM access
        """
        self.rag_chain = rag_chain
        self.llm = rag_chain.llm

    @property
    def capabilities(self) -> AgentCapability:
        """Return agent capabilities."""
        return AgentCapability(
            name="Developer Agent",
            description="Specialized in code generation, analysis, and refactoring",
            tools=["code_generator", "code_analyzer", "refactoring_advisor"],
            keywords=[
                "code", "implement", "function", "class", "refactor",
                "generate code", "write code", "create function",
                "analyze code", "code review", "implementation"
            ]
        )

    def execute(self, instruction: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a development instruction.

        Args:
            instruction: What to do
            context: Additional context

        Returns:
            Dict with success, output, tool_used, metadata
        """
        context = context or {}
        instruction_lower = instruction.lower()

        try:
            # Determine task type
            if any(kw in instruction_lower for kw in ["generate", "create", "write", "implement"]):
                return self._generate_code(instruction, context)
            elif any(kw in instruction_lower for kw in ["analyze", "review", "check"]):
                return self._analyze_code(instruction, context)
            elif any(kw in instruction_lower for kw in ["refactor", "improve", "optimize"]):
                return self._suggest_refactoring(instruction, context)
            else:
                return self._generate_code(instruction, context)

        except Exception as e:
            logger.error(f"Dev agent error: {e}")
            return {
                "success": False,
                "output": f"Error: {str(e)}",
                "tool_used": "dev_agent",
                "metadata": {"error": str(e)}
            }

    def _generate_code(self, instruction: str, context: Dict) -> Dict[str, Any]:
        """Generate code based on instruction."""
        from langchain_core.prompts import ChatPromptTemplate

        # Get relevant context from RAG
        rag_context = ""
        try:
            docs = self.rag_chain.retrieve_context(instruction, k=5)
            if docs:
                rag_context = self.rag_chain.format_context(docs)
        except Exception:
            pass

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert software developer. Generate clean, well-documented code.

Guidelines:
- Use clear variable and function names
- Include docstrings and comments
- Follow best practices for the language
- Handle errors appropriately
- Make code testable

If language is not specified, use Python."""),
            ("human", """Task: {instruction}

Context from documentation:
{context}

Previous results:
{previous}

Generate the code:""")
        ])

        previous = context.get("previous_results", {})
        previous_text = "\n".join([
            f"{k}: {str(v)[:200]}"
            for k, v in previous.items()
        ]) if previous else "None"

        messages = prompt.format_messages(
            instruction=instruction,
            context=rag_context[:3000] if rag_context else "No additional context",
            previous=previous_text[:1000]
        )

        response = self.llm.invoke(messages)

        return {
            "success": True,
            "output": response.content,
            "tool_used": "code_generator",
            "metadata": {"type": "code_generation"}
        }

    def _analyze_code(self, instruction: str, context: Dict) -> Dict[str, Any]:
        """Analyze code for issues and improvements."""
        from langchain_core.prompts import ChatPromptTemplate

        # Extract code from context or instruction
        code = context.get("code", "")
        if not code:
            # Try to extract code blocks from instruction
            code_match = re.search(r'```[\w]*\n?(.*?)```', instruction, re.DOTALL)
            if code_match:
                code = code_match.group(1)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior code reviewer. Analyze code for:

1. **Code Quality**
   - Readability and clarity
   - Naming conventions
   - Code structure

2. **Potential Issues**
   - Bugs and logic errors
   - Security vulnerabilities
   - Performance concerns

3. **Best Practices**
   - Design patterns
   - Error handling
   - Testing considerations

Provide specific, actionable feedback."""),
            ("human", """Analyze this code:

{code}

Additional context: {instruction}

Provide your analysis:""")
        ])

        messages = prompt.format_messages(
            code=code if code else instruction,
            instruction=instruction
        )

        response = self.llm.invoke(messages)

        return {
            "success": True,
            "output": response.content,
            "tool_used": "code_analyzer",
            "metadata": {"type": "code_analysis"}
        }

    def _suggest_refactoring(self, instruction: str, context: Dict) -> Dict[str, Any]:
        """Suggest code refactoring improvements."""
        from langchain_core.prompts import ChatPromptTemplate

        code = context.get("code", instruction)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a refactoring expert. Suggest improvements for:

1. **Structure** - Better organization, smaller functions
2. **Clarity** - More readable code, better names
3. **Performance** - Optimization opportunities
4. **Maintainability** - Easier to modify and extend
5. **Testing** - More testable code

Provide before/after examples where helpful."""),
            ("human", """Suggest refactoring for:

{code}

Focus: {instruction}""")
        ])

        messages = prompt.format_messages(
            code=code,
            instruction=instruction
        )

        response = self.llm.invoke(messages)

        return {
            "success": True,
            "output": response.content,
            "tool_used": "refactoring_advisor",
            "metadata": {"type": "refactoring"}
        }


class DocAgentInterface:
    """
    Documentation Agent - Handles documentation generation tasks.

    Capabilities:
    - Generate API documentation
    - Create user guides
    - Write README files
    - Generate code comments
    - Create architecture docs
    """

    def __init__(self, rag_chain: 'RAGChain'):
        """
        Initialize Doc Agent.

        Args:
            rag_chain: RAGChain for context retrieval and LLM access
        """
        self.rag_chain = rag_chain
        self.llm = rag_chain.llm

    @property
    def capabilities(self) -> AgentCapability:
        """Return agent capabilities."""
        return AgentCapability(
            name="Documentation Agent",
            description="Specialized in creating technical documentation, guides, and API docs",
            tools=["api_doc_generator", "readme_generator", "guide_writer"],
            keywords=[
                "document", "documentation", "readme", "guide",
                "api doc", "user guide", "tutorial", "explain",
                "describe", "write docs", "create documentation"
            ]
        )

    def execute(self, instruction: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a documentation instruction.

        Args:
            instruction: What to document
            context: Additional context

        Returns:
            Dict with success, output, tool_used, metadata
        """
        context = context or {}
        instruction_lower = instruction.lower()

        try:
            if any(kw in instruction_lower for kw in ["api", "endpoint", "swagger"]):
                return self._generate_api_docs(instruction, context)
            elif any(kw in instruction_lower for kw in ["readme", "project"]):
                return self._generate_readme(instruction, context)
            elif any(kw in instruction_lower for kw in ["guide", "tutorial", "how to"]):
                return self._generate_guide(instruction, context)
            elif any(kw in instruction_lower for kw in ["architecture", "design", "overview"]):
                return self._generate_architecture_doc(instruction, context)
            else:
                return self._generate_general_docs(instruction, context)

        except Exception as e:
            logger.error(f"Doc agent error: {e}")
            return {
                "success": False,
                "output": f"Error: {str(e)}",
                "tool_used": "doc_agent",
                "metadata": {"error": str(e)}
            }

    def _generate_api_docs(self, instruction: str, context: Dict) -> Dict[str, Any]:
        """Generate API documentation."""
        from langchain_core.prompts import ChatPromptTemplate

        # Get context
        rag_context = ""
        try:
            docs = self.rag_chain.retrieve_context(instruction, k=8)
            if docs:
                rag_context = self.rag_chain.format_context(docs)
        except Exception:
            pass

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a technical writer specializing in API documentation.

Generate comprehensive API documentation including:
- Endpoint description
- HTTP method and URL
- Request parameters (path, query, body)
- Request/response examples
- Error codes and handling
- Authentication requirements

Use clear formatting with markdown."""),
            ("human", """Create API documentation for:

{instruction}

Context:
{context}

Generate the documentation:""")
        ])

        messages = prompt.format_messages(
            instruction=instruction,
            context=rag_context[:4000] if rag_context else "No additional context"
        )

        response = self.llm.invoke(messages)

        return {
            "success": True,
            "output": response.content,
            "tool_used": "api_doc_generator",
            "metadata": {"type": "api_documentation"}
        }

    def _generate_readme(self, instruction: str, context: Dict) -> Dict[str, Any]:
        """Generate README file."""
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a technical writer. Create a professional README.md file.

Include these sections:
# Project Name
Brief description

## Features
- Feature 1
- Feature 2

## Installation
Step-by-step instructions

## Usage
Code examples and explanations

## Configuration
Environment variables, settings

## Contributing
How to contribute

## License
License information"""),
            ("human", """Create a README for:

{instruction}

Project context:
{context}""")
        ])

        project_context = context.get("project_info", "")

        messages = prompt.format_messages(
            instruction=instruction,
            context=project_context if project_context else "General project"
        )

        response = self.llm.invoke(messages)

        return {
            "success": True,
            "output": response.content,
            "tool_used": "readme_generator",
            "metadata": {"type": "readme"}
        }

    def _generate_guide(self, instruction: str, context: Dict) -> Dict[str, Any]:
        """Generate user guide or tutorial."""
        from langchain_core.prompts import ChatPromptTemplate

        rag_context = ""
        try:
            docs = self.rag_chain.retrieve_context(instruction, k=8)
            if docs:
                rag_context = self.rag_chain.format_context(docs)
        except Exception:
            pass

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a technical writer creating user-friendly guides.

Create a step-by-step guide including:
1. **Introduction** - What this guide covers
2. **Prerequisites** - What users need before starting
3. **Step-by-Step Instructions** - Numbered, clear steps
4. **Screenshots/Examples** - Code or visual examples
5. **Troubleshooting** - Common issues and solutions
6. **Next Steps** - What to do after completing the guide

Use clear, simple language. Assume the reader is a beginner."""),
            ("human", """Create a guide for:

{instruction}

Reference material:
{context}""")
        ])

        messages = prompt.format_messages(
            instruction=instruction,
            context=rag_context[:4000] if rag_context else "No additional context"
        )

        response = self.llm.invoke(messages)

        return {
            "success": True,
            "output": response.content,
            "tool_used": "guide_writer",
            "metadata": {"type": "user_guide"}
        }

    def _generate_architecture_doc(self, instruction: str, context: Dict) -> Dict[str, Any]:
        """Generate architecture documentation."""
        from langchain_core.prompts import ChatPromptTemplate

        rag_context = ""
        try:
            docs = self.rag_chain.retrieve_context(instruction, k=10)
            if docs:
                rag_context = self.rag_chain.format_context(docs)
        except Exception:
            pass

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a software architect documenting system design.

Create architecture documentation including:

## System Overview
High-level description

## Architecture Diagram
Text-based diagram (ASCII or Mermaid)

## Components
- Component descriptions
- Responsibilities
- Interfaces

## Data Flow
How data moves through the system

## Technology Stack
- Languages, frameworks, tools
- Rationale for choices

## Scalability & Performance
Design considerations

## Security
Security measures and considerations"""),
            ("human", """Document the architecture for:

{instruction}

System context:
{context}""")
        ])

        messages = prompt.format_messages(
            instruction=instruction,
            context=rag_context[:5000] if rag_context else "No additional context"
        )

        response = self.llm.invoke(messages)

        return {
            "success": True,
            "output": response.content,
            "tool_used": "architecture_doc_generator",
            "metadata": {"type": "architecture"}
        }

    def _generate_general_docs(self, instruction: str, context: Dict) -> Dict[str, Any]:
        """Generate general documentation."""
        from langchain_core.prompts import ChatPromptTemplate

        rag_context = ""
        try:
            docs = self.rag_chain.retrieve_context(instruction, k=5)
            if docs:
                rag_context = self.rag_chain.format_context(docs)
        except Exception:
            pass

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a technical writer. Create clear, comprehensive documentation.

Follow these principles:
- Use clear, simple language
- Include examples
- Organize with headings
- Be thorough but concise"""),
            ("human", """Create documentation for:

{instruction}

Context:
{context}""")
        ])

        messages = prompt.format_messages(
            instruction=instruction,
            context=rag_context[:3000] if rag_context else "No additional context"
        )

        response = self.llm.invoke(messages)

        return {
            "success": True,
            "output": response.content,
            "tool_used": "doc_generator",
            "metadata": {"type": "general_documentation"}
        }


class SecurityAgentInterface:
    """
    Security Agent - Handles security analysis and testing tasks.

    Capabilities:
    - Security code review
    - Vulnerability analysis
    - Security test generation
    - Compliance checking
    """

    def __init__(self, rag_chain: 'RAGChain'):
        """
        Initialize Security Agent.

        Args:
            rag_chain: RAGChain for context retrieval and LLM access
        """
        self.rag_chain = rag_chain
        self.llm = rag_chain.llm

    @property
    def capabilities(self) -> AgentCapability:
        """Return agent capabilities."""
        return AgentCapability(
            name="Security Agent",
            description="Specialized in security analysis, vulnerability detection, and security testing",
            tools=["security_analyzer", "vulnerability_scanner", "security_test_generator"],
            keywords=[
                "security", "vulnerability", "secure", "owasp",
                "penetration", "injection", "xss", "csrf",
                "authentication", "authorization", "encryption"
            ]
        )

    def execute(self, instruction: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a security instruction.

        Args:
            instruction: Security task to perform
            context: Additional context

        Returns:
            Dict with success, output, tool_used, metadata
        """
        context = context or {}
        instruction_lower = instruction.lower()

        try:
            if any(kw in instruction_lower for kw in ["analyze", "review", "audit"]):
                return self._security_review(instruction, context)
            elif any(kw in instruction_lower for kw in ["test", "pentest", "vulnerability"]):
                return self._generate_security_tests(instruction, context)
            elif any(kw in instruction_lower for kw in ["compliance", "owasp", "standard"]):
                return self._compliance_check(instruction, context)
            else:
                return self._security_review(instruction, context)

        except Exception as e:
            logger.error(f"Security agent error: {e}")
            return {
                "success": False,
                "output": f"Error: {str(e)}",
                "tool_used": "security_agent",
                "metadata": {"error": str(e)}
            }

    def _security_review(self, instruction: str, context: Dict) -> Dict[str, Any]:
        """Perform security code review."""
        from langchain_core.prompts import ChatPromptTemplate

        code = context.get("code", instruction)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a security expert performing a code review.

Check for these vulnerabilities (OWASP Top 10):
1. **Injection** - SQL, NoSQL, OS command injection
2. **Broken Authentication** - Weak passwords, session issues
3. **Sensitive Data Exposure** - Unencrypted data, logging secrets
4. **XXE** - XML external entity attacks
5. **Broken Access Control** - Missing authorization checks
6. **Security Misconfiguration** - Default configs, verbose errors
7. **XSS** - Cross-site scripting vulnerabilities
8. **Insecure Deserialization** - Untrusted data deserialization
9. **Components with Known Vulnerabilities** - Outdated dependencies
10. **Insufficient Logging** - Missing audit trails

For each issue found:
- Severity (Critical/High/Medium/Low)
- Location in code
- Description of the vulnerability
- Remediation steps
- Example fix"""),
            ("human", """Perform security review on:

{code}

Focus: {instruction}""")
        ])

        messages = prompt.format_messages(
            code=code,
            instruction=instruction
        )

        response = self.llm.invoke(messages)

        return {
            "success": True,
            "output": response.content,
            "tool_used": "security_analyzer",
            "metadata": {"type": "security_review"}
        }

    def _generate_security_tests(self, instruction: str, context: Dict) -> Dict[str, Any]:
        """Generate security test cases."""
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a security testing expert. Generate security test cases.

Include tests for:
1. **Authentication Tests**
   - Brute force protection
   - Session management
   - Password policies

2. **Authorization Tests**
   - Role-based access
   - Privilege escalation
   - IDOR vulnerabilities

3. **Input Validation Tests**
   - SQL injection
   - XSS attacks
   - Command injection

4. **Data Protection Tests**
   - Encryption verification
   - Sensitive data handling
   - Data leakage

Format each test case with:
- Test ID
- Vulnerability type
- Test steps
- Expected result
- Payload examples"""),
            ("human", """Generate security tests for:

{instruction}

Context:
{context}""")
        ])

        messages = prompt.format_messages(
            instruction=instruction,
            context=str(context.get("previous_results", ""))[:2000]
        )

        response = self.llm.invoke(messages)

        return {
            "success": True,
            "output": response.content,
            "tool_used": "security_test_generator",
            "metadata": {"type": "security_tests"}
        }

    def _compliance_check(self, instruction: str, context: Dict) -> Dict[str, Any]:
        """Check compliance against security standards."""
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a security compliance expert.

Check compliance against:
- OWASP Top 10
- OWASP ASVS (Application Security Verification Standard)
- CWE (Common Weakness Enumeration)
- SANS Top 25

Provide:
1. Compliance checklist
2. Current status (Pass/Fail/Unknown)
3. Recommendations for each item
4. Priority for remediation"""),
            ("human", """Check compliance for:

{instruction}

Application context:
{context}""")
        ])

        messages = prompt.format_messages(
            instruction=instruction,
            context=str(context)[:2000]
        )

        response = self.llm.invoke(messages)

        return {
            "success": True,
            "output": response.content,
            "tool_used": "compliance_checker",
            "metadata": {"type": "compliance_check"}
        }
