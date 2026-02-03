# Policy Engine Guide

This guide explains how to use the Policy Engine for agent behavior control and governance in your RAG system.

---

## 🎯 What is the Policy Engine?

The **Policy Engine** is a production-grade governance system that controls and monitors agent behavior. It provides:

- ✅ **Tool Usage Control** - Define which tools can be used and when
- ✅ **Rate Limiting** - Prevent API abuse and control costs
- ✅ **Content Filtering** - Block inappropriate or malicious content
- ✅ **Cost Management** - Set spending limits per request/session/day
- ✅ **Access Control** - Manage user permissions and roles
- ✅ **Audit Trail** - Complete record of policy violations

---

## 📋 Prerequisites

1. **Python Packages** - Policy engine dependencies installed
2. **PostgreSQL Setup** (Optional) - For persistent policy storage and audit logs
3. **Configuration** - Environment variables configured

---

## ⚙️ Configuration

### Enable Policy Engine

Edit `.env`:
```bash
# Enable Policy Engine (default: true)
USE_POLICY_ENGINE=true

# Optional: Enable PostgreSQL for persistent policy storage
USE_POSTGRES=true
DATABASE_URL=postgresql://user:password@localhost:5432/rag_chatbot
```

### Install Dependencies

```bash
pip install pyyaml  # For policy configuration files
pip install psycopg2-binary  # For PostgreSQL storage (optional)
```

---

## 🚀 Quick Start

### 1. Default Configuration

The policy engine loads sensible defaults automatically:

```python
from src.agent.agent_executor_v3 import AgentExecutorV3

# Initialize agent with policy engine enabled (default)
agent = AgentExecutorV3(
    llm=llm,
    tool_registry=tool_registry,
    config=config,
    enable_policy_engine=True  # Default: True
)

# Execute with policy enforcement
result = agent.execute(
    query="What is machine learning?",
    session_id="user-123"  # For policy tracking
)
```

**What Happens:**
1. Query is checked against content policies
2. Rate limits are evaluated
3. Tool usage is validated before execution
4. All checks are logged for audit
5. Violations block execution and return error

### 2. Custom Policy Configuration

Create `config/policies.yaml`:

```yaml
tool_policies:
  - rule_id: allow_safe_tools
    name: Allow Safe Tools Only
    description: Restrict to safe, approved tools
    action: deny
    enabled: true
    priority: 200
    blocked_tools:
      - system_command
      - file_delete
      - database_drop
    max_executions_per_session: 50

rate_limit_policies:
  - rule_id: standard_rate_limit
    name: Standard Rate Limit
    description: Prevent abuse
    action: throttle
    enabled: true
    max_requests_per_minute: 30
    max_requests_per_hour: 500
```

Load custom configuration:

```python
from src.policy import PolicyEngine

# Initialize with custom config
policy_engine = PolicyEngine(config_path='config/policies.yaml')
```

---

## 📊 Policy Types

### 1. Tool Usage Policies

Control which tools can be used:

```yaml
tool_policies:
  - rule_id: production_tool_policy
    name: Production Tool Policy
    action: deny
    enabled: true
    allowed_tools:
      - search_web
      - search_documents
      - calculator
    blocked_tools:
      - python_executor  # Block code execution
      - system_command
    max_executions_per_session: 100
    require_approval_for_tools:
      - web_agent  # Requires manual approval
```

**Configuration Options:**
- `allowed_tools` - Whitelist of permitted tools (empty = allow all except blocked)
- `blocked_tools` - Blacklist of forbidden tools
- `max_executions_per_session` - Total tool call limit
- `max_executions_per_tool` - Per-tool limits `{"web_agent": 10}`
- `require_approval_for_tools` - Tools requiring manual approval

### 2. Rate Limit Policies

Prevent abuse with request/token limits:

```yaml
rate_limit_policies:
  - rule_id: strict_rate_limit
    name: Strict Rate Limiting
    action: throttle
    enabled: true
    max_requests_per_minute: 10
    max_requests_per_hour: 100
    max_requests_per_day: 1000
    max_tokens_per_minute: 50000
    max_tokens_per_hour: 500000
    cooldown_period_seconds: 5
```

**Configuration Options:**
- `max_requests_per_minute/hour/day` - Request frequency limits
- `max_tokens_per_minute/hour/day` - Token consumption limits
- `cooldown_period_seconds` - Minimum time between requests

### 3. Content Filter Policies

Filter dangerous or inappropriate content:

```yaml
content_policies:
  - rule_id: strict_content_filter
    name: Strict Content Filter
    action: deny
    enabled: true
    max_input_length: 10000
    max_output_length: 50000
    blocked_keywords:
      - "DROP TABLE"
      - "DELETE FROM"
      - "rm -rf"
    blocked_patterns:
      - "(?i)eval\\s*\\("
      - "(?i)exec\\s*\\("
    allow_code_execution: false
    allow_file_access: false
    pii_detection_enabled: true
```

**Configuration Options:**
- `max_input_length` - Maximum query length
- `max_output_length` - Maximum response length
- `blocked_keywords` - List of forbidden words
- `blocked_patterns` - Regex patterns to block
- `allow_code_execution/file_access/network_access` - Feature toggles
- `pii_detection_enabled` - Detect personally identifiable information

### 4. Cost Limit Policies

Control API spending:

```yaml
cost_policies:
  - rule_id: production_cost_limit
    name: Production Cost Limit
    action: deny
    enabled: true
    max_cost_per_request: 0.10
    max_cost_per_session: 1.00
    max_cost_per_day: 50.00
    cost_alert_threshold: 40.00
    token_cost_per_1k: 0.002
```

**Configuration Options:**
- `max_cost_per_request` - Per-request spending limit
- `max_cost_per_session` - Per-session spending limit
- `max_cost_per_day` - Daily spending limit
- `max_cost_per_user` - Per-user spending limit
- `cost_alert_threshold` - Warning threshold
- `token_cost_per_1k` - Cost calculation rate

### 5. Access Control Policies

Manage user permissions:

```yaml
access_policies:
  - rule_id: whitelist_users
    name: Approved Users Only
    action: deny
    enabled: true
    allowed_users:
      - "admin@company.com"
      - "user1@company.com"
    blocked_users:
      - "spam_bot"
    allowed_roles:
      - "admin"
      - "developer"
```

**Configuration Options:**
- `allowed_users` - User ID whitelist (empty = allow all except blocked)
- `blocked_users` - User ID blacklist
- `allowed_roles` - Role-based access control
- `required_permissions` - Required permission set

---

## 🎮 Usage Examples

### Basic Policy Enforcement

```python
# Policies are automatically enforced during execution
result = agent.execute(
    query="Search the web for Python tutorials",
    session_id="user-123"
)

if result.get('policy_violation'):
    print(f"Blocked: {result['final_answer']}")
    print(f"Violated rules: {result['violated_rules']}")
else:
    print(f"Answer: {result['final_answer']}")
```

### Manual Policy Evaluation

```python
from src.policy import PolicyEvaluationContext

# Create evaluation context
context = PolicyEvaluationContext(
    session_id="user-123",
    tool_name="web_search",
    input_content="What is machine learning?",
    token_count=5
)

# Evaluate policies
decision = agent.policy_engine.evaluate_all(context)

if decision.allowed:
    print("✅ Request allowed")
else:
    print(f"❌ Blocked: {decision.message}")
    for rule in decision.violated_rules:
        print(f"   - Violated: {rule.name}")
```

### Check Policy Status

```python
# Get active policies
policies = agent.get_active_policies()
print(f"Active policies: {len(policies)}")

for policy in policies:
    print(f"- {policy['name']}: {policy['action']}")

# Filter by type
tool_policies = agent.get_active_policies(policy_type='tool_usage')
print(f"Tool policies: {len(tool_policies)}")
```

### View Policy Violations

```python
# Get violations for a session
violations = agent.get_policy_violations(session_id="user-123", limit=10)

for v in violations:
    print(f"[{v['timestamp']}] {v['policy_type']}: {v['details']}")
    print(f"   Action taken: {v['action_taken']}")
```

---

## 🔍 Policy Actions

Policies can take different actions when triggered:

| Action | Behavior |
|--------|----------|
| **allow** | Permit the action (default for whitelists) |
| **deny** | Block the action completely |
| **warn** | Log warning but allow execution |
| **throttle** | Rate limit the action |
| **require_approval** | Require manual approval before execution |

### Priority System

Higher priority rules are evaluated first:

```yaml
# High priority (evaluated first)
- rule_id: security_critical
  priority: 200
  action: deny

# Medium priority
- rule_id: cost_control
  priority: 100
  action: warn

# Low priority (evaluated last)
- rule_id: general_allow
  priority: 50
  action: allow
```

**Priority Rules:**
- Higher numbers = higher priority (200 > 100 > 50)
- DENY actions always take precedence
- THROTTLE overrides ALLOW
- First matching DENY/THROTTLE blocks execution

---

## 💾 Persistent Policy Storage

### Enable PostgreSQL Storage

With PostgreSQL enabled, policies and violations are persisted:

```python
from src.policy import get_policy_store

# Initialize policy store
policy_store = get_policy_store()

# Check if available
if policy_store.is_available():
    print("✅ Policy storage ready")

    # Save a policy
    from src.policy import ToolPolicy, PolicyType, PolicyAction

    policy = ToolPolicy(
        rule_id="custom_tool_policy",
        name="Custom Tool Policy",
        description="My custom policy",
        policy_type=PolicyType.TOOL_USAGE,
        action=PolicyAction.DENY,
        blocked_tools={"dangerous_tool"}
    )

    policy_store.save_policy(policy)
```

### Initialize Database Tables

```bash
# Run database initialization
python init_database.py

# This creates:
# - policies table (policy definitions)
# - policy_violations table (audit trail)
```

### Query Policy Database

```sql
-- View all active policies
SELECT rule_id, name, policy_type, action, enabled
FROM policies
WHERE enabled = TRUE
ORDER BY priority DESC;

-- View recent violations
SELECT
    timestamp,
    policy_type,
    action_taken,
    violation_details,
    session_id
FROM policy_violations
ORDER BY timestamp DESC
LIMIT 20;

-- Violation statistics
SELECT
    policy_type,
    COUNT(*) as violation_count
FROM policy_violations
GROUP BY policy_type
ORDER BY violation_count DESC;
```

---

## 🖥️ UI Components

### Policy Dashboard (Sidebar)

```python
from src.ui.components import render_policy_dashboard

# In your Streamlit app
render_policy_dashboard(agent_executor)
```

Shows:
- Active policy count by type
- Recent violations
- Policy status

### Policy Settings Page

```python
from src.ui.components import render_policy_settings

# In your Streamlit app
render_policy_settings(agent_executor)
```

Features:
- View all policies
- Filter by type
- Enable/disable policies
- Edit policy configuration

### Violations Table

```python
from src.ui.components import render_policy_violations_table

# In your Streamlit app
render_policy_violations_table(agent_executor, session_id="user-123")
```

Features:
- Tabular violation display
- Timestamp and details
- Download as CSV

---

## 🔧 Advanced Configuration

### Environment-Specific Policies

**Development (`.env.development`):**
```bash
USE_POLICY_ENGINE=true
# Relaxed limits for testing
```

**Production (`.env.production`):**
```bash
USE_POLICY_ENGINE=true
# Strict limits for security
```

Use separate policy files:
- `config/policies.development.yaml` - Permissive policies
- `config/policies.production.yaml` - Strict policies

### Dynamic Policy Updates

```python
# Add policy at runtime
from src.policy import RateLimitPolicy, PolicyType, PolicyAction

new_policy = RateLimitPolicy(
    rule_id="emergency_throttle",
    name="Emergency Throttle",
    description="Activated during high load",
    policy_type=PolicyType.RATE_LIMIT,
    action=PolicyAction.THROTTLE,
    max_requests_per_minute=5
)

agent.policy_engine.add_policy(new_policy)

# Remove policy
agent.policy_engine.remove_policy("emergency_throttle")
```

### Custom Policy Types

Extend the policy system:

```python
from dataclasses import dataclass
from src.policy import PolicyRule, PolicyType, PolicyAction

@dataclass
class CustomPolicy(PolicyRule):
    """Your custom policy type."""
    custom_field: str = ""

# Implement custom evaluation logic
def evaluate_custom_policy(context):
    # Your logic here
    pass
```

---

## 🐛 Troubleshooting

### Policy Engine Not Working

```python
# Check if enabled
if agent.policy_engine and agent.policy_engine.is_enabled():
    print("✅ Policy engine enabled")
else:
    print("❌ Policy engine disabled")
    # Check logs for errors
```

**Common Issues:**
1. `USE_POLICY_ENGINE=false` in .env
2. Missing `pyyaml` package
3. Invalid policy configuration file
4. Policy file not found

### Policies Not Loading

```bash
# Check policy file path
ls -la src/policy/default_policies.yaml

# Verify YAML syntax
python -c "import yaml; yaml.safe_load(open('src/policy/default_policies.yaml'))"

# Check logs for parsing errors
# Look for "⚠️ Failed to load policies" messages
```

### All Requests Blocked

```python
# Check policy configuration
policies = agent.get_active_policies()
for p in policies:
    if p['action'] == 'deny' and p['enabled']:
        print(f"Blocking policy: {p['name']}")
        print(f"  Priority: {p['priority']}")
```

**Solutions:**
1. Lower priority of blocking policies
2. Add allow policies with higher priority
3. Check `allowed_tools` whitelist (empty = allow all)
4. Review `blocked_keywords` for false positives

### Violations Not Recorded

```python
# Check audit logging
if agent.policy_engine:
    print(f"Audit enabled: {agent.policy_engine.enable_audit}")

    # Check violation count
    violations = agent.policy_engine.violations
    print(f"Recorded violations: {len(violations)}")
```

**Solutions:**
1. Enable audit logging: `enable_audit=True`
2. Check PostgreSQL connection for persistent storage
3. Verify policy actions (WARN doesn't record violations)

---

## 💡 Best Practices

### 1. Start Permissive, Tighten Gradually

```yaml
# Phase 1: Development (permissive)
tool_policies:
  - action: warn  # Log but allow
    enabled: true

# Phase 2: Staging (moderate)
tool_policies:
  - action: throttle  # Rate limit
    enabled: true

# Phase 3: Production (strict)
tool_policies:
  - action: deny  # Block violations
    enabled: true
```

### 2. Use Meaningful Rule IDs

```yaml
# ✅ Good
rule_id: prod_tool_whitelist_v2
rule_id: dev_rate_limit_relaxed

# ❌ Bad
rule_id: policy1
rule_id: temp_rule
```

### 3. Document Policy Changes

```yaml
tool_policies:
  - rule_id: block_code_exec
    name: Block Code Execution
    description: |
      Blocks python_executor and code_executor tools.
      Added 2026-02-03 after security review.
      See ticket SEC-123 for context.
```

### 4. Monitor Violation Trends

```python
# Regular monitoring
violations = agent.get_policy_violations(limit=100)

# Group by type
from collections import Counter
types = Counter(v['policy_type'] for v in violations)
print(f"Top violations: {types.most_common(3)}")

# Alert on spikes
if len(violations) > 50:
    print("⚠️  HIGH VIOLATION RATE - Review policies")
```

### 5. Test Policies Before Production

```python
# Test policy in isolation
from src.policy import PolicyEngine, PolicyEvaluationContext

test_engine = PolicyEngine(config_path='config/policies.test.yaml')

test_context = PolicyEvaluationContext(
    session_id="test",
    tool_name="web_search",
    input_content="test query"
)

decision = test_engine.evaluate_all(test_context)
assert decision.allowed, "Policy blocks valid request"
```

---

## 📈 Performance Considerations

### Policy Overhead

Each policy check adds minimal overhead:
- **Tool policy check:** ~0.1-0.5ms
- **Rate limit check:** ~0.1-0.3ms
- **Content filter:** ~1-2ms (depends on content size)
- **Total overhead:** ~1-3ms per request

### Optimization Tips

1. **Limit Active Policies** - Disable unused policies
2. **Avoid Complex Regex** - Simple patterns are faster
3. **Use Priority Wisely** - High-priority policies evaluated first
4. **Cache Policy Decisions** - For repeated checks within same request

### Scaling Considerations

- **In-memory tracking** - Request counts, token usage (fast, lost on restart)
- **PostgreSQL storage** - Persistent policies and violations (durable, slower)
- **Distributed systems** - Share policy engine state via Redis/memcached

---

## 🆘 Getting Help

**Policy engine not starting?**
1. Check `USE_POLICY_ENGINE=true` in .env
2. Verify `pyyaml` is installed
3. Check policy file syntax
4. Review logs for errors

**Policies not enforcing?**
1. Verify policies are enabled
2. Check priority order
3. Review action type (WARN doesn't block)
4. Test with manual evaluation

**Too many violations?**
1. Review blocked keywords/patterns
2. Adjust rate limits
3. Check priority conflicts
4. Use WARN action during testing

**PostgreSQL storage not working?**
1. Run `python init_database.py`
2. Check `USE_POSTGRES=true`
3. Verify database connection
4. Review table creation logs

---

## 📚 Additional Resources

- **Policy Configuration:** [src/policy/default_policies.yaml](src/policy/default_policies.yaml)
- **Policy Definitions:** [src/policy/policy_definitions.py](src/policy/policy_definitions.py)
- **Policy Engine:** [src/policy/policy_engine.py](src/policy/policy_engine.py)
- **Agent Integration:** [src/agent/agent_executor_v3.py](src/agent/agent_executor_v3.py)

---

*Last updated: 2026-02-03*
