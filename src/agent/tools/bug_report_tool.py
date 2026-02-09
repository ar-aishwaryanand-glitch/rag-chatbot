"""Bug Report tool for generating professional bug reports."""

from typing import TYPE_CHECKING, Optional
from .base_tool import BaseTool

if TYPE_CHECKING:
    from src.rag_chain import RAGChain


class BugReportTool(BaseTool):
    """
    Tool for generating detailed, professional bug reports from informal descriptions.

    Capabilities:
    - Convert informal bug descriptions into structured reports
    - Auto-suggest severity and priority
    - Generate clear reproduction steps
    - Format for Jira/GitHub/other bug trackers
    """

    def __init__(self, rag_chain: 'RAGChain'):
        """
        Initialize the Bug Report tool.

        Args:
            rag_chain: Instance of RAGChain for LLM access
        """
        super().__init__()
        self.rag_chain = rag_chain

    @property
    def name(self) -> str:
        return "bug_report"

    @property
    def description(self) -> str:
        return """Generate detailed, professional bug reports from informal descriptions. \
Use when user describes a bug, defect, or issue and needs help writing a proper bug report. \
Outputs structured format with title, severity, steps to reproduce, expected/actual results."""

    def _run(
        self,
        query: str = None,
        bug_description: str = None,
        environment: Optional[str] = None,
        format_type: str = "standard"
    ) -> str:
        """
        Generate a professional bug report from description.

        Args:
            query: Bug description (alias for bug_description, used by agent)
            bug_description: Informal description of the bug
            environment: Optional environment details (browser, OS, version)
            format_type: Output format - "standard", "jira", or "github"

        Returns:
            Formatted bug report
        """
        # Support both 'query' (from agent) and 'bug_description' (direct call)
        description = query or bug_description
        if not description or not description.strip():
            return "Error: Please provide a bug description"

        try:
            from langchain_core.prompts import ChatPromptTemplate

            format_instructions = self._get_format_instructions(format_type)

            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are an expert QA Engineer who writes clear, detailed bug reports.

Your task is to convert the user's bug description into a professional bug report.

{format_instructions}

GUIDELINES:
1. **Title**: Short, descriptive (max 80 chars), includes affected component
2. **Severity**:
   - Critical: System crash, data loss, security vulnerability
   - High: Major feature broken, no workaround
   - Medium: Feature partially broken, workaround exists
   - Low: Minor issue, cosmetic problem
3. **Priority**:
   - P0: Fix immediately (blocker)
   - P1: Fix in current sprint
   - P2: Fix in next sprint
   - P3: Fix when possible
4. **Steps**: Clear, numbered, anyone can follow
5. **Expected vs Actual**: Be specific about the difference
6. **Environment**: Include relevant details if provided

Be professional but concise. Focus on facts, not opinions."""),
                ("human", """Bug Description: {description}

Environment: {environment}

Generate a complete bug report.""")
            ])

            env_text = environment if environment else "Not specified - please add environment details"

            messages = prompt.format_messages(
                description=description,
                environment=env_text
            )
            response = self.rag_chain.llm.invoke(messages)

            return response.content

        except Exception as e:
            return f"Error generating bug report: {str(e)}"

    def _get_format_instructions(self, format_type: str) -> str:
        """Get format-specific instructions."""

        if format_type == "jira":
            return """OUTPUT FORMAT (Jira Style):
*Summary:* [Clear, concise title]

*Type:* Bug
*Priority:* [P0-Blocker/P1-Critical/P2-Major/P3-Minor/P4-Trivial]
*Severity:* [Critical/High/Medium/Low]
*Component:* [Affected component]
*Environment:* [Browser/OS/Version]

*Description:*
[Detailed description of the issue]

*Steps to Reproduce:*
# Step one
# Step two
# Step three

*Expected Result:*
[What should happen]

*Actual Result:*
[What actually happens]

*Attachments:*
[Note any screenshots/logs needed]

*Additional Notes:*
[Any workarounds or related issues]"""

        elif format_type == "github":
            return """OUTPUT FORMAT (GitHub Issue Style):
## Bug Report

### Description
[Clear description of the bug]

### Steps to Reproduce
1. Step one
2. Step two
3. Step three

### Expected Behavior
[What you expected to happen]

### Actual Behavior
[What actually happened]

### Environment
- OS: [e.g., Windows 11, macOS 14]
- Browser: [e.g., Chrome 120]
- Version: [e.g., v2.1.0]

### Screenshots
[If applicable, add screenshots]

### Additional Context
[Any other relevant information]

### Labels
`bug` `severity: [high/medium/low]` `priority: [P0/P1/P2/P3]`"""

        else:  # standard format
            return """OUTPUT FORMAT:
## Bug Report

**Title:** [Clear, descriptive title - max 80 characters]

**Bug ID:** BUG-[AUTO] _(to be assigned)_
**Reported By:** [User]
**Date:** [Current Date]

---

**Severity:** Critical / High / Medium / Low
**Priority:** P0 / P1 / P2 / P3
**Status:** New

---

### Environment
- **Platform:** [Web/Mobile/Desktop]
- **Browser/App:** [Name and version]
- **OS:** [Operating system]
- **Version:** [Application version]

---

### Description
[Detailed description of the bug]

---

### Steps to Reproduce
1. [First step]
2. [Second step]
3. [Third step]
4. [Continue as needed...]

---

### Expected Result
[What should happen when following the steps above]

### Actual Result
[What actually happens - be specific]

---

### Attachments
- [ ] Screenshot attached
- [ ] Video recording attached
- [ ] Error logs attached

---

### Workaround
[If any workaround exists, describe it here. Otherwise: "None known"]

---

### Additional Notes
[Any other relevant information, related bugs, or context]"""
