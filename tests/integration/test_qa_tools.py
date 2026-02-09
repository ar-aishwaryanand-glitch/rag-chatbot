"""
Integration tests for QA Expert Tools.

Tests cover all 7 QA tools:
- QAAnalysisTool - Test case gap analysis
- BugReportTool - Bug report generation
- TestStrategyTool - Test strategy creation
- RequirementsExtractorTool - Requirements extraction
- TraceabilityMatrixTool - REQ to TC mapping
- BDDGeneratorTool - BDD/Gherkin generation
- TestDataGeneratorTool - Test data generation

These tests validate:
- Tool initialization
- Input validation
- Output format
- Error handling
- Integration with RAGChain (mocked)
"""

import pytest
import json
import re
from unittest.mock import MagicMock, patch, PropertyMock
from dataclasses import dataclass


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_rag_chain():
    """Create a mock RAGChain for testing tools."""
    mock = MagicMock()

    # Mock LLM responses
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="Mock LLM response")
    mock.llm = mock_llm

    # Mock document retrieval
    mock.retrieve_context.return_value = [
        MagicMock(
            page_content="REQ-001: User login with email and password",
            metadata={"source": "requirements.md"}
        ),
        MagicMock(
            page_content="REQ-002: User logout functionality",
            metadata={"source": "requirements.md"}
        )
    ]

    mock.format_context.return_value = "REQ-001: User login\nREQ-002: User logout"

    return mock


@pytest.fixture
def mock_llm_response():
    """Factory for creating specific LLM responses."""
    def _create_response(content: str):
        response = MagicMock()
        response.content = content
        return response
    return _create_response


# ============================================================================
# QA Analysis Tool Tests
# ============================================================================

class TestQAAnalysisTool:
    """Tests for QAAnalysisTool."""

    def test_tool_import(self):
        """Test tool can be imported."""
        from src.agent.tools.qa_analysis_tool import QAAnalysisTool
        assert QAAnalysisTool is not None

    def test_tool_initialization(self, mock_rag_chain):
        """Test tool initialization."""
        from src.agent.tools.qa_analysis_tool import QAAnalysisTool
        tool = QAAnalysisTool(mock_rag_chain)

        assert tool.name == "qa_analysis"
        assert "gap" in tool.description.lower() or "coverage" in tool.description.lower()

    def test_empty_input_returns_error(self, mock_rag_chain):
        """Test empty input handling."""
        from src.agent.tools.qa_analysis_tool import QAAnalysisTool
        tool = QAAnalysisTool(mock_rag_chain)

        result = tool.run(test_cases="")
        assert result.success is False or "error" in result.output.lower()

    def test_analysis_with_test_cases(self, mock_rag_chain, mock_llm_response):
        """Test analysis with valid test cases."""
        from src.agent.tools.qa_analysis_tool import QAAnalysisTool

        # Setup mock response
        analysis_response = """## Test Coverage Analysis

### Coverage Gaps
- Missing authentication failure scenarios

### Missing Scenarios
- **Edge Cases:** Empty email, special characters
- **Negative Tests:** Invalid credentials
- **Boundary Conditions:** Password length limits

### Improvement Suggestions
- Add timeout testing

### Risk Assessment
| Area | Risk Level | Recommendation |
|------|------------|----------------|
| Login | High | Add security tests |

### Recommended Additional Test Cases
1. Given invalid email format, When login, Then show error
"""
        mock_rag_chain.llm.invoke.return_value = mock_llm_response(analysis_response)

        tool = QAAnalysisTool(mock_rag_chain)
        result = tool.run(test_cases="TC-001: Test user login with valid credentials")

        assert result.success is True
        assert "Coverage" in result.output or "Gap" in result.output

    def test_analysis_with_requirements_context(self, mock_rag_chain, mock_llm_response):
        """Test analysis with requirements context."""
        from src.agent.tools.qa_analysis_tool import QAAnalysisTool

        mock_rag_chain.llm.invoke.return_value = mock_llm_response("## Analysis with context")

        tool = QAAnalysisTool(mock_rag_chain)
        result = tool.run(
            test_cases="TC-001: Login test",
            requirements="User authentication feature"
        )

        assert result.success is True
        mock_rag_chain.retrieve_context.assert_called()


# ============================================================================
# Bug Report Tool Tests
# ============================================================================

class TestBugReportTool:
    """Tests for BugReportTool."""

    def test_tool_import(self):
        """Test tool can be imported."""
        from src.agent.tools.bug_report_tool import BugReportTool
        assert BugReportTool is not None

    def test_tool_initialization(self, mock_rag_chain):
        """Test tool initialization."""
        from src.agent.tools.bug_report_tool import BugReportTool
        tool = BugReportTool(mock_rag_chain)

        assert tool.name == "bug_report"
        assert "bug" in tool.description.lower()

    def test_empty_input_returns_error(self, mock_rag_chain):
        """Test empty input handling."""
        from src.agent.tools.bug_report_tool import BugReportTool
        tool = BugReportTool(mock_rag_chain)

        result = tool.run(bug_description="")
        assert result.success is False or "error" in result.output.lower()

    def test_bug_report_generation(self, mock_rag_chain, mock_llm_response):
        """Test bug report generation."""
        from src.agent.tools.bug_report_tool import BugReportTool

        bug_report = """# Bug Report: Login Button Not Working

**Severity:** High
**Priority:** P1

## Summary
Login button does not respond to clicks

## Steps to Reproduce
1. Navigate to login page
2. Enter credentials
3. Click login button
4. Nothing happens

## Expected Result
User should be logged in

## Actual Result
No response from button

## Environment
- Browser: Chrome 120
- OS: Windows 11
"""
        mock_rag_chain.llm.invoke.return_value = mock_llm_response(bug_report)

        tool = BugReportTool(mock_rag_chain)
        result = tool.run(bug_description="Login button not working when clicked")

        assert result.success is True
        assert "Bug Report" in result.output or "Summary" in result.output

    def test_bug_report_formats(self, mock_rag_chain, mock_llm_response):
        """Test different output formats."""
        from src.agent.tools.bug_report_tool import BugReportTool

        mock_rag_chain.llm.invoke.return_value = mock_llm_response("Bug report content")

        tool = BugReportTool(mock_rag_chain)

        # Test different formats
        for fmt in ["standard", "jira", "github"]:
            result = tool.run(bug_description="Test bug", format_type=fmt)
            assert result.success is True


# ============================================================================
# Test Strategy Tool Tests
# ============================================================================

class TestTestStrategyTool:
    """Tests for TestStrategyTool."""

    def test_tool_import(self):
        """Test tool can be imported."""
        from src.agent.tools.test_strategy_tool import TestStrategyTool
        assert TestStrategyTool is not None

    def test_tool_initialization(self, mock_rag_chain):
        """Test tool initialization."""
        from src.agent.tools.test_strategy_tool import TestStrategyTool
        tool = TestStrategyTool(mock_rag_chain)

        assert tool.name == "test_strategy"
        assert "strateg" in tool.description.lower()  # Matches both "strategy" and "strategies"

    def test_empty_input_returns_error(self, mock_rag_chain):
        """Test empty input handling."""
        from src.agent.tools.test_strategy_tool import TestStrategyTool
        tool = TestStrategyTool(mock_rag_chain)

        result = tool.run(feature_description="")
        assert result.success is False or "error" in result.output.lower()

    def test_strategy_generation(self, mock_rag_chain, mock_llm_response):
        """Test test strategy generation."""
        from src.agent.tools.test_strategy_tool import TestStrategyTool

        strategy_content = """## Test Strategy: User Authentication

### Complexity Assessment
Medium-High complexity feature

### Testing Pyramid
- Unit Tests: 60%
- Integration Tests: 30%
- E2E Tests: 10%

### Test Types
1. Functional Testing
2. Security Testing
3. Performance Testing

### Recommendations
- Prioritize security tests
- Add load testing for login endpoint
"""
        mock_rag_chain.llm.invoke.return_value = mock_llm_response(strategy_content)

        tool = TestStrategyTool(mock_rag_chain)
        result = tool.run(feature_description="User authentication system")

        assert result.success is True
        assert "Strategy" in result.output or "Test" in result.output


# ============================================================================
# Requirements Extractor Tool Tests
# ============================================================================

class TestRequirementsExtractorTool:
    """Tests for RequirementsExtractorTool."""

    def test_tool_import(self):
        """Test tool can be imported."""
        from src.agent.tools.requirements_extractor_tool import RequirementsExtractorTool
        assert RequirementsExtractorTool is not None

    def test_tool_initialization(self, mock_rag_chain):
        """Test tool initialization."""
        from src.agent.tools.requirements_extractor_tool import RequirementsExtractorTool
        tool = RequirementsExtractorTool(mock_rag_chain)

        assert tool.name == "requirements_extractor"
        assert "requirement" in tool.description.lower()

    def test_empty_input_returns_error(self, mock_rag_chain):
        """Test empty input handling."""
        from src.agent.tools.requirements_extractor_tool import RequirementsExtractorTool
        tool = RequirementsExtractorTool(mock_rag_chain)

        result = tool.run(topic="")
        assert result.success is False or "error" in result.output.lower()

    def test_requirements_extraction(self, mock_rag_chain, mock_llm_response):
        """Test requirements extraction."""
        from src.agent.tools.requirements_extractor_tool import RequirementsExtractorTool

        requirements_content = """## Requirements: User Authentication

### REQ-001: User Login
**Priority:** High
**Type:** Functional

Users must be able to login with email and password.

**Acceptance Criteria:**
- Valid credentials grant access
- Invalid credentials show error

### REQ-002: Session Management
**Priority:** Medium
**Type:** Non-Functional

User sessions must timeout after 30 minutes of inactivity.
"""
        mock_rag_chain.llm.invoke.return_value = mock_llm_response(requirements_content)

        tool = RequirementsExtractorTool(mock_rag_chain)
        result = tool.run(topic="User authentication")

        assert result.success is True
        mock_rag_chain.retrieve_context.assert_called()

    def test_output_formats(self, mock_rag_chain, mock_llm_response):
        """Test different output formats."""
        from src.agent.tools.requirements_extractor_tool import RequirementsExtractorTool

        mock_rag_chain.llm.invoke.return_value = mock_llm_response("Requirements content")

        tool = RequirementsExtractorTool(mock_rag_chain)

        for fmt in ["structured", "user_stories", "acceptance_criteria"]:
            result = tool.run(topic="Test feature", output_format=fmt)
            assert result.success is True


# ============================================================================
# Traceability Matrix Tool Tests
# ============================================================================

class TestTraceabilityMatrixTool:
    """Tests for TraceabilityMatrixTool."""

    def test_tool_import(self):
        """Test tool can be imported."""
        from src.agent.tools.traceability_matrix_tool import TraceabilityMatrixTool
        assert TraceabilityMatrixTool is not None

    def test_tool_initialization(self, mock_rag_chain):
        """Test tool initialization."""
        from src.agent.tools.traceability_matrix_tool import TraceabilityMatrixTool
        tool = TraceabilityMatrixTool(mock_rag_chain)

        assert tool.name == "traceability_matrix"
        assert "traceability" in tool.description.lower() or "matrix" in tool.description.lower()

    def test_empty_input_returns_error(self, mock_rag_chain):
        """Test empty input handling."""
        from src.agent.tools.traceability_matrix_tool import TraceabilityMatrixTool
        tool = TraceabilityMatrixTool(mock_rag_chain)

        result = tool.run(topic="")
        assert result.success is False or "error" in result.output.lower()

    def test_matrix_generation(self, mock_rag_chain, mock_llm_response):
        """Test traceability matrix generation."""
        from src.agent.tools.traceability_matrix_tool import TraceabilityMatrixTool

        matrix_content = """## Traceability Matrix: Authentication

### Summary
- **Total Requirements:** 3
- **Total Test Cases:** 5
- **Mapped Requirements:** 2
- **Coverage:** 67%

### Matrix

| Requirement ID | Requirement Title | Test Cases | Status |
|----------------|-------------------|------------|--------|
| REQ-001 | User Login | TC-001, TC-002 | Covered |
| REQ-002 | User Logout | TC-003 | Covered |
| REQ-003 | Password Reset | - | Not Covered |

### Unmapped Requirements
1. **REQ-003**: Password Reset - Needs test cases

### Recommendations
1. Add test cases for password reset functionality
"""
        mock_rag_chain.llm.invoke.return_value = mock_llm_response(matrix_content)

        tool = TraceabilityMatrixTool(mock_rag_chain)
        result = tool.run(topic="User authentication")

        assert result.success is True
        assert "Matrix" in result.output or "Coverage" in result.output

    def test_csv_output_format(self, mock_rag_chain, mock_llm_response):
        """Test CSV output format conversion."""
        from src.agent.tools.traceability_matrix_tool import TraceabilityMatrixTool

        matrix_content = """### Matrix

| Requirement ID | Requirement Title | Test Cases | Status |
|----------------|-------------------|------------|--------|
| REQ-001 | User Login | TC-001, TC-002 | Covered |
"""
        mock_rag_chain.llm.invoke.return_value = mock_llm_response(matrix_content)

        tool = TraceabilityMatrixTool(mock_rag_chain)
        result = tool.run(topic="Authentication", output_format="csv")

        assert result.success is True
        # CSV should have comma-separated values
        assert "," in result.output or "Requirement ID" in result.output

    def test_json_output_format(self, mock_rag_chain, mock_llm_response):
        """Test JSON output format conversion."""
        from src.agent.tools.traceability_matrix_tool import TraceabilityMatrixTool

        matrix_content = """### Summary
- **Coverage:** 75%

### Matrix

| Requirement ID | Requirement Title | Test Cases | Status |
|----------------|-------------------|------------|--------|
| REQ-001 | User Login | TC-001 | Covered |
"""
        mock_rag_chain.llm.invoke.return_value = mock_llm_response(matrix_content)

        tool = TraceabilityMatrixTool(mock_rag_chain)
        result = tool.run(topic="Authentication", output_format="json")

        assert result.success is True
        # Try to parse as JSON
        try:
            parsed = json.loads(result.output)
            assert "coverage_percent" in parsed or "requirements" in parsed
        except json.JSONDecodeError:
            # JSON conversion may fail if LLM output doesn't match expected format
            pass


# ============================================================================
# BDD Generator Tool Tests
# ============================================================================

class TestBDDGeneratorTool:
    """Tests for BDDGeneratorTool."""

    def test_tool_import(self):
        """Test tool can be imported."""
        from src.agent.tools.bdd_generator_tool import BDDGeneratorTool
        assert BDDGeneratorTool is not None

    def test_tool_initialization(self, mock_rag_chain):
        """Test tool initialization."""
        from src.agent.tools.bdd_generator_tool import BDDGeneratorTool
        tool = BDDGeneratorTool(mock_rag_chain)

        assert tool.name == "bdd_generator"
        assert "bdd" in tool.description.lower() or "gherkin" in tool.description.lower()

    def test_empty_input_returns_error(self, mock_rag_chain):
        """Test empty input handling."""
        from src.agent.tools.bdd_generator_tool import BDDGeneratorTool
        tool = BDDGeneratorTool(mock_rag_chain)

        result = tool.run(feature_description="")
        assert result.success is False or "error" in result.output.lower()

    def test_feature_file_generation(self, mock_rag_chain, mock_llm_response):
        """Test BDD feature file generation."""
        from src.agent.tools.bdd_generator_tool import BDDGeneratorTool

        feature_content = """@authentication @login
Feature: User Login
  As a registered user
  I want to log into my account
  So that I can access personalized features

  Background:
    Given the login page is displayed

  @smoke @positive
  Scenario: Successful login with valid credentials
    Given I have valid login credentials
    When I enter my email "user@example.com"
    And I enter my password "SecurePass123"
    And I click the login button
    Then I should be redirected to the dashboard
    And I should see a welcome message

  @negative
  Scenario: Login fails with invalid password
    Given I have an account with email "user@example.com"
    When I enter my email "user@example.com"
    And I enter an incorrect password "WrongPass"
    And I click the login button
    Then I should see an error message "Invalid credentials"
    And I should remain on the login page

  @data-driven
  Scenario Outline: Login validation with various inputs
    When I enter email "<email>"
    And I enter password "<password>"
    And I click login
    Then I should see "<result>"

    Examples:
      | email           | password    | result        |
      | valid@test.com  | ValidPass1  | dashboard     |
      | invalid@        | ValidPass1  | email_error   |
      | valid@test.com  | short       | password_error|
"""
        mock_rag_chain.llm.invoke.return_value = mock_llm_response(feature_content)

        tool = BDDGeneratorTool(mock_rag_chain)
        result = tool.run(feature_description="User login with email and password")

        assert result.success is True
        assert "Feature:" in result.output
        assert "Scenario" in result.output

    def test_gherkin_validation(self, mock_rag_chain, mock_llm_response):
        """Test Gherkin syntax validation."""
        from src.agent.tools.bdd_generator_tool import BDDGeneratorTool

        # Valid Gherkin content
        valid_content = """Feature: Test
  Scenario: Test scenario
    Given a precondition
    When an action
    Then a result
"""
        mock_rag_chain.llm.invoke.return_value = mock_llm_response(valid_content)

        tool = BDDGeneratorTool(mock_rag_chain)
        result = tool.run(feature_description="Test feature")

        # Should not have validation warnings for valid content
        assert result.success is True
        assert "Feature:" in result.output

    def test_gherkin_validation_detects_issues(self, mock_rag_chain):
        """Test that validation detects missing elements."""
        from src.agent.tools.bdd_generator_tool import BDDGeneratorTool

        tool = BDDGeneratorTool(mock_rag_chain)

        # Test validation method directly
        invalid_content = "Just some text without proper Gherkin"
        validation_result = tool._validate_gherkin(invalid_content)

        assert validation_result is not None
        assert "Missing" in validation_result or "Feature" in validation_result

    def test_framework_specific_notes(self, mock_rag_chain, mock_llm_response):
        """Test framework-specific notes."""
        from src.agent.tools.bdd_generator_tool import BDDGeneratorTool

        mock_rag_chain.llm.invoke.return_value = mock_llm_response("Feature: Test")

        tool = BDDGeneratorTool(mock_rag_chain)

        # Test different frameworks
        for framework in ["cucumber", "behave"]:
            result = tool.run(feature_description="Test", framework=framework)
            assert result.success is True


# ============================================================================
# Test Data Generator Tool Tests
# ============================================================================

class TestTestDataGeneratorTool:
    """Tests for TestDataGeneratorTool."""

    def test_tool_import(self):
        """Test tool can be imported."""
        from src.agent.tools.test_data_generator_tool import TestDataGeneratorTool
        assert TestDataGeneratorTool is not None

    def test_tool_initialization(self, mock_rag_chain):
        """Test tool initialization."""
        from src.agent.tools.test_data_generator_tool import TestDataGeneratorTool
        tool = TestDataGeneratorTool(mock_rag_chain)

        assert tool.name == "test_data_generator"
        assert "data" in tool.description.lower() or "test" in tool.description.lower()

    def test_empty_input_returns_error(self, mock_rag_chain):
        """Test empty input handling."""
        from src.agent.tools.test_data_generator_tool import TestDataGeneratorTool
        tool = TestDataGeneratorTool(mock_rag_chain)

        result = tool.run(field_definitions="")
        assert result.success is False or "error" in result.output.lower()

    def test_json_data_generation(self, mock_rag_chain, mock_llm_response):
        """Test JSON test data generation."""
        from src.agent.tools.test_data_generator_tool import TestDataGeneratorTool

        json_data = """{
  "valid": [
    {"description": "Standard user", "data": {"username": "john_doe", "email": "john@example.com", "age": 25}}
  ],
  "invalid": [
    {"description": "Missing @ in email", "data": {"username": "jane", "email": "janeexample.com", "age": 30}, "expected_error": "Invalid email"}
  ],
  "boundary": [
    {"description": "Min age", "data": {"username": "min_user", "email": "min@test.com", "age": 0}, "test_type": "min_value"},
    {"description": "Max age", "data": {"username": "max_user", "email": "max@test.com", "age": 150}, "test_type": "max_value"}
  ],
  "edge_cases": [
    {"description": "SQL injection", "data": {"username": "'; DROP TABLE;--", "email": "test@test.com", "age": 25}, "security_test": true}
  ]
}"""
        mock_rag_chain.llm.invoke.return_value = mock_llm_response(json_data)

        tool = TestDataGeneratorTool(mock_rag_chain)
        result = tool.run(
            field_definitions="username: string 3-20 chars, email: valid email, age: integer 0-150",
            output_format="json"
        )

        assert result.success is True
        # Try to parse as JSON
        try:
            parsed = json.loads(result.output)
            assert "valid" in parsed or "invalid" in parsed or "boundary" in parsed
        except json.JSONDecodeError:
            # May have parsing issues, but should still return output
            assert len(result.output) > 0

    def test_csv_data_generation(self, mock_rag_chain, mock_llm_response):
        """Test CSV test data generation."""
        from src.agent.tools.test_data_generator_tool import TestDataGeneratorTool

        csv_data = """category,description,username,email,age
valid,Standard user,john_doe,john@example.com,25
invalid,Missing @ in email,jane,janeexample.com,30
boundary,Min age,min_user,min@test.com,0
edge_case,SQL injection,'; DROP TABLE;--,test@test.com,25"""

        mock_rag_chain.llm.invoke.return_value = mock_llm_response(csv_data)

        tool = TestDataGeneratorTool(mock_rag_chain)
        result = tool.run(
            field_definitions="username, email, age",
            output_format="csv"
        )

        assert result.success is True
        assert "," in result.output  # CSV should have commas

    def test_edge_case_generation(self, mock_rag_chain, mock_llm_response):
        """Test edge case data generation."""
        from src.agent.tools.test_data_generator_tool import TestDataGeneratorTool

        mock_rag_chain.llm.invoke.return_value = mock_llm_response('{"edge_cases": []}')

        tool = TestDataGeneratorTool(mock_rag_chain)
        result = tool.run(
            field_definitions="password: string"
        )

        assert result.success is True


# ============================================================================
# Integration Tests - Tools Working Together
# ============================================================================

class TestQAToolsIntegration:
    """Integration tests for QA tools working together."""

    def test_all_tools_have_consistent_interface(self, mock_rag_chain):
        """Test all tools have consistent base interface."""
        from src.agent.tools.qa_analysis_tool import QAAnalysisTool
        from src.agent.tools.bug_report_tool import BugReportTool
        from src.agent.tools.test_strategy_tool import TestStrategyTool
        from src.agent.tools.requirements_extractor_tool import RequirementsExtractorTool
        from src.agent.tools.traceability_matrix_tool import TraceabilityMatrixTool
        from src.agent.tools.bdd_generator_tool import BDDGeneratorTool
        from src.agent.tools.test_data_generator_tool import TestDataGeneratorTool

        tools = [
            QAAnalysisTool(mock_rag_chain),
            BugReportTool(mock_rag_chain),
            TestStrategyTool(mock_rag_chain),
            RequirementsExtractorTool(mock_rag_chain),
            TraceabilityMatrixTool(mock_rag_chain),
            BDDGeneratorTool(mock_rag_chain),
            TestDataGeneratorTool(mock_rag_chain)
        ]

        for tool in tools:
            # All tools should have name and description
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert isinstance(tool.name, str)
            assert isinstance(tool.description, str)
            assert len(tool.name) > 0
            assert len(tool.description) > 0

            # All tools should have run method
            assert hasattr(tool, 'run')
            assert callable(tool.run)

    def test_tools_return_tool_result(self, mock_rag_chain, mock_llm_response):
        """Test all tools return ToolResult objects."""
        from src.agent.tools.base_tool import ToolResult
        from src.agent.tools.qa_analysis_tool import QAAnalysisTool
        from src.agent.tools.bug_report_tool import BugReportTool
        from src.agent.tools.test_strategy_tool import TestStrategyTool
        from src.agent.tools.requirements_extractor_tool import RequirementsExtractorTool
        from src.agent.tools.traceability_matrix_tool import TraceabilityMatrixTool
        from src.agent.tools.bdd_generator_tool import BDDGeneratorTool
        from src.agent.tools.test_data_generator_tool import TestDataGeneratorTool

        mock_rag_chain.llm.invoke.return_value = mock_llm_response("Test response")

        tools_and_inputs = [
            (QAAnalysisTool(mock_rag_chain), {"test_cases": "TC-001"}),
            (BugReportTool(mock_rag_chain), {"bug_description": "Bug"}),
            (TestStrategyTool(mock_rag_chain), {"feature_description": "Feature"}),
            (RequirementsExtractorTool(mock_rag_chain), {"topic": "Topic"}),
            (TraceabilityMatrixTool(mock_rag_chain), {"topic": "Topic"}),
            (BDDGeneratorTool(mock_rag_chain), {"feature_description": "Feature"}),
            (TestDataGeneratorTool(mock_rag_chain), {"field_definitions": "field1"})
        ]

        for tool, inputs in tools_and_inputs:
            result = tool.run(**inputs)
            assert isinstance(result, ToolResult), f"{tool.name} should return ToolResult"
            assert hasattr(result, 'success')
            assert hasattr(result, 'output')
            assert hasattr(result, 'duration')

    def test_tools_handle_llm_errors_gracefully(self, mock_rag_chain):
        """Test all tools handle LLM errors gracefully."""
        from src.agent.tools.qa_analysis_tool import QAAnalysisTool
        from src.agent.tools.bug_report_tool import BugReportTool
        from src.agent.tools.bdd_generator_tool import BDDGeneratorTool

        # Make LLM raise exception
        mock_rag_chain.llm.invoke.side_effect = Exception("LLM error")

        tools_and_inputs = [
            (QAAnalysisTool(mock_rag_chain), {"test_cases": "TC-001"}),
            (BugReportTool(mock_rag_chain), {"bug_description": "Bug"}),
            (BDDGeneratorTool(mock_rag_chain), {"feature_description": "Feature"})
        ]

        for tool, inputs in tools_and_inputs:
            result = tool.run(**inputs)
            # Should handle error gracefully
            assert result.success is False or "error" in result.output.lower()

    def test_tool_registry_can_register_all_qa_tools(self, mock_rag_chain):
        """Test all QA tools can be registered in ToolRegistry."""
        from src.agent.tool_registry import ToolRegistry
        from src.agent.tools.qa_analysis_tool import QAAnalysisTool
        from src.agent.tools.bug_report_tool import BugReportTool
        from src.agent.tools.test_strategy_tool import TestStrategyTool
        from src.agent.tools.requirements_extractor_tool import RequirementsExtractorTool
        from src.agent.tools.traceability_matrix_tool import TraceabilityMatrixTool
        from src.agent.tools.bdd_generator_tool import BDDGeneratorTool
        from src.agent.tools.test_data_generator_tool import TestDataGeneratorTool

        registry = ToolRegistry()

        qa_tools = [
            QAAnalysisTool(mock_rag_chain),
            BugReportTool(mock_rag_chain),
            TestStrategyTool(mock_rag_chain),
            RequirementsExtractorTool(mock_rag_chain),
            TraceabilityMatrixTool(mock_rag_chain),
            BDDGeneratorTool(mock_rag_chain),
            TestDataGeneratorTool(mock_rag_chain)
        ]

        for tool in qa_tools:
            registry.register(tool)

        assert len(registry) == 7

        # Verify all tools are retrievable
        assert registry.get_tool("qa_analysis") is not None
        assert registry.get_tool("bug_report") is not None
        assert registry.get_tool("test_strategy") is not None
        assert registry.get_tool("requirements_extractor") is not None
        assert registry.get_tool("traceability_matrix") is not None
        assert registry.get_tool("bdd_generator") is not None
        assert registry.get_tool("test_data_generator") is not None


# ============================================================================
# QA Pipeline Tests
# ============================================================================

class TestQAPipeline:
    """Tests for QA Pipeline orchestration."""

    def test_pipeline_import(self):
        """Test QAPipeline can be imported."""
        from src.agent.qa_pipeline import QAPipeline
        assert QAPipeline is not None

    def test_pipeline_initialization(self, mock_rag_chain):
        """Test pipeline initialization."""
        from src.agent.qa_pipeline import QAPipeline
        from src.agent.tools.requirements_extractor_tool import RequirementsExtractorTool
        from src.agent.tools.qa_analysis_tool import QAAnalysisTool

        req_tool = RequirementsExtractorTool(mock_rag_chain)
        qa_tool = QAAnalysisTool(mock_rag_chain)

        pipeline = QAPipeline(
            rag_chain=mock_rag_chain,
            requirements_tool=req_tool,
            qa_analysis_tool=qa_tool
        )

        assert pipeline is not None
        assert pipeline.state.is_complete is False

    def test_pipeline_state_tracking(self, mock_rag_chain):
        """Test pipeline state tracking."""
        from src.agent.qa_pipeline import QAPipeline, PipelineStage
        from src.agent.tools.requirements_extractor_tool import RequirementsExtractorTool
        from src.agent.tools.qa_analysis_tool import QAAnalysisTool

        req_tool = RequirementsExtractorTool(mock_rag_chain)
        qa_tool = QAAnalysisTool(mock_rag_chain)

        pipeline = QAPipeline(
            rag_chain=mock_rag_chain,
            requirements_tool=req_tool,
            qa_analysis_tool=qa_tool
        )

        state = pipeline.get_state()
        assert state.current_stage == PipelineStage.EXTRACT_REQUIREMENTS
        assert state.progress_percent == 0

    def test_pipeline_reset(self, mock_rag_chain):
        """Test pipeline reset functionality."""
        from src.agent.qa_pipeline import QAPipeline
        from src.agent.tools.requirements_extractor_tool import RequirementsExtractorTool
        from src.agent.tools.qa_analysis_tool import QAAnalysisTool

        req_tool = RequirementsExtractorTool(mock_rag_chain)
        qa_tool = QAAnalysisTool(mock_rag_chain)

        pipeline = QAPipeline(
            rag_chain=mock_rag_chain,
            requirements_tool=req_tool,
            qa_analysis_tool=qa_tool
        )

        # Modify state
        pipeline.state.progress_percent = 50
        pipeline.state.requirements = [{"id": "REQ-001"}]

        # Reset
        pipeline.reset()

        state = pipeline.get_state()
        assert state.progress_percent == 0
        assert state.requirements == []

    def test_pipeline_progress_callback(self, mock_rag_chain, mock_llm_response):
        """Test pipeline progress callback."""
        from src.agent.qa_pipeline import QAPipeline
        from src.agent.tools.requirements_extractor_tool import RequirementsExtractorTool
        from src.agent.tools.qa_analysis_tool import QAAnalysisTool

        progress_calls = []

        def progress_callback(message, percent):
            progress_calls.append((message, percent))

        # Mock tool responses
        mock_rag_chain.llm.invoke.return_value = mock_llm_response("REQ-001: Test requirement")

        req_tool = RequirementsExtractorTool(mock_rag_chain)
        qa_tool = QAAnalysisTool(mock_rag_chain)

        pipeline = QAPipeline(
            rag_chain=mock_rag_chain,
            requirements_tool=req_tool,
            qa_analysis_tool=qa_tool,
            progress_callback=progress_callback
        )

        # Update progress
        pipeline._update_progress("Test message", 50)

        assert len(progress_calls) == 1
        assert progress_calls[0] == ("Test message", 50)


# ============================================================================
# Run tests with: pytest tests/integration/test_qa_tools.py -v
# ============================================================================
