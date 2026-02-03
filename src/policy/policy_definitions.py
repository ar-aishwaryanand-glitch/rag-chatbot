"""
Policy definitions and data structures for the policy engine.

Defines policy types, rules, and constraints for agent behavior control.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from datetime import datetime


class PolicyType(Enum):
    """Types of policies supported by the engine."""
    TOOL_USAGE = "tool_usage"           # Control which tools can be used
    RATE_LIMIT = "rate_limit"           # Limit request frequency
    CONTENT_FILTER = "content_filter"   # Filter input/output content
    COST_LIMIT = "cost_limit"           # Control API costs
    ACCESS_CONTROL = "access_control"   # User permissions
    RESOURCE_LIMIT = "resource_limit"   # Execution limits


class PolicyAction(Enum):
    """Actions to take when a policy is triggered."""
    ALLOW = "allow"           # Allow the action
    DENY = "deny"             # Block the action
    WARN = "warn"             # Log warning but allow
    THROTTLE = "throttle"     # Rate limit the action
    REQUIRE_APPROVAL = "require_approval"  # Require manual approval


class PolicyScope(Enum):
    """Scope of policy application."""
    GLOBAL = "global"         # Applies to all users
    USER = "user"             # Applies to specific user
    SESSION = "session"       # Applies to specific session
    TOOL = "tool"             # Applies to specific tool


@dataclass
class PolicyRule:
    """Base policy rule structure."""
    rule_id: str
    name: str
    description: str
    policy_type: PolicyType
    action: PolicyAction
    enabled: bool = True
    priority: int = 0  # Higher priority rules are evaluated first
    scope: PolicyScope = PolicyScope.GLOBAL
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ToolPolicy(PolicyRule):
    """Policy for controlling tool usage."""
    allowed_tools: Optional[Set[str]] = None      # Whitelist of allowed tools
    blocked_tools: Optional[Set[str]] = None      # Blacklist of blocked tools
    max_executions_per_session: Optional[int] = None
    max_executions_per_tool: Optional[Dict[str, int]] = None
    require_approval_for_tools: Optional[Set[str]] = None

    def __post_init__(self):
        """Initialize sets if None."""
        if self.allowed_tools is None:
            self.allowed_tools = set()
        if self.blocked_tools is None:
            self.blocked_tools = set()
        if self.require_approval_for_tools is None:
            self.require_approval_for_tools = set()
        if self.max_executions_per_tool is None:
            self.max_executions_per_tool = {}


@dataclass
class RateLimitPolicy(PolicyRule):
    """Policy for rate limiting requests."""
    max_requests_per_minute: Optional[int] = None
    max_requests_per_hour: Optional[int] = None
    max_requests_per_day: Optional[int] = None
    max_tokens_per_minute: Optional[int] = None
    max_tokens_per_hour: Optional[int] = None
    max_tokens_per_day: Optional[int] = None
    cooldown_period_seconds: Optional[int] = None


@dataclass
class ContentPolicy(PolicyRule):
    """Policy for content filtering."""
    blocked_keywords: Set[str] = field(default_factory=set)
    blocked_patterns: List[str] = field(default_factory=list)  # Regex patterns
    max_input_length: Optional[int] = None
    max_output_length: Optional[int] = None
    allow_code_execution: bool = False
    allow_file_access: bool = False
    allow_network_access: bool = True
    pii_detection_enabled: bool = False
    profanity_filter_enabled: bool = False


@dataclass
class CostPolicy(PolicyRule):
    """Policy for cost control."""
    max_cost_per_request: Optional[float] = None
    max_cost_per_session: Optional[float] = None
    max_cost_per_day: Optional[float] = None
    max_cost_per_user: Optional[float] = None
    cost_alert_threshold: Optional[float] = None
    token_cost_per_1k: float = 0.001  # Default cost per 1k tokens


@dataclass
class AccessPolicy(PolicyRule):
    """Policy for access control."""
    allowed_users: Set[str] = field(default_factory=set)
    blocked_users: Set[str] = field(default_factory=set)
    allowed_roles: Set[str] = field(default_factory=set)
    required_permissions: Set[str] = field(default_factory=set)
    ip_whitelist: Set[str] = field(default_factory=set)
    ip_blacklist: Set[str] = field(default_factory=set)


@dataclass
class PolicyViolationRecord:
    """Record of a policy violation."""
    violation_id: str
    rule_id: str
    policy_type: PolicyType
    action_taken: PolicyAction
    violation_details: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyEvaluationContext:
    """Context information for policy evaluation."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tool_name: Optional[str] = None
    input_content: Optional[str] = None
    output_content: Optional[str] = None
    token_count: int = 0
    estimated_cost: float = 0.0
    request_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyDecision:
    """Result of policy evaluation."""
    allowed: bool
    action: PolicyAction
    violated_rules: List[PolicyRule] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
