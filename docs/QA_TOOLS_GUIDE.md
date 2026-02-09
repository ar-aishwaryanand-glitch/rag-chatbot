# QA Expert Tools - User Guide

This guide covers all QA automation tools available in the QA Expert Assistant.

## Table of Contents

1. [Overview](#overview)
2. [Test Case Generator](#test-case-generator)
3. [QA Analysis Tool](#qa-analysis-tool)
4. [Bug Report Generator](#bug-report-generator)
5. [Test Strategy Advisor](#test-strategy-advisor)
6. [Requirements Extractor](#requirements-extractor)
7. [Traceability Matrix](#traceability-matrix)
8. [BDD/Gherkin Generator](#bddgherkin-generator)
9. [Test Data Generator](#test-data-generator)
10. [QA Pipeline](#qa-pipeline)
11. [Best Practices](#best-practices)

---

## Overview

The QA Expert Assistant provides 7 specialized tools for automating QA workflows:

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| Test Case Generator | Generate test cases from requirements | Feature/requirement description | Test case documentation or pytest code |
| QA Analysis | Analyze test coverage gaps | Existing test cases | Gap analysis report |
| Bug Report | Create professional bug reports | Bug description | Formatted bug report |
| Test Strategy | Plan testing approach | Feature description | Strategy document |
| Requirements Extractor | Extract requirements from docs | Topic/feature area | Structured requirements |
| Traceability Matrix | Map requirements to tests | Topic/feature area | REQ-TC matrix |
| BDD Generator | Generate Gherkin scenarios | Feature description | .feature file content |
| Test Data Generator | Create test datasets | Field definitions | JSON/CSV test data |

---

## Test Case Generator

### What It Does
Generates comprehensive test cases from your indexed requirement documents.

### How to Use

1. **Navigate to the Test Generator tab** on the home screen
2. **Enter the feature/requirements** you want to test (e.g., "User Authentication")
3. **Select output format:**
   - **Documentation** - Markdown test case documentation
   - **Pytest Code** - Python pytest skeleton code
   - **Both** - Get both formats
4. **Set retrieval depth** (5-20 requirement chunks to use)
5. **Choose focus area:**
   - **All** - Comprehensive coverage
   - **Functional** - Happy path scenarios
   - **Edge Cases** - Boundary conditions
   - **Negative** - Error scenarios

### Example Input
```
User login with email and password - focus on security scenarios
```

### Example Output (Documentation)
```markdown
## Test Cases: User Authentication

### TC-001: Successful Login
**Priority:** High
**Type:** Functional

**Preconditions:**
- User has valid account

**Steps:**
1. Navigate to login page
2. Enter valid email
3. Enter valid password
4. Click login button

**Expected Result:**
- User is redirected to dashboard
- Session is created
```

### Tips
- Be specific about the feature area
- Import requirements documents first for best results
- Use the "Focus" option to target specific test types

---

## QA Analysis Tool

### What It Does
Analyzes existing test cases to identify coverage gaps, missing scenarios, and improvement opportunities.

### How to Use

1. In the chat, describe your test cases or paste them directly
2. Ask for gap analysis (e.g., "Analyze these test cases for coverage gaps")
3. Optionally provide requirements context

### Example Input
```
Analyze these test cases:

TC-001: Login with valid credentials
TC-002: Login with invalid password
TC-003: Logout functionality

Requirements context: User authentication with MFA support
```

### Example Output
```markdown
## Test Coverage Analysis

### Coverage Gaps
- No MFA-related test cases
- Missing session timeout testing

### Missing Scenarios
- **Edge Cases:** Login with expired account, concurrent sessions
- **Negative Tests:** Brute force protection, account lockout
- **Boundary Conditions:** Password length limits

### Risk Assessment
| Area | Risk Level | Recommendation |
|------|------------|----------------|
| MFA | High | Add MFA enable/disable tests |
| Session | Medium | Add timeout and refresh tests |

### Recommended Additional Test Cases
1. TC-004: Enable MFA with authenticator app
2. TC-005: Login with MFA code
3. TC-006: Session timeout after inactivity
```

---

## Bug Report Generator

### What It Does
Converts informal bug descriptions into professional, structured bug reports.

### How to Use

1. Describe the bug in natural language
2. Specify format if needed: "standard", "jira", or "github"

### Example Input
```
The login button doesn't work when I click it on mobile. It works fine on desktop.
Chrome on Android. The button just doesn't respond to taps.
```

### Example Output (Standard Format)
```markdown
## Bug Report

**Title:** Login button unresponsive on mobile Chrome

**Severity:** High
**Priority:** P1
**Status:** New

### Environment
- **Platform:** Mobile Web
- **Browser:** Chrome on Android
- **OS:** Android

### Description
Login button is non-functional on mobile devices. Button does not respond
to tap/click events while functioning normally on desktop browsers.

### Steps to Reproduce
1. Open application on Android device with Chrome browser
2. Navigate to login page
3. Enter valid credentials
4. Tap the login button
5. Observe: Button does not respond

### Expected Result
Button should respond to tap and initiate login process.

### Actual Result
Button is visually present but unresponsive to touch events.

### Workaround
Use desktop browser or different mobile browser (to be tested).
```

---

## Test Strategy Advisor

### What It Does
Recommends comprehensive testing strategies for features, including test types, tools, and prioritization.

### How to Use

1. Describe the feature you need to test
2. Optionally specify app type (web, mobile, API)
3. Mention existing tech stack if relevant

### Example Input
```
Plan testing strategy for a new payment processing feature.
Web application using React frontend and Node.js backend.
```

### Example Output
```markdown
## Testing Strategy: Payment Processing

### Feature Analysis
- **Complexity:** High
- **Risk Level:** Critical
- **Integration Points:** Payment gateway, database, notification service

### Testing Pyramid

```
        /\
       /  \     E2E Tests (10%)
      /----\    ~5 tests
     /      \
    /--------\  Integration Tests (25%)
   /          \ ~15 tests
  /------------\
 /              \ Unit Tests (65%)
/________________\ ~40 tests
```

### Test Types Required

| Test Type | Priority | Coverage Areas |
|-----------|----------|----------------|
| Unit Tests | High | Payment calculations, validation |
| Integration Tests | High | Payment gateway, database |
| E2E Tests | High | Complete payment flows |
| Security Tests | Critical | PCI compliance, encryption |
| Performance Tests | Medium | Load testing, response times |

### Recommended Tools

| Purpose | Tool | Alternative |
|---------|------|-------------|
| Unit Testing | Jest | Mocha |
| E2E Testing | Playwright | Cypress |
| API Testing | Postman/Newman | REST Assured |
| Security | OWASP ZAP | Burp Suite |
```

---

## Requirements Extractor

### What It Does
Extracts and structures requirements from your indexed documents.

### How to Use

1. Specify a topic or feature area
2. Choose output format:
   - **structured** - Formal requirements (REQ-XXX)
   - **user_stories** - As a/I want/So that format
   - **acceptance_criteria** - Given/When/Then criteria

### Example Input
```
Extract requirements for shopping cart functionality
```

### Example Output
```markdown
## Requirements: Shopping Cart

### REQ-001: Add Item to Cart
**Priority:** High
**Type:** Functional

Users must be able to add products to their shopping cart.

**Acceptance Criteria:**
- AC-001.1: Item appears in cart after adding
- AC-001.2: Cart count updates correctly
- AC-001.3: Item quantity can be specified

### REQ-002: Remove Item from Cart
**Priority:** High
**Type:** Functional

Users must be able to remove items from their cart.

**Acceptance Criteria:**
- AC-002.1: Item is removed when delete clicked
- AC-002.2: Cart total updates automatically
```

---

## Traceability Matrix

### What It Does
Creates a mapping between requirements (REQ-XXX) and test cases (TC-XXX) with coverage analysis.

### How to Use

1. Specify a topic or feature area
2. Choose output format: markdown, csv, or json

### Example Input
```
Generate traceability matrix for user authentication
```

### Example Output
```markdown
## Traceability Matrix: User Authentication

### Summary
- **Total Requirements:** 5
- **Total Test Cases:** 8
- **Mapped Requirements:** 4
- **Coverage:** 80%

### Matrix

| Requirement ID | Requirement Title | Test Cases | Status |
|----------------|-------------------|------------|--------|
| REQ-001 | User Login | TC-001, TC-002, TC-003 | Covered |
| REQ-002 | User Logout | TC-004 | Covered |
| REQ-003 | Password Reset | TC-005, TC-006 | Covered |
| REQ-004 | Session Management | TC-007 | Covered |
| REQ-005 | MFA Support | - | Not Covered |

### Unmapped Requirements
1. **REQ-005**: MFA Support - Needs test cases

### Recommendations
1. Add test cases for MFA functionality (REQ-005)
2. Consider adding more edge case tests for login (REQ-001)
```

---

## BDD/Gherkin Generator

### What It Does
Generates executable BDD .feature files with Given/When/Then scenarios.

### How to Use

1. Describe the feature in natural language
2. Choose framework: cucumber or behave
3. Optionally enable/disable Scenario Outline examples

### Example Input
```
User login with email and password, including MFA verification
```

### Example Output
```gherkin
@authentication @login
Feature: User Login
  As a registered user
  I want to log into my account
  So that I can access my personalized dashboard

  Background:
    Given the login page is displayed
    And the system is operational

  @smoke @positive
  Scenario: Successful login with valid credentials
    Given I have a valid user account
    When I enter my email "user@example.com"
    And I enter my password "SecurePass123"
    And I click the login button
    Then I should be redirected to the dashboard
    And I should see a welcome message

  @mfa @positive
  Scenario: Login with MFA verification
    Given I have MFA enabled on my account
    When I enter valid login credentials
    And I click the login button
    Then I should see the MFA verification screen
    When I enter a valid MFA code
    Then I should be logged in successfully

  @negative
  Scenario: Login fails with invalid password
    Given I have a valid user account
    When I enter my email "user@example.com"
    And I enter an incorrect password "WrongPassword"
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
      | email              | password    | result           |
      | valid@test.com     | ValidPass1  | dashboard        |
      | invalid@           | ValidPass1  | email_error      |
      | valid@test.com     | short       | password_error   |
      | blocked@test.com   | ValidPass1  | account_blocked  |
```

---

## Test Data Generator

### What It Does
Generates comprehensive test datasets including valid, invalid, boundary, and edge case data.

### How to Use

1. Define your fields and their types
2. Choose output format: json or csv
3. Specify number of records needed

### Example Input
```
Fields:
- username: string, 3-20 characters, alphanumeric only
- email: valid email format
- age: integer, 18-120
- phone: US phone format
```

### Example Output (JSON)
```json
{
  "valid": [
    {
      "description": "Standard user",
      "data": {
        "username": "john_doe",
        "email": "john@example.com",
        "age": 25,
        "phone": "555-123-4567"
      }
    },
    {
      "description": "Minimum values",
      "data": {
        "username": "abc",
        "email": "a@b.co",
        "age": 18,
        "phone": "555-000-0000"
      }
    }
  ],
  "invalid": [
    {
      "description": "Username too short",
      "data": {"username": "ab"},
      "expected_error": "Username must be at least 3 characters"
    },
    {
      "description": "Invalid email format",
      "data": {"email": "invalid-email"},
      "expected_error": "Invalid email format"
    }
  ],
  "boundary": [
    {
      "description": "Max username length",
      "data": {"username": "abcdefghijklmnopqrst"},
      "test_type": "max_length"
    },
    {
      "description": "Minimum age",
      "data": {"age": 18},
      "test_type": "min_value"
    }
  ],
  "edge_cases": [
    {
      "description": "SQL injection attempt",
      "data": {"username": "'; DROP TABLE users;--"},
      "security_test": true
    },
    {
      "description": "XSS attempt",
      "data": {"username": "<script>alert('xss')</script>"},
      "security_test": true
    },
    {
      "description": "Unicode characters",
      "data": {"username": "用户名测试"},
      "test_type": "unicode"
    }
  ]
}
```

---

## QA Pipeline

### What It Does
Orchestrates a complete QA workflow: Extract Requirements → Generate Test Cases → Analyze Gaps

### How to Use

1. Navigate to the QA Tools tab
2. Enter a topic/feature area
3. Click "Run Pipeline"

### Pipeline Stages

1. **Extract Requirements** (33%)
   - Retrieves requirements from indexed documents
   - Structures them with REQ-XXX IDs

2. **Generate Test Cases** (66%)
   - Creates test cases for extracted requirements
   - Covers positive, negative, and edge cases

3. **Analyze Gaps** (100%)
   - Compares test cases against requirements
   - Identifies coverage gaps
   - Provides recommendations

### Auto-Run Feature
Enable "Auto-run after import" to automatically run the pipeline when you import new documents from Confluence.

---

## Best Practices

### 1. Document Preparation
- Import requirement documents before generating test cases
- Use clear, structured requirement documents for better results
- Include acceptance criteria in your requirements

### 2. Test Case Generation
- Be specific about the feature area
- Use the "Focus" option to target specific test types
- Review and customize generated test cases

### 3. BDD Scenarios
- Use business language in scenario descriptions
- Keep scenarios focused on single behaviors
- Include both positive and negative scenarios

### 4. Test Data
- Define clear field constraints
- Always include edge case and security test data
- Validate generated data against your actual validation rules

### 5. Coverage Analysis
- Run gap analysis regularly
- Prioritize high-risk areas first
- Update test cases as requirements change

---

## Troubleshooting

### "No requirements found"
- Import documents first using the Documents tab
- Check that documents contain relevant content
- Try a more specific or broader topic

### "Tool not available"
- Restart the agent from Settings tab
- Check that all dependencies are installed
- Review error logs in terminal

### "Generation failed"
- Check your input meets minimum length requirements
- Ensure the LLM service is accessible
- Try a simpler, more focused query

---

## Quick Reference

| Action | Where | What to Enter |
|--------|-------|---------------|
| Generate test cases | Test Generator tab | Feature name + format |
| Analyze coverage | Chat | "Analyze these test cases: [paste tests]" |
| Create bug report | Chat | "Write bug report: [describe bug]" |
| Plan testing | Chat | "Test strategy for [feature]" |
| Extract requirements | Chat | "Extract requirements for [topic]" |
| Create matrix | Chat | "Traceability matrix for [topic]" |
| Generate BDD | Chat | "Generate BDD scenarios for [feature]" |
| Generate test data | Chat | "Test data for: [field definitions]" |
| Run full pipeline | QA Tools tab | Topic + click Run Pipeline |
