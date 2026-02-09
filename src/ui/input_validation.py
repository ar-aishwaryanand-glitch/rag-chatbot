"""Input validation utilities for QA Expert UI.

Provides validation functions for user inputs before they're sent to QA tools.
This improves user experience by catching invalid inputs early.
"""

from typing import Tuple, Optional, List
from dataclasses import dataclass
import re


@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    error_message: Optional[str] = None
    warnings: List[str] = None
    sanitized_value: str = ""

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class InputValidator:
    """Validates user inputs for QA tools."""

    # Minimum input lengths for different types
    MIN_LENGTHS = {
        "test_cases": 10,
        "bug_description": 15,
        "feature_description": 10,
        "topic": 3,
        "field_definitions": 5,
        "requirement_query": 5
    }

    # Maximum input lengths
    MAX_LENGTHS = {
        "test_cases": 50000,
        "bug_description": 10000,
        "feature_description": 10000,
        "topic": 500,
        "field_definitions": 5000,
        "requirement_query": 2000
    }

    @classmethod
    def validate_test_cases(cls, test_cases: str) -> ValidationResult:
        """
        Validate test cases input for QA Analysis tool.

        Args:
            test_cases: Test cases text to validate

        Returns:
            ValidationResult with validation status and any issues
        """
        if not test_cases:
            return ValidationResult(
                is_valid=False,
                error_message="Please provide test cases to analyze",
                sanitized_value=""
            )

        test_cases = test_cases.strip()

        if len(test_cases) < cls.MIN_LENGTHS["test_cases"]:
            return ValidationResult(
                is_valid=False,
                error_message=f"Test cases too short. Please provide at least {cls.MIN_LENGTHS['test_cases']} characters.",
                sanitized_value=test_cases
            )

        if len(test_cases) > cls.MAX_LENGTHS["test_cases"]:
            return ValidationResult(
                is_valid=False,
                error_message=f"Test cases too long. Maximum {cls.MAX_LENGTHS['test_cases']} characters allowed.",
                sanitized_value=test_cases[:cls.MAX_LENGTHS["test_cases"]]
            )

        warnings = []
        # Check if test cases look like actual test cases
        if not any(keyword in test_cases.lower() for keyword in ["test", "tc-", "scenario", "given", "when", "then", "verify", "check"]):
            warnings.append("Content doesn't appear to be test cases. Consider including test scenarios or steps.")

        return ValidationResult(
            is_valid=True,
            sanitized_value=test_cases,
            warnings=warnings
        )

    @classmethod
    def validate_bug_description(cls, description: str) -> ValidationResult:
        """
        Validate bug description input for Bug Report tool.

        Args:
            description: Bug description to validate

        Returns:
            ValidationResult with validation status
        """
        if not description:
            return ValidationResult(
                is_valid=False,
                error_message="Please provide a bug description",
                sanitized_value=""
            )

        description = description.strip()

        if len(description) < cls.MIN_LENGTHS["bug_description"]:
            return ValidationResult(
                is_valid=False,
                error_message=f"Description too short. Please provide at least {cls.MIN_LENGTHS['bug_description']} characters.",
                sanitized_value=description
            )

        if len(description) > cls.MAX_LENGTHS["bug_description"]:
            return ValidationResult(
                is_valid=False,
                error_message=f"Description too long. Maximum {cls.MAX_LENGTHS['bug_description']} characters.",
                sanitized_value=description[:cls.MAX_LENGTHS["bug_description"]]
            )

        warnings = []
        # Check for useful bug report content
        if not any(keyword in description.lower() for keyword in ["error", "fail", "bug", "issue", "problem", "not work", "crash", "broken"]):
            warnings.append("Consider describing what went wrong or what the expected behavior should be.")

        return ValidationResult(
            is_valid=True,
            sanitized_value=description,
            warnings=warnings
        )

    @classmethod
    def validate_feature_description(cls, description: str, tool_type: str = "bdd") -> ValidationResult:
        """
        Validate feature description for BDD Generator or Test Strategy tools.

        Args:
            description: Feature description to validate
            tool_type: Type of tool ("bdd" or "strategy")

        Returns:
            ValidationResult with validation status
        """
        if not description:
            return ValidationResult(
                is_valid=False,
                error_message="Please provide a feature description",
                sanitized_value=""
            )

        description = description.strip()

        if len(description) < cls.MIN_LENGTHS["feature_description"]:
            return ValidationResult(
                is_valid=False,
                error_message=f"Description too short. Please provide at least {cls.MIN_LENGTHS['feature_description']} characters.",
                sanitized_value=description
            )

        if len(description) > cls.MAX_LENGTHS["feature_description"]:
            return ValidationResult(
                is_valid=False,
                error_message=f"Description too long. Maximum {cls.MAX_LENGTHS['feature_description']} characters.",
                sanitized_value=description[:cls.MAX_LENGTHS["feature_description"]]
            )

        return ValidationResult(
            is_valid=True,
            sanitized_value=description
        )

    @classmethod
    def validate_topic(cls, topic: str) -> ValidationResult:
        """
        Validate topic/feature area for Requirements Extractor and Traceability Matrix.

        Args:
            topic: Topic or feature area to validate

        Returns:
            ValidationResult with validation status
        """
        if not topic:
            return ValidationResult(
                is_valid=False,
                error_message="Please provide a topic or feature area",
                sanitized_value=""
            )

        topic = topic.strip()

        if len(topic) < cls.MIN_LENGTHS["topic"]:
            return ValidationResult(
                is_valid=False,
                error_message=f"Topic too short. Please provide at least {cls.MIN_LENGTHS['topic']} characters.",
                sanitized_value=topic
            )

        if len(topic) > cls.MAX_LENGTHS["topic"]:
            return ValidationResult(
                is_valid=False,
                error_message=f"Topic too long. Maximum {cls.MAX_LENGTHS['topic']} characters.",
                sanitized_value=topic[:cls.MAX_LENGTHS["topic"]]
            )

        return ValidationResult(
            is_valid=True,
            sanitized_value=topic
        )

    @classmethod
    def validate_field_definitions(cls, fields: str) -> ValidationResult:
        """
        Validate field definitions for Test Data Generator.

        Args:
            fields: Field definitions to validate

        Returns:
            ValidationResult with validation status
        """
        if not fields:
            return ValidationResult(
                is_valid=False,
                error_message="Please provide field definitions",
                sanitized_value=""
            )

        fields = fields.strip()

        if len(fields) < cls.MIN_LENGTHS["field_definitions"]:
            return ValidationResult(
                is_valid=False,
                error_message=f"Field definitions too short. Please provide more detail.",
                sanitized_value=fields
            )

        if len(fields) > cls.MAX_LENGTHS["field_definitions"]:
            return ValidationResult(
                is_valid=False,
                error_message=f"Field definitions too long. Maximum {cls.MAX_LENGTHS['field_definitions']} characters.",
                sanitized_value=fields[:cls.MAX_LENGTHS["field_definitions"]]
            )

        warnings = []
        # Check for field format hints
        if ':' not in fields and ',' not in fields:
            warnings.append("Tip: Specify field types like 'username: string, email: email, age: integer'")

        return ValidationResult(
            is_valid=True,
            sanitized_value=fields,
            warnings=warnings
        )

    @classmethod
    def validate_requirement_query(cls, query: str) -> ValidationResult:
        """
        Validate requirement query for test case generation.

        Args:
            query: Requirement query to validate

        Returns:
            ValidationResult with validation status
        """
        if not query:
            return ValidationResult(
                is_valid=False,
                error_message="Please provide requirements to generate test cases for",
                sanitized_value=""
            )

        query = query.strip()

        if len(query) < cls.MIN_LENGTHS["requirement_query"]:
            return ValidationResult(
                is_valid=False,
                error_message=f"Query too short. Please provide at least {cls.MIN_LENGTHS['requirement_query']} characters.",
                sanitized_value=query
            )

        if len(query) > cls.MAX_LENGTHS["requirement_query"]:
            return ValidationResult(
                is_valid=False,
                error_message=f"Query too long. Maximum {cls.MAX_LENGTHS['requirement_query']} characters.",
                sanitized_value=query[:cls.MAX_LENGTHS["requirement_query"]]
            )

        return ValidationResult(
            is_valid=True,
            sanitized_value=query
        )

    @classmethod
    def validate_confluence_space_key(cls, space_key: str) -> ValidationResult:
        """
        Validate Confluence space key.

        Args:
            space_key: Confluence space key to validate

        Returns:
            ValidationResult with validation status
        """
        if not space_key:
            return ValidationResult(
                is_valid=False,
                error_message="Please provide a Confluence space key",
                sanitized_value=""
            )

        space_key = space_key.strip().upper()

        # Space keys are typically alphanumeric and short
        if not re.match(r'^[A-Z][A-Z0-9_]{0,19}$', space_key):
            return ValidationResult(
                is_valid=False,
                error_message="Invalid space key format. Use uppercase letters and numbers (e.g., DOCS, PROJ123)",
                sanitized_value=space_key
            )

        return ValidationResult(
            is_valid=True,
            sanitized_value=space_key
        )

    @classmethod
    def validate_confluence_page_id(cls, page_id: str) -> ValidationResult:
        """
        Validate Confluence page ID.

        Args:
            page_id: Confluence page ID to validate

        Returns:
            ValidationResult with validation status
        """
        if not page_id:
            return ValidationResult(
                is_valid=False,
                error_message="Please provide a page ID",
                sanitized_value=""
            )

        page_id = page_id.strip()

        # Page IDs are typically numeric
        if not page_id.isdigit():
            return ValidationResult(
                is_valid=False,
                error_message="Page ID should be numeric",
                sanitized_value=page_id
            )

        return ValidationResult(
            is_valid=True,
            sanitized_value=page_id
        )


def validate_input(input_type: str, value: str) -> ValidationResult:
    """
    Convenience function to validate input based on type.

    Args:
        input_type: Type of input ("test_cases", "bug_description", etc.)
        value: Value to validate

    Returns:
        ValidationResult
    """
    validators = {
        "test_cases": InputValidator.validate_test_cases,
        "bug_description": InputValidator.validate_bug_description,
        "feature_description": InputValidator.validate_feature_description,
        "topic": InputValidator.validate_topic,
        "field_definitions": InputValidator.validate_field_definitions,
        "requirement_query": InputValidator.validate_requirement_query,
        "confluence_space_key": InputValidator.validate_confluence_space_key,
        "confluence_page_id": InputValidator.validate_confluence_page_id
    }

    validator = validators.get(input_type)
    if validator:
        return validator(value)

    # Default: basic non-empty validation
    if not value or not value.strip():
        return ValidationResult(
            is_valid=False,
            error_message="Please provide a value",
            sanitized_value=""
        )

    return ValidationResult(
        is_valid=True,
        sanitized_value=value.strip()
    )


def show_validation_feedback(result: ValidationResult, container=None):
    """
    Display validation feedback in Streamlit.

    Args:
        result: ValidationResult to display
        container: Optional Streamlit container (uses st if not provided)
    """
    import streamlit as st

    target = container if container else st

    if not result.is_valid:
        target.error(f"⚠️ {result.error_message}")
    elif result.warnings:
        for warning in result.warnings:
            target.warning(f"💡 {warning}")
