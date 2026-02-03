"""
Core Policy Engine for agent behavior control.

Evaluates policies, enforces rules, and tracks violations.
"""

import os
import re
import yaml
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

from .policy_definitions import (
    PolicyType,
    PolicyAction,
    PolicyRule,
    ToolPolicy,
    RateLimitPolicy,
    ContentPolicy,
    CostPolicy,
    AccessPolicy,
    PolicyEvaluationContext,
    PolicyDecision,
    PolicyViolationRecord,
    PolicyScope
)


class PolicyViolation(Exception):
    """Exception raised when a policy is violated."""

    def __init__(self, message: str, violated_rules: List[PolicyRule], action: PolicyAction):
        self.message = message
        self.violated_rules = violated_rules
        self.action = action
        super().__init__(message)


class PolicyEngine:
    """
    Central policy engine for agent behavior control.

    Features:
    - Tool usage policies
    - Rate limiting
    - Content filtering
    - Cost control
    - Access management
    - Audit logging
    """

    def __init__(self, config_path: Optional[str] = None, enable_audit: bool = True):
        """
        Initialize policy engine.

        Args:
            config_path: Path to policy configuration file
            enable_audit: Enable audit logging
        """
        self.policies: Dict[str, PolicyRule] = {}
        self.enable_audit = enable_audit
        self.enabled = self._check_enabled()

        # Tracking state
        self.request_counts: Dict[str, List[datetime]] = defaultdict(list)
        self.token_counts: Dict[str, List[tuple[datetime, int]]] = defaultdict(list)
        self.cost_tracking: Dict[str, List[tuple[datetime, float]]] = defaultdict(list)
        self.tool_executions: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.violations: List[PolicyViolationRecord] = []

        # Load policies from config
        if self.enabled:
            self._load_policies(config_path)
            print("✅ Policy Engine initialized")
        else:
            print("📝 Policy Engine disabled")

    def _check_enabled(self) -> bool:
        """Check if policy engine is enabled."""
        return os.getenv('USE_POLICY_ENGINE', 'true').lower() == 'true'

    def _load_policies(self, config_path: Optional[str] = None):
        """Load policies from configuration file."""
        if not config_path:
            # Try default locations
            default_paths = [
                'src/policy/default_policies.yaml',
                'config/policies.yaml',
                'policies.yaml'
            ]
            for path in default_paths:
                if os.path.exists(path):
                    config_path = path
                    break

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    self._parse_policies(config)
                print(f"📋 Loaded {len(self.policies)} policies from {config_path}")
            except Exception as e:
                print(f"⚠️  Failed to load policies: {e}")
                self._load_default_policies()
        else:
            print("📝 No policy config found, using defaults")
            self._load_default_policies()

    def _parse_policies(self, config: Dict[str, Any]):
        """Parse policies from configuration."""
        # Parse tool policies
        for policy_data in config.get('tool_policies', []):
            policy = self._create_tool_policy(policy_data)
            if policy:
                self.policies[policy.rule_id] = policy

        # Parse rate limit policies
        for policy_data in config.get('rate_limit_policies', []):
            policy = self._create_rate_limit_policy(policy_data)
            if policy:
                self.policies[policy.rule_id] = policy

        # Parse content policies
        for policy_data in config.get('content_policies', []):
            policy = self._create_content_policy(policy_data)
            if policy:
                self.policies[policy.rule_id] = policy

        # Parse cost policies
        for policy_data in config.get('cost_policies', []):
            policy = self._create_cost_policy(policy_data)
            if policy:
                self.policies[policy.rule_id] = policy

        # Parse access policies
        for policy_data in config.get('access_policies', []):
            policy = self._create_access_policy(policy_data)
            if policy:
                self.policies[policy.rule_id] = policy

    def _create_tool_policy(self, data: Dict[str, Any]) -> Optional[ToolPolicy]:
        """Create tool policy from configuration data."""
        try:
            return ToolPolicy(
                rule_id=data['rule_id'],
                name=data['name'],
                description=data.get('description', ''),
                policy_type=PolicyType.TOOL_USAGE,
                action=PolicyAction(data.get('action', 'allow')),
                enabled=data.get('enabled', True),
                priority=data.get('priority', 0),
                allowed_tools=set(data.get('allowed_tools', [])),
                blocked_tools=set(data.get('blocked_tools', [])),
                max_executions_per_session=data.get('max_executions_per_session'),
                max_executions_per_tool=data.get('max_executions_per_tool', {}),
                require_approval_for_tools=set(data.get('require_approval_for_tools', []))
            )
        except Exception as e:
            print(f"⚠️  Failed to create tool policy: {e}")
            return None

    def _create_rate_limit_policy(self, data: Dict[str, Any]) -> Optional[RateLimitPolicy]:
        """Create rate limit policy from configuration data."""
        try:
            return RateLimitPolicy(
                rule_id=data['rule_id'],
                name=data['name'],
                description=data.get('description', ''),
                policy_type=PolicyType.RATE_LIMIT,
                action=PolicyAction(data.get('action', 'throttle')),
                enabled=data.get('enabled', True),
                priority=data.get('priority', 0),
                max_requests_per_minute=data.get('max_requests_per_minute'),
                max_requests_per_hour=data.get('max_requests_per_hour'),
                max_requests_per_day=data.get('max_requests_per_day'),
                max_tokens_per_minute=data.get('max_tokens_per_minute'),
                max_tokens_per_hour=data.get('max_tokens_per_hour'),
                max_tokens_per_day=data.get('max_tokens_per_day'),
                cooldown_period_seconds=data.get('cooldown_period_seconds')
            )
        except Exception as e:
            print(f"⚠️  Failed to create rate limit policy: {e}")
            return None

    def _create_content_policy(self, data: Dict[str, Any]) -> Optional[ContentPolicy]:
        """Create content policy from configuration data."""
        try:
            return ContentPolicy(
                rule_id=data['rule_id'],
                name=data['name'],
                description=data.get('description', ''),
                policy_type=PolicyType.CONTENT_FILTER,
                action=PolicyAction(data.get('action', 'deny')),
                enabled=data.get('enabled', True),
                priority=data.get('priority', 0),
                blocked_keywords=set(data.get('blocked_keywords', [])),
                blocked_patterns=data.get('blocked_patterns', []),
                max_input_length=data.get('max_input_length'),
                max_output_length=data.get('max_output_length'),
                allow_code_execution=data.get('allow_code_execution', False),
                allow_file_access=data.get('allow_file_access', False),
                allow_network_access=data.get('allow_network_access', True),
                pii_detection_enabled=data.get('pii_detection_enabled', False),
                profanity_filter_enabled=data.get('profanity_filter_enabled', False)
            )
        except Exception as e:
            print(f"⚠️  Failed to create content policy: {e}")
            return None

    def _create_cost_policy(self, data: Dict[str, Any]) -> Optional[CostPolicy]:
        """Create cost policy from configuration data."""
        try:
            return CostPolicy(
                rule_id=data['rule_id'],
                name=data['name'],
                description=data.get('description', ''),
                policy_type=PolicyType.COST_LIMIT,
                action=PolicyAction(data.get('action', 'deny')),
                enabled=data.get('enabled', True),
                priority=data.get('priority', 0),
                max_cost_per_request=data.get('max_cost_per_request'),
                max_cost_per_session=data.get('max_cost_per_session'),
                max_cost_per_day=data.get('max_cost_per_day'),
                max_cost_per_user=data.get('max_cost_per_user'),
                cost_alert_threshold=data.get('cost_alert_threshold'),
                token_cost_per_1k=data.get('token_cost_per_1k', 0.001)
            )
        except Exception as e:
            print(f"⚠️  Failed to create cost policy: {e}")
            return None

    def _create_access_policy(self, data: Dict[str, Any]) -> Optional[AccessPolicy]:
        """Create access policy from configuration data."""
        try:
            return AccessPolicy(
                rule_id=data['rule_id'],
                name=data['name'],
                description=data.get('description', ''),
                policy_type=PolicyType.ACCESS_CONTROL,
                action=PolicyAction(data.get('action', 'deny')),
                enabled=data.get('enabled', True),
                priority=data.get('priority', 0),
                allowed_users=set(data.get('allowed_users', [])),
                blocked_users=set(data.get('blocked_users', [])),
                allowed_roles=set(data.get('allowed_roles', [])),
                required_permissions=set(data.get('required_permissions', []))
            )
        except Exception as e:
            print(f"⚠️  Failed to create access policy: {e}")
            return None

    def _load_default_policies(self):
        """Load default policies."""
        # Default: Allow all tools except dangerous ones
        self.policies['default_tool_policy'] = ToolPolicy(
            rule_id='default_tool_policy',
            name='Default Tool Policy',
            description='Allow most tools, block dangerous operations',
            policy_type=PolicyType.TOOL_USAGE,
            action=PolicyAction.ALLOW,
            blocked_tools={'system_command', 'file_delete'},
            max_executions_per_session=100
        )

        # Default: Basic rate limiting
        self.policies['default_rate_limit'] = RateLimitPolicy(
            rule_id='default_rate_limit',
            name='Default Rate Limit',
            description='Prevent abuse with reasonable limits',
            policy_type=PolicyType.RATE_LIMIT,
            action=PolicyAction.THROTTLE,
            max_requests_per_minute=60,
            max_requests_per_hour=1000,
            max_tokens_per_minute=50000
        )

        # Default: Content filtering
        self.policies['default_content_filter'] = ContentPolicy(
            rule_id='default_content_filter',
            name='Default Content Filter',
            description='Basic content safety',
            policy_type=PolicyType.CONTENT_FILTER,
            action=PolicyAction.DENY,
            max_input_length=10000,
            max_output_length=50000,
            allow_code_execution=True,
            allow_file_access=False,
            allow_network_access=True
        )

    def evaluate_tool_usage(self, context: PolicyEvaluationContext) -> PolicyDecision:
        """Evaluate tool usage against policies."""
        if not self.enabled:
            return PolicyDecision(allowed=True, action=PolicyAction.ALLOW)

        violated_rules = []
        warnings = []
        highest_action = PolicyAction.ALLOW

        # Get tool policies sorted by priority
        tool_policies = sorted(
            [p for p in self.policies.values() if isinstance(p, ToolPolicy) and p.enabled],
            key=lambda x: x.priority,
            reverse=True
        )

        for policy in tool_policies:
            # Check if tool is blocked
            if context.tool_name in policy.blocked_tools:
                violated_rules.append(policy)
                if policy.action == PolicyAction.DENY:
                    highest_action = PolicyAction.DENY
                elif policy.action == PolicyAction.WARN:
                    warnings.append(f"Tool '{context.tool_name}' is flagged by policy '{policy.name}'")

            # Check if tool is in whitelist (if whitelist exists and is not empty)
            if policy.allowed_tools and context.tool_name not in policy.allowed_tools:
                violated_rules.append(policy)
                if policy.action == PolicyAction.DENY:
                    highest_action = PolicyAction.DENY

            # Check execution limits
            session_key = f"{context.session_id}:total"
            tool_key = f"{context.session_id}:{context.tool_name}"

            if policy.max_executions_per_session:
                session_count = sum(self.tool_executions[context.session_id].values())
                if session_count >= policy.max_executions_per_session:
                    violated_rules.append(policy)
                    highest_action = PolicyAction.DENY

            if policy.max_executions_per_tool and context.tool_name in policy.max_executions_per_tool:
                tool_count = self.tool_executions[context.session_id][context.tool_name]
                max_allowed = policy.max_executions_per_tool[context.tool_name]
                if tool_count >= max_allowed:
                    violated_rules.append(policy)
                    highest_action = PolicyAction.DENY

            # Check if approval required
            if context.tool_name in policy.require_approval_for_tools:
                highest_action = PolicyAction.REQUIRE_APPROVAL

        allowed = highest_action in [PolicyAction.ALLOW, PolicyAction.WARN]
        message = None

        if not allowed:
            if highest_action == PolicyAction.DENY:
                message = f"Tool '{context.tool_name}' is blocked by policy"
            elif highest_action == PolicyAction.REQUIRE_APPROVAL:
                message = f"Tool '{context.tool_name}' requires manual approval"

        return PolicyDecision(
            allowed=allowed,
            action=highest_action,
            violated_rules=violated_rules,
            warnings=warnings,
            message=message
        )

    def evaluate_rate_limit(self, context: PolicyEvaluationContext) -> PolicyDecision:
        """Evaluate rate limits."""
        if not self.enabled:
            return PolicyDecision(allowed=True, action=PolicyAction.ALLOW)

        violated_rules = []
        warnings = []
        highest_action = PolicyAction.ALLOW

        # Get rate limit policies
        rate_policies = [p for p in self.policies.values() if isinstance(p, RateLimitPolicy) and p.enabled]

        key = context.session_id or context.user_id or 'anonymous'
        now = datetime.now()

        # Clean old entries
        self._clean_old_tracking_data(key, now)

        for policy in rate_policies:
            # Check request rate limits
            if policy.max_requests_per_minute:
                recent_requests = [t for t in self.request_counts[key] if now - t < timedelta(minutes=1)]
                if len(recent_requests) >= policy.max_requests_per_minute:
                    violated_rules.append(policy)
                    highest_action = PolicyAction.THROTTLE

            if policy.max_requests_per_hour:
                recent_requests = [t for t in self.request_counts[key] if now - t < timedelta(hours=1)]
                if len(recent_requests) >= policy.max_requests_per_hour:
                    violated_rules.append(policy)
                    highest_action = PolicyAction.THROTTLE

            # Check token rate limits
            if policy.max_tokens_per_minute:
                recent_tokens = [(t, c) for t, c in self.token_counts[key] if now - t < timedelta(minutes=1)]
                total_tokens = sum(c for _, c in recent_tokens)
                if total_tokens >= policy.max_tokens_per_minute:
                    violated_rules.append(policy)
                    highest_action = PolicyAction.THROTTLE

        # Record this request
        self.request_counts[key].append(now)
        if context.token_count > 0:
            self.token_counts[key].append((now, context.token_count))

        allowed = highest_action != PolicyAction.THROTTLE
        message = "Rate limit exceeded" if not allowed else None

        return PolicyDecision(
            allowed=allowed,
            action=highest_action,
            violated_rules=violated_rules,
            warnings=warnings,
            message=message
        )

    def evaluate_content(self, context: PolicyEvaluationContext) -> PolicyDecision:
        """Evaluate content against policies."""
        if not self.enabled:
            return PolicyDecision(allowed=True, action=PolicyAction.ALLOW)

        violated_rules = []
        warnings = []
        highest_action = PolicyAction.ALLOW

        content_policies = [p for p in self.policies.values() if isinstance(p, ContentPolicy) and p.enabled]

        for policy in content_policies:
            content = context.input_content or context.output_content or ""

            # Check length limits
            if policy.max_input_length and context.input_content:
                if len(context.input_content) > policy.max_input_length:
                    violated_rules.append(policy)
                    highest_action = PolicyAction.DENY

            # Check for blocked keywords
            if policy.blocked_keywords:
                content_lower = content.lower()
                for keyword in policy.blocked_keywords:
                    if keyword.lower() in content_lower:
                        violated_rules.append(policy)
                        if policy.action == PolicyAction.DENY:
                            highest_action = PolicyAction.DENY

            # Check for blocked patterns (regex)
            for pattern in policy.blocked_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    violated_rules.append(policy)
                    if policy.action == PolicyAction.DENY:
                        highest_action = PolicyAction.DENY

        allowed = highest_action != PolicyAction.DENY
        message = "Content violates policy" if not allowed else None

        return PolicyDecision(
            allowed=allowed,
            action=highest_action,
            violated_rules=violated_rules,
            warnings=warnings,
            message=message
        )

    def evaluate_cost(self, context: PolicyEvaluationContext) -> PolicyDecision:
        """Evaluate cost limits."""
        if not self.enabled:
            return PolicyDecision(allowed=True, action=PolicyAction.ALLOW)

        violated_rules = []
        warnings = []
        highest_action = PolicyAction.ALLOW

        cost_policies = [p for p in self.policies.values() if isinstance(p, CostPolicy) and p.enabled]

        key = context.session_id or context.user_id or 'anonymous'
        now = datetime.now()

        for policy in cost_policies:
            # Check per-request cost
            if policy.max_cost_per_request and context.estimated_cost > policy.max_cost_per_request:
                violated_rules.append(policy)
                highest_action = PolicyAction.DENY

            # Check session cost
            if policy.max_cost_per_session:
                session_costs = [c for t, c in self.cost_tracking[key]]
                total_cost = sum(session_costs) + context.estimated_cost
                if total_cost > policy.max_cost_per_session:
                    violated_rules.append(policy)
                    highest_action = PolicyAction.DENY

            # Check daily cost
            if policy.max_cost_per_day:
                daily_costs = [c for t, c in self.cost_tracking[key] if now - t < timedelta(days=1)]
                total_cost = sum(daily_costs) + context.estimated_cost
                if total_cost > policy.max_cost_per_day:
                    violated_rules.append(policy)
                    highest_action = PolicyAction.DENY

        # Record cost
        if context.estimated_cost > 0:
            self.cost_tracking[key].append((now, context.estimated_cost))

        allowed = highest_action != PolicyAction.DENY
        message = "Cost limit exceeded" if not allowed else None

        return PolicyDecision(
            allowed=allowed,
            action=highest_action,
            violated_rules=violated_rules,
            warnings=warnings,
            message=message
        )

    def evaluate_all(self, context: PolicyEvaluationContext) -> PolicyDecision:
        """Evaluate all applicable policies."""
        if not self.enabled:
            return PolicyDecision(allowed=True, action=PolicyAction.ALLOW)

        decisions = []

        # Evaluate each policy type
        if context.tool_name:
            decisions.append(self.evaluate_tool_usage(context))

        decisions.append(self.evaluate_rate_limit(context))

        if context.input_content or context.output_content:
            decisions.append(self.evaluate_content(context))

        if context.estimated_cost > 0:
            decisions.append(self.evaluate_cost(context))

        # Combine decisions
        all_violated_rules = []
        all_warnings = []
        highest_action = PolicyAction.ALLOW

        for decision in decisions:
            all_violated_rules.extend(decision.violated_rules)
            all_warnings.extend(decision.warnings)

            # DENY takes precedence over THROTTLE, which takes precedence over ALLOW
            if decision.action == PolicyAction.DENY:
                highest_action = PolicyAction.DENY
            elif decision.action == PolicyAction.THROTTLE and highest_action != PolicyAction.DENY:
                highest_action = PolicyAction.THROTTLE
            elif decision.action == PolicyAction.REQUIRE_APPROVAL and highest_action == PolicyAction.ALLOW:
                highest_action = PolicyAction.REQUIRE_APPROVAL

        allowed = highest_action in [PolicyAction.ALLOW, PolicyAction.WARN]

        # Record violation if blocked
        if not allowed and self.enable_audit:
            self._record_violation(context, all_violated_rules, highest_action)

        return PolicyDecision(
            allowed=allowed,
            action=highest_action,
            violated_rules=all_violated_rules,
            warnings=all_warnings
        )

    def record_tool_execution(self, session_id: str, tool_name: str):
        """Record a tool execution for tracking."""
        if self.enabled:
            self.tool_executions[session_id][tool_name] += 1

    def _clean_old_tracking_data(self, key: str, now: datetime):
        """Clean up old tracking data."""
        # Keep only last 24 hours of request data
        self.request_counts[key] = [t for t in self.request_counts[key] if now - t < timedelta(days=1)]
        self.token_counts[key] = [(t, c) for t, c in self.token_counts[key] if now - t < timedelta(days=1)]
        self.cost_tracking[key] = [(t, c) for t, c in self.cost_tracking[key] if now - t < timedelta(days=7)]

    def _record_violation(self, context: PolicyEvaluationContext, violated_rules: List[PolicyRule], action: PolicyAction):
        """Record a policy violation."""
        import uuid

        violation = PolicyViolationRecord(
            violation_id=str(uuid.uuid4()),
            rule_id=violated_rules[0].rule_id if violated_rules else 'unknown',
            policy_type=violated_rules[0].policy_type if violated_rules else PolicyType.TOOL_USAGE,
            action_taken=action,
            violation_details=f"Policy violation for {context.tool_name or 'request'}",
            user_id=context.user_id,
            session_id=context.session_id,
            metadata={'context': context.metadata}
        )

        self.violations.append(violation)

    def get_violations(self, session_id: Optional[str] = None, limit: int = 100) -> List[PolicyViolationRecord]:
        """Get policy violations."""
        if session_id:
            return [v for v in self.violations if v.session_id == session_id][:limit]
        return self.violations[:limit]

    def add_policy(self, policy: PolicyRule):
        """Add or update a policy."""
        self.policies[policy.rule_id] = policy

    def remove_policy(self, rule_id: str):
        """Remove a policy."""
        if rule_id in self.policies:
            del self.policies[rule_id]

    def get_policy(self, rule_id: str) -> Optional[PolicyRule]:
        """Get a policy by ID."""
        return self.policies.get(rule_id)

    def list_policies(self, policy_type: Optional[PolicyType] = None) -> List[PolicyRule]:
        """List all policies, optionally filtered by type."""
        if policy_type:
            return [p for p in self.policies.values() if p.policy_type == policy_type]
        return list(self.policies.values())

    def is_enabled(self) -> bool:
        """Check if policy engine is enabled."""
        return self.enabled
