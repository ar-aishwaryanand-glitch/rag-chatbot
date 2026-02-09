# QA Automation Features - Complete Reference Guide

> **Last Updated:** February 2026
> **Version:** 1.0
> **Purpose:** Comprehensive guide for selecting and using QA automation tools

---

## Table of Contents

1. [Quick Decision Matrix](#quick-decision-matrix)
2. [Tool Deep Dives](#tool-deep-dives)
   - [Test Case Generator](#1-test-case-generator)
   - [QA Analysis Tool](#2-qa-analysis-tool)
   - [Bug Report Generator](#3-bug-report-generator)
   - [Test Strategy Advisor](#4-test-strategy-advisor)
   - [Requirements Extractor](#5-requirements-extractor)
   - [Traceability Matrix](#6-traceability-matrix)
   - [BDD/Gherkin Generator](#7-bddgherkin-generator)
   - [Test Data Generator](#8-test-data-generator)
3. [QA Pipeline Orchestrator](#qa-pipeline-orchestrator)
4. [Workflow Recipes](#workflow-recipes)
5. [Integration Patterns](#integration-patterns)
6. [Troubleshooting](#troubleshooting)

---

## Quick Decision Matrix

Use this table to quickly identify which tool to use:

| I want to... | Use This Tool | Why |
|--------------|---------------|-----|
| Create test cases from requirements | **Test Case Generator** | Generates TC-XXX format with steps |
| Find missing test scenarios | **QA Analysis Tool** | Analyzes gaps in existing tests |
| Write a professional bug report | **Bug Report Generator** | Formats for Jira/GitHub/Standard |
| Plan testing for a new feature | **Test Strategy Advisor** | Provides test pyramid & tools |
| Get structured requirements | **Requirements Extractor** | Pulls REQ-XXX from documents |
| See requirement coverage | **Traceability Matrix** | Maps REQ → TC with % coverage |
| Create executable BDD tests | **BDD/Gherkin Generator** | Generates .feature files |
| Generate test data | **Test Data Generator** | Creates valid/invalid/boundary data |
| Run complete QA workflow | **QA Pipeline** | Chains all tools together |

---

## Tool Deep Dives

---

### 1. Test Case Generator

#### Overview
Automatically generates comprehensive test cases from feature descriptions or requirements. Uses RAG to pull relevant context from your indexed documents.

#### Technical Details

| Property | Value |
|----------|-------|
| **Tool Name** | `test_case_generator` |
| **File Location** | `src/agent/tools/test_generator_tool.py` |
| **RAG Integration** | Yes - retrieves requirement context |
| **LLM Dependency** | Yes - generates test case content |

#### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Feature/requirement to generate tests for |
| `output_format` | string | No | "documentation" | "documentation", "pytest", or "both" |
| `num_cases` | int | No | 10 | Number of test cases to generate |
| `focus` | string | No | "all" | "all", "functional", "edge_cases", "negative" |

#### Output Format

**Documentation Format:**
```markdown
## Test Cases: [Feature Name]

### TC-001: [Test Name]
**Priority:** High/Medium/Low
**Type:** Functional/Negative/Edge Case

**Preconditions:**
- Condition 1
- Condition 2

**Test Steps:**
1. Step one
2. Step two
3. Step three

**Expected Result:**
- Expected outcome

**Test Data:**
- Input: value
- Expected: result
```

**Pytest Format:**
```python
import pytest

class TestFeatureName:
    """Test cases for Feature Name."""

    def test_tc_001_happy_path(self):
        """TC-001: Verify successful scenario."""
        # Arrange
        # Act
        # Assert
        pass
```

#### When to Use

✅ **USE when:**
- Starting testing for a new feature
- Requirements documents are indexed in the system
- You need consistent test case format
- Manual test case writing is taking too long
- You want pytest skeleton code

❌ **DON'T USE when:**
- You need to analyze existing test cases (use QA Analysis)
- You want executable BDD tests (use BDD Generator)
- You only need test data, not test cases (use Test Data Generator)
- Requirements aren't documented yet (extract them first)

#### Real-World Examples

**Example 1: E-commerce Checkout**
```
Input: "Shopping cart checkout with multiple payment methods"
Focus: "all"

Output includes:
- TC-001: Successful checkout with credit card
- TC-002: Successful checkout with PayPal
- TC-003: Checkout fails with expired card
- TC-004: Checkout with empty cart (edge case)
- TC-005: Checkout with max items limit
- TC-006: Price calculation with discounts
```

**Example 2: API Authentication**
```
Input: "JWT token authentication for REST API"
Focus: "negative"

Output includes:
- TC-001: Request with expired token
- TC-002: Request with malformed token
- TC-003: Request with revoked token
- TC-004: Token refresh after expiry
- TC-005: Concurrent token usage
```

#### Pro Tips

1. **Be specific about the feature area** - "User login" generates generic tests; "User login with SSO and MFA fallback" generates targeted tests

2. **Use the focus parameter** - If you already have happy path tests, set `focus="negative"` or `focus="edge_cases"`

3. **Combine with Requirements Extractor** - First extract requirements, then generate tests for specific REQ-XXX items

---

### 2. QA Analysis Tool

#### Overview
Analyzes existing test cases to identify coverage gaps, missing scenarios, and improvement opportunities. Think of it as a "code review" for your test suite.

#### Technical Details

| Property | Value |
|----------|-------|
| **Tool Name** | `qa_analysis` |
| **File Location** | `src/agent/tools/qa_analysis_tool.py` |
| **RAG Integration** | Optional - enhances analysis with requirements |
| **LLM Dependency** | Yes - performs analysis |

#### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `test_cases` | string | Yes | - | Existing test cases to analyze |
| `requirements_context` | string | No | "" | Requirements for comparison |
| `analysis_depth` | string | No | "standard" | "quick", "standard", "comprehensive" |

#### Output Format

```markdown
## Test Coverage Analysis

### Summary
- **Total Test Cases Analyzed:** X
- **Coverage Assessment:** Good/Moderate/Poor
- **Risk Level:** Low/Medium/High

### Coverage Gaps
| Area | Gap Description | Risk Level | Priority |
|------|-----------------|------------|----------|
| Security | No authentication tests | High | P1 |
| Edge Cases | Missing boundary tests | Medium | P2 |

### Missing Scenarios
1. **Functional Gaps:**
   - Scenario description

2. **Edge Cases Missing:**
   - Boundary condition X

3. **Negative Tests Missing:**
   - Error scenario Y

### Risk Assessment
| Component | Current Coverage | Risk | Recommendation |
|-----------|------------------|------|----------------|
| Login | 60% | Medium | Add MFA tests |

### Recommended Additional Test Cases
1. TC-NEW-001: Description
2. TC-NEW-002: Description

### Improvement Suggestions
- Suggestion 1
- Suggestion 2
```

#### When to Use

✅ **USE when:**
- Reviewing existing test suite before release
- After writing tests, to validate completeness
- During sprint retrospective for test quality
- Preparing for audit/compliance review
- Onboarding to unfamiliar test codebase

❌ **DON'T USE when:**
- You have no existing test cases (use Test Case Generator)
- You want to create tests, not analyze them
- You need specific REQ-TC mapping (use Traceability Matrix)

#### Real-World Examples

**Example 1: Login Test Suite Review**
```
Input Test Cases:
TC-001: Login with valid credentials
TC-002: Login with invalid password
TC-003: Logout functionality

Analysis Output:
Coverage Gaps Identified:
- No MFA-related test cases
- Missing session timeout testing
- No account lockout tests
- Missing "remember me" functionality tests

Recommended Additions:
TC-004: Enable MFA with authenticator app
TC-005: Login with MFA code
TC-006: Session timeout after 30 min inactivity
TC-007: Account lockout after 5 failed attempts
```

**Example 2: API Test Analysis**
```
Input: API tests for /users endpoint

Gaps Found:
- No rate limiting tests
- Missing pagination edge cases
- No concurrent request handling
- Partial error response validation
```

#### Pro Tips

1. **Provide requirements context** - Analysis is much better when it can compare tests against actual requirements

2. **Use comprehensive depth for releases** - Before major releases, use `analysis_depth="comprehensive"`

3. **Run after Test Case Generator** - Generate tests, then analyze them to catch any remaining gaps

---

### 3. Bug Report Generator

#### Overview
Transforms informal bug descriptions into professional, structured bug reports ready for Jira, GitHub, or standard documentation.

#### Technical Details

| Property | Value |
|----------|-------|
| **Tool Name** | `bug_report` |
| **File Location** | `src/agent/tools/bug_report_tool.py` |
| **RAG Integration** | No |
| **LLM Dependency** | Yes - structures the report |

#### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `bug_description` | string | Yes | - | Informal bug description |
| `format_type` | string | No | "standard" | "standard", "jira", "github" |
| `severity` | string | No | auto | "critical", "high", "medium", "low" |

#### Output Formats

**Standard Format:**
```markdown
## Bug Report

**ID:** BUG-XXXX
**Title:** [Concise bug title]
**Severity:** High
**Priority:** P1
**Status:** New
**Reported By:** [Auto]
**Date:** [Auto]

### Environment
- **Platform:** Web/Mobile/Desktop
- **Browser:** Chrome 120
- **OS:** Windows 11
- **Version:** 2.3.1

### Description
[Clear description of the issue]

### Steps to Reproduce
1. Step one
2. Step two
3. Step three
4. Observe: [What happens]

### Expected Result
[What should happen]

### Actual Result
[What actually happens]

### Screenshots/Logs
[Placeholder for attachments]

### Workaround
[If any workaround exists]

### Additional Notes
[Any other relevant information]
```

**Jira Format:**
```
*Summary:* Bug title

*Priority:* High
*Labels:* bug, regression

*Description:*
h3. Environment
* Browser: Chrome 120
* OS: Windows 11

h3. Steps to Reproduce
# Step one
# Step two

h3. Expected vs Actual
||Expected||Actual||
|Should work|Doesn't work|
```

**GitHub Format:**
```markdown
### Bug Description
Brief description

### Environment
- OS: Windows 11
- Browser: Chrome 120

### Steps to Reproduce
1. Step one
2. Step two

### Expected Behavior
What should happen

### Actual Behavior
What happens

### Screenshots
<!-- Add screenshots -->

### Additional Context
<!-- Any other info -->
```

#### When to Use

✅ **USE when:**
- Found a bug during testing
- Need to document issues quickly
- Want consistent bug report format
- Reporting bugs to developers
- Creating bug reports for stakeholders

❌ **DON'T USE when:**
- Documenting feature requests (not bugs)
- Creating test cases
- Analyzing test coverage

#### Real-World Examples

**Example 1: Mobile UI Bug**
```
Input: "The submit button is not clickable on iPhone Safari.
Works fine on desktop. Just tapping does nothing."

Output:
Title: Submit button unresponsive on iOS Safari

Severity: High (blocks user workflow)

Steps to Reproduce:
1. Open application on iPhone (iOS 17)
2. Navigate to form page
3. Fill out form fields
4. Tap "Submit" button
5. Observe: Button does not respond

Root Cause Hypothesis:
- Touch event handling issue
- CSS hit area too small
- Z-index conflict with overlay
```

**Example 2: Data Bug**
```
Input: "prices are showing wrong after discount is applied.
10% off on $100 shows $89 instead of $90"

Output:
Title: Incorrect discount calculation - off by $1

Severity: Critical (financial impact)

Steps:
1. Add $100 item to cart
2. Apply 10% discount code
3. Observe: Shows $89 (expected: $90)

Impact: Potential revenue loss or customer overcharge
```

#### Pro Tips

1. **Include environment details** - More context = faster bug resolution

2. **Use Jira format for sprint work** - Direct paste into Jira tickets

3. **Be descriptive in input** - "Button broken" → poor report; "Submit button on checkout page doesn't respond to clicks on mobile Safari, works on desktop Chrome" → great report

---

### 4. Test Strategy Advisor

#### Overview
Creates comprehensive testing strategies for features, including test types, tools recommendations, test pyramid distribution, and risk-based prioritization.

#### Technical Details

| Property | Value |
|----------|-------|
| **Tool Name** | `test_strategy` |
| **File Location** | `src/agent/tools/test_strategy_tool.py` |
| **RAG Integration** | Yes - pulls feature context |
| **LLM Dependency** | Yes - generates strategy |

#### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `feature_description` | string | Yes | - | Feature to plan testing for |
| `app_type` | string | No | "web" | "web", "mobile", "api", "desktop" |
| `tech_stack` | string | No | "" | Technologies used |
| `constraints` | string | No | "" | Time/resource constraints |

#### Output Format

```markdown
## Test Strategy: [Feature Name]

### 1. Feature Analysis
- **Complexity:** High/Medium/Low
- **Risk Level:** Critical/High/Medium/Low
- **Integration Points:** [List of systems]
- **User Impact:** [Description]

### 2. Test Pyramid

```
        /\
       /  \     E2E Tests (10%)
      /----\    5-10 tests
     /      \
    /--------\  Integration Tests (25%)
   /          \ 15-20 tests
  /------------\
 /              \ Unit Tests (65%)
/________________\ 40-50 tests
```

### 3. Test Types Required

| Test Type | Priority | Scope | Estimated Count |
|-----------|----------|-------|-----------------|
| Unit Tests | High | Business logic | 40 |
| Integration | High | API contracts | 15 |
| E2E | Medium | Critical paths | 5 |
| Security | Critical | Auth, input | 10 |
| Performance | Medium | Load, response | 3 |
| Accessibility | Medium | WCAG compliance | 5 |

### 4. Testing Phases

| Phase | Focus | Duration | Exit Criteria |
|-------|-------|----------|---------------|
| Phase 1 | Unit tests | Sprint 1 | 80% coverage |
| Phase 2 | Integration | Sprint 2 | All APIs tested |
| Phase 3 | E2E | Sprint 3 | Critical paths pass |

### 5. Tool Recommendations

| Purpose | Recommended | Alternative |
|---------|-------------|-------------|
| Unit Testing | Jest | Mocha |
| E2E Testing | Playwright | Cypress |
| API Testing | Postman | REST Assured |
| Performance | k6 | JMeter |
| Security | OWASP ZAP | Burp Suite |

### 6. Risk-Based Priorities

| Risk Area | Probability | Impact | Mitigation |
|-----------|-------------|--------|------------|
| Payment failures | Medium | Critical | Extensive integration tests |
| Data loss | Low | Critical | Backup/recovery tests |

### 7. Resource Requirements
- QA Engineers: X
- Test Environment: Y
- Test Data: Z

### 8. Success Metrics
- Code Coverage: >80%
- Critical Path Coverage: 100%
- Bug Escape Rate: <5%
```

#### When to Use

✅ **USE when:**
- Starting a new project/feature
- Planning sprint testing activities
- Presenting test plan to stakeholders
- Onboarding team to testing approach
- Resource/time estimation for QA

❌ **DON'T USE when:**
- You need actual test cases (use Test Case Generator)
- Analyzing existing tests (use QA Analysis)
- You just need quick smoke tests

#### Real-World Examples

**Example 1: Payment Feature**
```
Input: "New payment processing with Stripe integration.
Tech stack: React, Node.js, PostgreSQL"

Strategy Output:
- Security Priority: CRITICAL
- PCI Compliance tests required
- Recommended: Payment sandbox for all tests
- Integration tests for Stripe webhooks
- Load testing for checkout flow
```

**Example 2: Mobile App Feature**
```
Input: "Offline mode for mobile app - sync when back online"

Strategy Output:
- Test offline data storage
- Test sync conflict resolution
- Test network transition scenarios
- Test battery/performance impact
- E2E tests on real devices required
```

#### Pro Tips

1. **Include tech stack** - Strategy changes significantly based on React vs Angular, REST vs GraphQL

2. **Mention constraints** - "2-week timeline" or "1 QA engineer" affects strategy

3. **Use for sprint planning** - Great input for estimation and resource allocation

---

### 5. Requirements Extractor

#### Overview
Extracts structured requirements from indexed documents. Transforms unstructured text into REQ-XXX formatted requirements with acceptance criteria.

#### Technical Details

| Property | Value |
|----------|-------|
| **Tool Name** | `requirements_extractor` |
| **File Location** | `src/agent/tools/requirements_extractor_tool.py` |
| **RAG Integration** | Yes - primary functionality |
| **LLM Dependency** | Yes - structures requirements |

#### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `topic` | string | Yes | - | Topic/feature area to extract |
| `output_format` | string | No | "structured" | "structured", "user_stories", "acceptance_criteria" |
| `depth` | int | No | 10 | Number of document chunks to analyze |

#### Output Formats

**Structured Format:**
```markdown
## Requirements: [Topic]

### REQ-001: [Requirement Title]
**Priority:** High/Medium/Low
**Type:** Functional/Non-Functional
**Source:** [Document name]

**Description:**
[Detailed requirement description]

**Acceptance Criteria:**
- AC-001.1: Criteria one
- AC-001.2: Criteria two
- AC-001.3: Criteria three

**Dependencies:**
- REQ-XXX (if any)

**Notes:**
- Additional context
```

**User Stories Format:**
```markdown
## User Stories: [Topic]

### US-001: [Story Title]
**As a** [role]
**I want** [feature]
**So that** [benefit]

**Acceptance Criteria:**
- [ ] Criteria 1
- [ ] Criteria 2

**Story Points:** [Estimate]
```

**Acceptance Criteria Format:**
```markdown
## Acceptance Criteria: [Topic]

### Feature: [Feature Name]

**Given** [precondition]
**When** [action]
**Then** [expected result]

---

**Given** [another precondition]
**When** [another action]
**Then** [another result]
```

#### When to Use

✅ **USE when:**
- Starting work on a feature, need requirements summary
- Documents are in Confluence/imported but unstructured
- Creating test cases and need requirements first
- Building traceability matrix
- Onboarding to new project area

❌ **DON'T USE when:**
- No documents are indexed (import first)
- You need test cases (use Test Case Generator)
- Requirements are already structured in Jira

#### Real-World Examples

**Example 1: Authentication Requirements**
```
Input: "User authentication and authorization"

Output:
REQ-001: User Registration
- Users must register with email and password
- AC: Email validation, password strength check

REQ-002: User Login
- Users must authenticate to access protected resources
- AC: Valid credentials grant access, invalid shows error

REQ-003: Password Reset
- Users must be able to reset forgotten passwords
- AC: Email link sent, expires in 24h

REQ-004: Role-Based Access
- System must enforce role-based permissions
- AC: Admin, Editor, Viewer roles defined
```

**Example 2: E-commerce Cart**
```
Input: "Shopping cart functionality"

Output:
REQ-001: Add to Cart
- Users can add products to shopping cart
- AC: Item appears, quantity selectable, price shown

REQ-002: Cart Persistence
- Cart persists across sessions
- AC: Items remain after logout/login

REQ-003: Cart Limits
- Maximum 50 items per cart
- AC: Error shown when limit exceeded
```

#### Pro Tips

1. **Import documents first** - Tool only works with indexed documents

2. **Be specific about topic** - "Cart" vs "Shopping cart checkout with guest user support"

3. **Use as first step** - Extract requirements → Generate tests → Build matrix

---

### 6. Traceability Matrix

#### Overview
Creates bidirectional mapping between requirements (REQ-XXX) and test cases (TC-XXX). Shows coverage percentage and identifies untested requirements.

#### Technical Details

| Property | Value |
|----------|-------|
| **Tool Name** | `traceability_matrix` |
| **File Location** | `src/agent/tools/traceability_matrix_tool.py` |
| **RAG Integration** | Yes - retrieves requirements and tests |
| **LLM Dependency** | Yes - performs mapping |

#### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `topic` | string | Yes | - | Topic/feature to map |
| `output_format` | string | No | "markdown" | "markdown", "csv", "json" |
| `include_gaps` | bool | No | true | Highlight unmapped items |

#### Output Format

```markdown
## Traceability Matrix: [Topic]

### Summary
| Metric | Value |
|--------|-------|
| Total Requirements | 10 |
| Total Test Cases | 15 |
| Mapped Requirements | 8 |
| Coverage | 80% |

### Coverage Status
🟢 Fully Covered: 6 requirements
🟡 Partially Covered: 2 requirements
🔴 Not Covered: 2 requirements

### Requirements → Test Cases Matrix

| REQ ID | Requirement | Test Cases | Coverage |
|--------|-------------|------------|----------|
| REQ-001 | User Login | TC-001, TC-002, TC-003 | ✅ Full |
| REQ-002 | User Logout | TC-004 | ✅ Full |
| REQ-003 | Password Reset | TC-005, TC-006 | ✅ Full |
| REQ-004 | Session Mgmt | TC-007 | 🟡 Partial |
| REQ-005 | MFA Support | - | 🔴 None |

### Test Cases → Requirements Matrix

| TC ID | Test Case | Requirements | Type |
|-------|-----------|--------------|------|
| TC-001 | Valid login | REQ-001 | Functional |
| TC-002 | Invalid password | REQ-001 | Negative |
| TC-003 | Account lockout | REQ-001 | Security |
| TC-004 | Logout redirect | REQ-002 | Functional |

### Unmapped Requirements (Gaps)
| REQ ID | Requirement | Risk | Action Needed |
|--------|-------------|------|---------------|
| REQ-005 | MFA Support | High | Create test cases |

### Orphan Test Cases
(Test cases not linked to requirements)
| TC ID | Test Case | Recommendation |
|-------|-----------|----------------|
| TC-010 | Performance test | Link to NFR |

### Recommendations
1. **High Priority:** Create tests for REQ-005 (MFA)
2. **Medium Priority:** Add more coverage for REQ-004
3. **Review:** TC-010 needs requirement linkage
```

#### When to Use

✅ **USE when:**
- Preparing for release sign-off
- Audit/compliance requirements
- Sprint review meetings
- Identifying testing gaps
- Quality metrics reporting

❌ **DON'T USE when:**
- No requirements exist (extract first)
- No test cases exist (generate first)
- You need to create tests (use Test Case Generator)

#### Real-World Examples

**Example 1: Release Readiness**
```
Input: "User management module"

Output:
Coverage: 85%
Gaps:
- REQ-007 (Bulk user import) - No tests
- REQ-009 (Audit logging) - Partial coverage

Action: Block release until 100% coverage
```

**Example 2: Compliance Audit**
```
Input: "Payment processing"

Output:
All PCI requirements mapped:
- REQ-PCI-001 → TC-SEC-001, TC-SEC-002
- REQ-PCI-002 → TC-SEC-003
- REQ-PCI-003 → TC-SEC-004, TC-SEC-005

Coverage: 100% - Audit ready
```

#### Pro Tips

1. **Run before releases** - Essential for go/no-go decisions

2. **Use CSV for spreadsheets** - Export to Excel for stakeholder review

3. **Track over time** - Compare matrices across sprints

---

### 7. BDD/Gherkin Generator

#### Overview
Generates executable Behavior-Driven Development (BDD) test files in Gherkin syntax. Creates .feature files compatible with Cucumber (Java/JS) or Behave (Python).

#### Technical Details

| Property | Value |
|----------|-------|
| **Tool Name** | `bdd_generator` |
| **File Location** | `src/agent/tools/bdd_generator_tool.py` |
| **RAG Integration** | Yes - retrieves feature context |
| **LLM Dependency** | Yes - generates scenarios |
| **Validation** | Comprehensive Gherkin syntax validation |

#### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `feature_description` | string | Yes | - | Feature to generate tests for |
| `framework` | string | No | "cucumber" | "cucumber" or "behave" |
| `include_examples` | bool | No | true | Include Scenario Outline with Examples |

#### Output Format

```gherkin
@feature-tag @module-name
Feature: [Feature Title]
  As a [role]
  I want [capability]
  So that [benefit]

  Background:
    Given [common precondition]
    And [another common setup]

  @smoke @positive @priority-high
  Scenario: [Happy path scenario name]
    Given [initial state]
    And [additional context]
    When [action is performed]
    And [additional action]
    Then [expected outcome]
    And [additional verification]

  @negative @priority-medium
  Scenario: [Error scenario name]
    Given [initial state]
    When [invalid action]
    Then [error handling]
    And [user feedback]

  @edge-case @priority-low
  Scenario: [Edge case name]
    Given [unusual state]
    When [boundary action]
    Then [correct handling]

  @data-driven @priority-high
  Scenario Outline: [Parameterized test name]
    Given user has "<role>" permissions
    When user attempts "<action>" on "<resource>"
    Then result should be "<expected_result>"

    Examples: Valid permissions
      | role    | action | resource | expected_result |
      | admin   | delete | user     | success         |
      | admin   | create | user     | success         |
      | editor  | update | content  | success         |

    Examples: Invalid permissions
      | role    | action | resource | expected_result |
      | viewer  | delete | user     | access_denied   |
      | guest   | create | user     | unauthorized    |
```

#### Validation Rules Applied

The tool validates generated Gherkin for:
- ✅ Feature keyword present with title
- ✅ At least one Scenario or Scenario Outline
- ✅ Given/When/Then steps present
- ✅ Scenario Outline has Examples table
- ✅ Placeholder syntax `<variable>` in outlines
- ✅ Valid tag format `@tag-name`
- ✅ Single Background section only
- ✅ No empty scenarios

#### When to Use

✅ **USE when:**
- Team practices BDD/ATDD
- Need executable acceptance tests
- Using Cucumber, Behave, or SpecFlow
- Want business-readable tests
- Creating living documentation

❌ **DON'T USE when:**
- Team doesn't use BDD frameworks
- Need pytest/JUnit style tests (use Test Case Generator)
- Just need test documentation, not executable tests

#### Real-World Examples

**Example 1: User Authentication**
```
Input: "User login with email, password, and optional MFA"

Output:
@authentication @login
Feature: User Login
  As a registered user
  I want to log into my account
  So that I can access personalized features

  Background:
    Given the login page is displayed
    And the authentication service is available

  @smoke @positive
  Scenario: Successful login with valid credentials
    Given I have a registered account with email "user@test.com"
    When I enter email "user@test.com"
    And I enter password "SecurePass123!"
    And I click the login button
    Then I should be redirected to the dashboard
    And I should see "Welcome back" message

  @mfa @positive
  Scenario: Login with MFA verification
    Given I have MFA enabled on my account
    And I have my authenticator app ready
    When I enter valid credentials
    And I click login
    Then I should see the MFA verification screen
    When I enter the 6-digit code from my authenticator
    Then I should be logged in successfully

  @negative @security
  Scenario: Login fails after 5 incorrect attempts
    Given I have a registered account
    When I enter incorrect password 5 times
    Then my account should be locked
    And I should see "Account locked. Try again in 30 minutes"

  @data-driven
  Scenario Outline: Login validation with various inputs
    When I enter email "<email>"
    And I enter password "<password>"
    And I click login
    Then I should see "<message>"

    Examples:
      | email           | password      | message              |
      | invalid-email   | ValidPass1    | Invalid email format |
      | user@test.com   | short         | Password too short   |
      |                 | ValidPass1    | Email is required    |
      | user@test.com   |               | Password is required |
```

**Example 2: Shopping Cart**
```
Input: "Add and remove items from shopping cart"

Output:
@cart @e-commerce
Feature: Shopping Cart Management

  @smoke
  Scenario: Add single item to empty cart
    Given my cart is empty
    When I add "Blue T-Shirt" to my cart
    Then my cart should contain 1 item
    And cart total should be "$29.99"

  @outline
  Scenario Outline: Add multiple quantities
    Given my cart is empty
    When I add <quantity> of "<product>" to cart
    Then cart should show <quantity> items
    And total should be "<expected_total>"

    Examples:
      | quantity | product      | expected_total |
      | 1        | T-Shirt      | $29.99         |
      | 2        | T-Shirt      | $59.98         |
      | 5        | Socks        | $49.95         |
```

#### Pro Tips

1. **Use Background wisely** - Common setup steps reduce duplication

2. **Tag strategically** - `@smoke`, `@regression`, `@wip` help organize test runs

3. **Scenario Outline for data variations** - One scenario, multiple data sets

4. **Keep scenarios independent** - Each should run standalone

---

### 8. Test Data Generator

#### Overview
Generates comprehensive test datasets including valid, invalid, boundary, and edge case data. Includes security test data (SQL injection, XSS) automatically.

#### Technical Details

| Property | Value |
|----------|-------|
| **Tool Name** | `test_data_generator` |
| **File Location** | `src/agent/tools/test_data_generator_tool.py` |
| **RAG Integration** | Optional - context enhancement |
| **LLM Dependency** | Yes - generates data variations |

#### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `field_definitions` | string | Yes | - | Field names and constraints |
| `output_format` | string | No | "json" | "json" or "csv" |
| `num_records` | int | No | 5 | Records per category |

#### Output Format (JSON)

```json
{
  "valid": [
    {
      "description": "Standard valid user",
      "data": {
        "username": "john_doe",
        "email": "john@example.com",
        "age": 25,
        "phone": "555-123-4567"
      }
    },
    {
      "description": "Minimum valid values",
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
      "expected_error": "Username must be at least 3 characters",
      "field": "username"
    },
    {
      "description": "Invalid email - missing @",
      "data": {"email": "invalidemail.com"},
      "expected_error": "Invalid email format",
      "field": "email"
    },
    {
      "description": "Age below minimum",
      "data": {"age": 17},
      "expected_error": "Must be 18 or older",
      "field": "age"
    }
  ],
  "boundary": [
    {
      "description": "Username at max length (20)",
      "data": {"username": "abcdefghijklmnopqrst"},
      "test_type": "max_length",
      "should_pass": true
    },
    {
      "description": "Username exceeds max (21)",
      "data": {"username": "abcdefghijklmnopqrstu"},
      "test_type": "exceeds_max",
      "should_pass": false
    },
    {
      "description": "Age at minimum boundary",
      "data": {"age": 18},
      "test_type": "min_value",
      "should_pass": true
    },
    {
      "description": "Age at maximum boundary",
      "data": {"age": 120},
      "test_type": "max_value",
      "should_pass": true
    }
  ],
  "edge_cases": [
    {
      "description": "SQL injection attempt",
      "data": {"username": "'; DROP TABLE users;--"},
      "security_test": true,
      "attack_type": "sql_injection"
    },
    {
      "description": "XSS script injection",
      "data": {"username": "<script>alert('xss')</script>"},
      "security_test": true,
      "attack_type": "xss"
    },
    {
      "description": "Unicode characters",
      "data": {"username": "用户名测试"},
      "test_type": "unicode"
    },
    {
      "description": "Emoji in input",
      "data": {"username": "john_😀_doe"},
      "test_type": "emoji"
    },
    {
      "description": "Null byte injection",
      "data": {"username": "john\u0000doe"},
      "security_test": true,
      "attack_type": "null_byte"
    },
    {
      "description": "Empty string",
      "data": {"username": ""},
      "test_type": "empty"
    },
    {
      "description": "Whitespace only",
      "data": {"username": "   "},
      "test_type": "whitespace"
    }
  ]
}
```

#### Output Format (CSV)

```csv
category,description,username,email,age,phone,expected_error
valid,Standard user,john_doe,john@example.com,25,555-123-4567,
valid,Minimum values,abc,a@b.co,18,555-000-0000,
invalid,Username too short,ab,,,Username must be 3+ chars
invalid,Invalid email,,invalid-email,,"Invalid email format"
boundary,Max username length,abcdefghijklmnopqrst,,,
boundary,Min age,,,18,,
edge_case,SQL injection,"'; DROP TABLE;--",,,
edge_case,XSS attack,"<script>alert('xss')</script>",,,
```

#### Field Type Support

| Field Type | Valid Examples | Invalid Examples | Boundary Tests |
|------------|----------------|------------------|----------------|
| string | "john_doe" | "", null | min/max length |
| email | "a@b.com" | "invalid", "@.com" | shortest valid |
| integer | 25, 0, -1 | "abc", 1.5 | min/max int |
| phone | "555-1234" | "abc", "123" | format variations |
| date | "2024-01-01" | "invalid", "32/13/2024" | past/future/leap |
| url | "https://x.com" | "not-url", "ftp://" | long URLs |
| boolean | true, false | "yes", 1, null | type coercion |

#### When to Use

✅ **USE when:**
- Testing form validation
- API payload testing
- Database constraint testing
- Security/penetration testing
- Boundary value analysis
- Exploratory testing data

❌ **DON'T USE when:**
- Need test cases, not data (use Test Case Generator)
- Need realistic production-like data (use data masking tools)
- Need specific business logic data (create manually)

#### Real-World Examples

**Example 1: User Registration Form**
```
Input: "username: string 3-20 alphanumeric,
        email: valid email format,
        password: string 8-50 with uppercase lowercase number special,
        age: integer 18-120"

Output includes:
- Valid: standard user, minimum values, maximum values
- Invalid: short username, invalid email, weak password, underage
- Boundary: exactly 3 chars, exactly 20 chars, age 18, age 120
- Edge cases: SQL injection, XSS, unicode, emoji, whitespace
```

**Example 2: Payment API**
```
Input: "amount: decimal 0.01-10000.00,
        currency: enum USD EUR GBP,
        card_number: 16 digits"

Output includes:
- Valid: typical amounts, different currencies
- Invalid: negative amount, zero, invalid currency
- Boundary: $0.01, $10000.00, $10000.01
- Edge cases: scientific notation, special chars in amount
```

#### Pro Tips

1. **Specify constraints clearly** - "3-20 characters" gives better boundary tests

2. **Include all field types** - Helps generate appropriate edge cases

3. **Use JSON for automation** - Easy to parse in test scripts

4. **Review security tests** - Ensure your app handles injection attempts

---

## Manager Agent (NEW)

### Overview
The Manager Agent is a **hierarchical orchestration layer** that sits above all QA tools. Instead of manually selecting tools, you give it high-level goals and it automatically plans, delegates, and executes tasks.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      MANAGER AGENT                               │
│         (Plans, Delegates, Synthesizes)                          │
├─────────────────────────────────────────────────────────────────┤
│                              │                                   │
│              ┌───────────────┼───────────────┐                  │
│              ▼               ▼               ▼                  │
│       ┌───────────┐   ┌───────────┐   ┌───────────┐            │
│       │ QA Agent  │   │ Dev Agent │   │ Doc Agent │            │
│       │ (Active)  │   │ (Future)  │   │ (Future)  │            │
│       └───────────┘   └───────────┘   └───────────┘            │
│              │                                                   │
│              ▼                                                   │
│       ┌─────────────────────────────────────────┐               │
│       │  8 QA Tools + Pipeline                  │               │
│       │  (Auto-selected based on goal)          │               │
│       └─────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

### How It Works

1. **You provide a goal** (natural language)
2. **Manager creates a plan** (using LLM or rules)
3. **Manager delegates tasks** to specialized agents
4. **Agents execute** using their tools
5. **Manager aggregates** results and provides summary

### File Location
`src/agent/manager_agent.py`

### Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goal` | string | Yes | High-level goal in natural language |

### Example Goals

```
# Testing Goals
"Create comprehensive tests for user authentication"
"Ensure login feature has full test coverage with BDD scenarios"
"Generate test data and analyze gaps for checkout flow"

# QA Workflow Goals
"Extract requirements and build traceability matrix for payments"
"Plan testing strategy and generate test cases for new API"
"Document bugs and create regression tests for failed features"
```

### Sample Execution

**Input:**
```
Goal: "Ensure user authentication is fully tested with BDD and test data"
```

**Manager Plan:**
```
Task 1: Extract requirements for user authentication (QA Agent)
Task 2: Generate test cases (depends on Task 1)
Task 3: Create BDD scenarios (depends on Task 1)
Task 4: Generate test data for auth fields
Task 5: Analyze coverage gaps (depends on Task 2)
```

**Output:**
- Requirements extracted (REQ-001 to REQ-010)
- Test cases generated (TC-001 to TC-025)
- BDD .feature file with 8 scenarios
- Test data JSON (valid/invalid/boundary/edge)
- Gap analysis showing 95% coverage

### When to Use

✅ **USE when:**
- You have a complex goal spanning multiple tools
- You don't want to manually chain tools
- You want AI to plan the optimal workflow
- You need comprehensive results from multiple sources

❌ **DON'T USE when:**
- You need just one specific tool output
- You want precise control over each step
- The task is simple (single tool sufficient)

### Accessing in UI

1. Open sidebar → "🤖 Manager Agent" section
2. Enter your goal in the text area
3. Click "🚀 Execute Goal"
4. Watch progress as tasks execute
5. Results appear in chat + details available

### Programmatic Usage

```python
from src.agent.manager_agent import create_manager_with_qa_agent

# Create manager with QA agent
manager = create_manager_with_qa_agent(
    rag_chain=rag_chain,
    llm=rag_chain.llm
)

# Execute a goal
result = manager.execute(
    "Create comprehensive tests for payment processing",
    progress_callback=lambda msg, pct: print(f"{pct}%: {msg}")
)

# Access results
if result['success']:
    print(result['summary'])
    for task_id, task_result in result['results'].items():
        print(f"{task_id}: {task_result['output'][:100]}")
```

### Available Specialized Agents

The Manager Agent now comes with **4 specialized agents**:

| Agent | Type | Capabilities |
|-------|------|--------------|
| **QA Agent** | `qa` | Testing, test cases, BDD, coverage, bug reports |
| **Dev Agent** | `developer` | Code generation, analysis, refactoring |
| **Doc Agent** | `documentation` | README, API docs, guides, tutorials |
| **Security Agent** | `security` | Security review, vulnerability analysis, OWASP |

### Creating a Full Manager

```python
from src.agent.manager_agent import create_full_manager

# Create manager with ALL agents
manager = create_full_manager(
    rag_chain=rag_chain,
    llm=rag_chain.llm,
    enable_memory=True  # Persistent learning
)

# Manager will route to appropriate agents
result = manager.execute("Document the API and create security tests")
# → Routes "document" to Doc Agent
# → Routes "security tests" to QA + Security Agents
```

---

## Manager Memory (Persistent Learning)

### Overview
The Manager Agent can learn from past executions using persistent memory.

### Features
- **Execution History** - Stores all past executions
- **Performance Analytics** - Tracks success rates by agent/tool
- **Smart Recommendations** - Suggests agents based on past success
- **Pattern Learning** - Learns optimal workflows

### File Location
`src/agent/manager_memory.py`

### How It Works

```python
# Memory is automatically enabled with create_full_manager
manager = create_full_manager(rag_chain, llm, enable_memory=True)

# Execute goals (automatically recorded)
result = manager.execute("Create tests for auth")

# Get recommendations for new goals
recommendations = manager.get_recommendations("Test the payment flow")
# Returns: {"suggested_agents": ["qa"], "estimated_tasks": 3, "tips": [...]}

# Find similar past executions
similar = manager.get_similar_executions("Test login feature")

# Get performance summary
perf = manager.get_performance_summary()
# Returns: {"total_executions": 50, "success_rate": 0.85, ...}
```

### Memory Storage
```
data/manager_memory/
├── execution_history.jsonl   # All past executions
├── agent_performance.json    # Performance metrics
└── learned_patterns.json     # Successful patterns
```

---

## Task Scheduler (Automated Workflows)

### Overview
Schedule recurring QA tasks to run automatically.

### File Location
`src/agent/task_scheduler.py`

### Schedule Types

| Type | Description | Example |
|------|-------------|---------|
| `once` | Run once at specific time | "Run at 2pm tomorrow" |
| `daily` | Run every day at set time | "Run at 9am daily" |
| `weekly` | Run on specific day | "Run Monday at 8am" |
| `hourly` | Run every hour | "Check every hour" |
| `interval` | Run every N minutes | "Every 30 minutes" |

### Usage

```python
from src.agent.task_scheduler import TaskScheduler

# Create scheduler
scheduler = TaskScheduler(manager_agent)

# Schedule daily QA analysis
task_id = scheduler.schedule_recurring(
    goal="Run QA analysis for user authentication",
    schedule_type="daily",
    time="09:00"
)

# Schedule weekly coverage report
scheduler.schedule_recurring(
    goal="Generate traceability matrix for all modules",
    schedule_type="weekly",
    day_of_week=0,  # Monday
    time="08:00"
)

# Start the scheduler (runs in background)
scheduler.start()

# Check status
status = scheduler.get_status()
# {"running": True, "total_tasks": 2, "next_scheduled": "2024-01-15T09:00:00"}

# Stop scheduler
scheduler.stop()
```

### UI Access

1. Open sidebar → "📅 Task Scheduler"
2. Add scheduled tasks with goal and frequency
3. Start/stop scheduler
4. View pending and running tasks

### Helper Functions

```python
from src.agent.task_scheduler import (
    create_daily_qa_schedule,
    create_weekly_coverage_report
)

# Quick daily QA setup
task_id = create_daily_qa_schedule(manager, "auth module", time="09:00")

# Quick weekly reports for multiple topics
task_ids = create_weekly_coverage_report(
    manager,
    topics=["auth", "payments", "orders"],
    day_of_week=0,
    time="08:00"
)
```

---

## QA Pipeline Orchestrator

### Overview
Chains multiple tools together for complete QA workflows. Runs: Extract Requirements → Generate Test Cases → Analyze Gaps.

### File Location
`src/agent/qa_pipeline.py`

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────┐
│                        QA PIPELINE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  STAGE 1     │    │  STAGE 2     │    │  STAGE 3     │      │
│  │              │    │              │    │              │      │
│  │  Extract     │───▶│  Generate    │───▶│  Analyze     │      │
│  │  Requirements│    │  Test Cases  │    │  Gaps        │      │
│  │              │    │              │    │              │      │
│  │  (33%)       │    │  (66%)       │    │  (100%)      │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│    REQ-001...          TC-001...         Gap Report             │
│    REQ-002...          TC-002...         Coverage %             │
│    REQ-003...          TC-003...         Recommendations        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Usage

**Manual Trigger:**
1. Go to QA Tools tab
2. Enter topic
3. Click "Run QA Pipeline"

**Auto Trigger:**
1. Enable "Auto-run after import"
2. Import documents from Confluence
3. Pipeline runs automatically

### Output

Combined results from all three stages in a single report.

---

## Workflow Recipes

### Recipe 1: New Feature Testing (Complete)

```
1. Import requirements from Confluence
           ↓
2. Run QA Pipeline (auto or manual)
           ↓
3. Review gap analysis
           ↓
4. Generate BDD scenarios for execution
           ↓
5. Generate test data for scenarios
           ↓
6. Execute tests
           ↓
7. Report bugs using Bug Reporter
```

### Recipe 2: Sprint Test Planning

```
1. Extract requirements for sprint features
           ↓
2. Get Test Strategy recommendations
           ↓
3. Generate test cases
           ↓
4. Build traceability matrix
           ↓
5. Estimate effort based on coverage
```

### Recipe 3: Release Readiness Check

```
1. Run Traceability Matrix
           ↓
2. If coverage < 100%, run QA Analysis
           ↓
3. Generate missing test cases
           ↓
4. Re-run matrix to confirm coverage
           ↓
5. Sign off for release
```

### Recipe 4: Bug Found During Testing

```
1. Document bug informally
           ↓
2. Use Bug Report Generator (Jira format)
           ↓
3. Copy to Jira
           ↓
4. Generate additional test cases for bug area
           ↓
5. Add to regression suite
```

### Recipe 5: Security Testing

```
1. Generate Test Data with edge cases
           ↓
2. Focus on security_test: true items
           ↓
3. Generate BDD scenarios for security
           ↓
4. Run security test cases
           ↓
5. Report vulnerabilities as bugs
```

---

## Integration Patterns

### Pattern 1: CI/CD Integration

```yaml
# .github/workflows/qa-automation.yml
name: QA Automation

on:
  pull_request:
    paths:
      - 'requirements/**'

jobs:
  generate-tests:
    steps:
      - name: Extract Requirements
        run: qa-tool extract --topic "${{ github.event.pull_request.title }}"

      - name: Generate Test Cases
        run: qa-tool generate --format pytest

      - name: Run Tests
        run: pytest tests/generated/
```

### Pattern 2: Confluence Webhook

```python
# Auto-trigger on Confluence page update
@app.route('/webhook/confluence', methods=['POST'])
def confluence_update():
    page_id = request.json['page']['id']

    # Import updated page
    import_confluence_page(page_id)

    # Trigger QA pipeline
    run_qa_pipeline(topic=request.json['page']['title'])

    return {'status': 'pipeline_triggered'}
```

### Pattern 3: Jira Integration

```python
# Create Jira tickets from gaps
def create_jira_tickets_from_gaps(matrix_result):
    gaps = matrix_result['unmapped_requirements']

    for req in gaps:
        jira.create_issue(
            project='QA',
            issue_type='Task',
            summary=f"Create tests for {req['id']}",
            description=f"Requirement: {req['description']}\nRisk: {req['risk']}"
        )
```

---

## Troubleshooting

### Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| "No requirements found" | Documents not indexed | Import documents first |
| "Tool not available" | Tool not registered | Restart the agent |
| "Generation failed" | LLM error | Check API keys, retry |
| "Empty output" | Input too vague | Be more specific |
| "Low coverage %" | Few documents indexed | Import more documentation |

### Validation Errors

**BDD Generator Errors:**
- "Missing Feature keyword" → Output malformed, regenerate
- "No Then steps" → Scenarios lack assertions, regenerate
- "Scenario Outline missing Examples" → Data table needed

**Test Data Errors:**
- "Invalid JSON" → LLM output parsing failed, retry
- "Missing categories" → Field definitions unclear

### Performance Tips

1. **Start specific** - Narrow topics give better results faster
2. **Index incrementally** - Don't import entire Confluence at once
3. **Cache results** - Pipeline results stored in session state
4. **Use appropriate depth** - Don't over-retrieve for simple queries

---

## Appendix: Quick Reference Card

```
┌────────────────────────────────────────────────────────────────┐
│                    QA TOOLS QUICK REFERENCE                     │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CREATE TEST CASES        → Test Case Generator                 │
│  FIND GAPS                → QA Analysis Tool                    │
│  DOCUMENT BUGS            → Bug Report Generator                │
│  PLAN TESTING             → Test Strategy Advisor               │
│  GET REQUIREMENTS         → Requirements Extractor              │
│  CHECK COVERAGE           → Traceability Matrix                 │
│  CREATE BDD TESTS         → BDD/Gherkin Generator               │
│  GENERATE TEST DATA       → Test Data Generator                 │
│  RUN FULL WORKFLOW        → QA Pipeline                         │
│                                                                 │
│  ═══════════════════════════════════════════════════════════   │
│  🤖 MANAGER AGENT (NEW)                                         │
│  ═══════════════════════════════════════════════════════════   │
│  GIVE GOAL, LET AI PLAN   → Manager Agent                       │
│                                                                 │
│  Example: "Ensure login is fully tested with BDD and data"      │
│  Manager auto-runs: Requirements → Tests → BDD → Data → Gaps    │
│                                                                 │
├────────────────────────────────────────────────────────────────┤
│  MANUAL WORKFLOW:                                               │
│  Import Docs → Pipeline → Review → BDD → Test Data              │
│                                                                 │
│  AI-DRIVEN WORKFLOW:                                            │
│  Give Goal to Manager Agent → Let AI Plan & Execute → Review    │
└────────────────────────────────────────────────────────────────┘
```

---

*Document maintained by QA Automation Team*
*For issues: Check troubleshooting section or contact support*
