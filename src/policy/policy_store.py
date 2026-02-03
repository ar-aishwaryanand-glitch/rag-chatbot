"""
PostgreSQL storage for policies and violations.

Enables persistent policy management and audit trails.
"""

import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.pool import SimpleConnectionPool
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from .policy_definitions import (
    PolicyType,
    PolicyAction,
    PolicyRule,
    ToolPolicy,
    RateLimitPolicy,
    ContentPolicy,
    CostPolicy,
    AccessPolicy,
    PolicyViolationRecord,
    PolicyScope
)


class PolicyStore:
    """
    PostgreSQL storage for policies and violations.

    Features:
    - Persistent policy storage
    - Policy versioning
    - Violation audit trail
    - Policy templates
    """

    def __init__(self, connection_string: Optional[str] = None):
        """Initialize policy store."""
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 not installed. Run: pip install psycopg2-binary")

        self.connection_string = connection_string or self._get_connection_string()
        self.enabled = self._check_enabled()
        self.pool = None

        if self.enabled:
            self._initialize_pool()

    def _check_enabled(self) -> bool:
        """Check if PostgreSQL is enabled."""
        return os.getenv('USE_POSTGRES', 'false').lower() == 'true'

    def _get_connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        conn_str = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')

        if conn_str:
            return conn_str

        user = os.getenv('POSTGRES_USER', 'postgres')
        password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        database = os.getenv('POSTGRES_DB', 'rag_chatbot')

        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    def _initialize_pool(self):
        """Initialize connection pool."""
        try:
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=5,
                dsn=self.connection_string
            )
            print("✅ Policy store initialized")
        except Exception as e:
            print(f"⚠️  Failed to initialize policy store: {e}")
            self.enabled = False

    @contextmanager
    def get_connection(self):
        """Get database connection from pool."""
        if not self.enabled or not self.pool:
            yield None
            return

        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        finally:
            if conn:
                self.pool.putconn(conn)

    def initialize_tables(self):
        """Create policy storage tables."""
        if not self.enabled:
            return

        with self.get_connection() as conn:
            if not conn:
                return

            cursor = conn.cursor()

            # Create policies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS policies (
                    rule_id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    policy_type VARCHAR(50) NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    priority INTEGER DEFAULT 0,
                    scope VARCHAR(50) DEFAULT 'global',
                    policy_data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1
                )
            """)

            # Create policy violations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS policy_violations (
                    violation_id VARCHAR(255) PRIMARY KEY,
                    rule_id VARCHAR(255),
                    policy_type VARCHAR(50) NOT NULL,
                    action_taken VARCHAR(50) NOT NULL,
                    violation_details TEXT,
                    user_id VARCHAR(255),
                    session_id VARCHAR(255),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_policies_type
                ON policies(policy_type)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_policies_enabled
                ON policies(enabled)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_violations_session
                ON policy_violations(session_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_violations_timestamp
                ON policy_violations(timestamp)
            """)

            conn.commit()
            cursor.close()

            print("✅ Policy tables created")

    def save_policy(self, policy: PolicyRule) -> bool:
        """Save or update a policy."""
        if not self.enabled:
            return False

        try:
            with self.get_connection() as conn:
                if not conn:
                    return False

                cursor = conn.cursor()

                # Serialize policy data
                policy_data = self._serialize_policy(policy)

                cursor.execute("""
                    INSERT INTO policies (
                        rule_id, name, description, policy_type, action,
                        enabled, priority, scope, policy_data, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (rule_id)
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        policy_type = EXCLUDED.policy_type,
                        action = EXCLUDED.action,
                        enabled = EXCLUDED.enabled,
                        priority = EXCLUDED.priority,
                        scope = EXCLUDED.scope,
                        policy_data = EXCLUDED.policy_data,
                        updated_at = EXCLUDED.updated_at,
                        version = policies.version + 1
                """, (
                    policy.rule_id,
                    policy.name,
                    policy.description,
                    policy.policy_type.value,
                    policy.action.value,
                    policy.enabled,
                    policy.priority,
                    policy.scope.value,
                    json.dumps(policy_data),
                    datetime.now()
                ))

                conn.commit()
                cursor.close()
                return True

        except Exception as e:
            print(f"⚠️  Failed to save policy: {e}")
            return False

    def get_policy(self, rule_id: str) -> Optional[PolicyRule]:
        """Get a policy by ID."""
        if not self.enabled:
            return None

        try:
            with self.get_connection() as conn:
                if not conn:
                    return None

                cursor = conn.cursor(cursor_factory=RealDictCursor)

                cursor.execute("""
                    SELECT * FROM policies WHERE rule_id = %s
                """, (rule_id,))

                row = cursor.fetchone()
                cursor.close()

                if row:
                    return self._deserialize_policy(row)

                return None

        except Exception as e:
            print(f"⚠️  Failed to get policy: {e}")
            return None

    def list_policies(self, policy_type: Optional[PolicyType] = None,
                     enabled_only: bool = True) -> List[PolicyRule]:
        """List policies."""
        if not self.enabled:
            return []

        try:
            with self.get_connection() as conn:
                if not conn:
                    return []

                cursor = conn.cursor(cursor_factory=RealDictCursor)

                query = "SELECT * FROM policies WHERE 1=1"
                params = []

                if policy_type:
                    query += " AND policy_type = %s"
                    params.append(policy_type.value)

                if enabled_only:
                    query += " AND enabled = TRUE"

                query += " ORDER BY priority DESC, rule_id"

                cursor.execute(query, params)
                rows = cursor.fetchall()
                cursor.close()

                return [self._deserialize_policy(row) for row in rows]

        except Exception as e:
            print(f"⚠️  Failed to list policies: {e}")
            return []

    def delete_policy(self, rule_id: str) -> bool:
        """Delete a policy."""
        if not self.enabled:
            return False

        try:
            with self.get_connection() as conn:
                if not conn:
                    return False

                cursor = conn.cursor()

                cursor.execute("""
                    DELETE FROM policies WHERE rule_id = %s
                """, (rule_id,))

                conn.commit()
                cursor.close()
                return True

        except Exception as e:
            print(f"⚠️  Failed to delete policy: {e}")
            return False

    def record_violation(self, violation: PolicyViolationRecord) -> bool:
        """Record a policy violation."""
        if not self.enabled:
            return False

        try:
            with self.get_connection() as conn:
                if not conn:
                    return False

                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO policy_violations (
                        violation_id, rule_id, policy_type, action_taken,
                        violation_details, user_id, session_id, timestamp, metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    violation.violation_id,
                    violation.rule_id,
                    violation.policy_type.value,
                    violation.action_taken.value,
                    violation.violation_details,
                    violation.user_id,
                    violation.session_id,
                    violation.timestamp,
                    json.dumps(violation.metadata)
                ))

                conn.commit()
                cursor.close()
                return True

        except Exception as e:
            print(f"⚠️  Failed to record violation: {e}")
            return False

    def get_violations(self, session_id: Optional[str] = None,
                      user_id: Optional[str] = None,
                      limit: int = 100) -> List[PolicyViolationRecord]:
        """Get policy violations."""
        if not self.enabled:
            return []

        try:
            with self.get_connection() as conn:
                if not conn:
                    return []

                cursor = conn.cursor(cursor_factory=RealDictCursor)

                query = "SELECT * FROM policy_violations WHERE 1=1"
                params = []

                if session_id:
                    query += " AND session_id = %s"
                    params.append(session_id)

                if user_id:
                    query += " AND user_id = %s"
                    params.append(user_id)

                query += " ORDER BY timestamp DESC LIMIT %s"
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()
                cursor.close()

                return [self._deserialize_violation(row) for row in rows]

        except Exception as e:
            print(f"⚠️  Failed to get violations: {e}")
            return []

    def _serialize_policy(self, policy: PolicyRule) -> Dict[str, Any]:
        """Serialize policy to JSON-compatible dict."""
        data = {
            'rule_id': policy.rule_id,
            'name': policy.name,
            'description': policy.description,
            'policy_type': policy.policy_type.value,
            'action': policy.action.value,
            'enabled': policy.enabled,
            'priority': policy.priority,
            'scope': policy.scope.value,
            'metadata': policy.metadata
        }

        # Add type-specific fields
        if isinstance(policy, ToolPolicy):
            data.update({
                'allowed_tools': list(policy.allowed_tools),
                'blocked_tools': list(policy.blocked_tools),
                'max_executions_per_session': policy.max_executions_per_session,
                'max_executions_per_tool': policy.max_executions_per_tool,
                'require_approval_for_tools': list(policy.require_approval_for_tools)
            })
        elif isinstance(policy, RateLimitPolicy):
            data.update({
                'max_requests_per_minute': policy.max_requests_per_minute,
                'max_requests_per_hour': policy.max_requests_per_hour,
                'max_requests_per_day': policy.max_requests_per_day,
                'max_tokens_per_minute': policy.max_tokens_per_minute,
                'max_tokens_per_hour': policy.max_tokens_per_hour,
                'max_tokens_per_day': policy.max_tokens_per_day,
                'cooldown_period_seconds': policy.cooldown_period_seconds
            })
        elif isinstance(policy, ContentPolicy):
            data.update({
                'blocked_keywords': list(policy.blocked_keywords),
                'blocked_patterns': policy.blocked_patterns,
                'max_input_length': policy.max_input_length,
                'max_output_length': policy.max_output_length,
                'allow_code_execution': policy.allow_code_execution,
                'allow_file_access': policy.allow_file_access,
                'allow_network_access': policy.allow_network_access,
                'pii_detection_enabled': policy.pii_detection_enabled,
                'profanity_filter_enabled': policy.profanity_filter_enabled
            })
        elif isinstance(policy, CostPolicy):
            data.update({
                'max_cost_per_request': policy.max_cost_per_request,
                'max_cost_per_session': policy.max_cost_per_session,
                'max_cost_per_day': policy.max_cost_per_day,
                'max_cost_per_user': policy.max_cost_per_user,
                'cost_alert_threshold': policy.cost_alert_threshold,
                'token_cost_per_1k': policy.token_cost_per_1k
            })
        elif isinstance(policy, AccessPolicy):
            data.update({
                'allowed_users': list(policy.allowed_users),
                'blocked_users': list(policy.blocked_users),
                'allowed_roles': list(policy.allowed_roles),
                'required_permissions': list(policy.required_permissions)
            })

        return data

    def _deserialize_policy(self, row: Dict[str, Any]) -> PolicyRule:
        """Deserialize policy from database row."""
        policy_type = PolicyType(row['policy_type'])
        action = PolicyAction(row['action'])
        scope = PolicyScope(row['scope'])
        policy_data = row['policy_data']

        # Create base args
        base_args = {
            'rule_id': row['rule_id'],
            'name': row['name'],
            'description': row['description'],
            'policy_type': policy_type,
            'action': action,
            'enabled': row['enabled'],
            'priority': row['priority'],
            'scope': scope,
            'metadata': row.get('metadata', {})
        }

        # Create type-specific policy
        if policy_type == PolicyType.TOOL_USAGE:
            return ToolPolicy(
                **base_args,
                allowed_tools=set(policy_data.get('allowed_tools', [])),
                blocked_tools=set(policy_data.get('blocked_tools', [])),
                max_executions_per_session=policy_data.get('max_executions_per_session'),
                max_executions_per_tool=policy_data.get('max_executions_per_tool', {}),
                require_approval_for_tools=set(policy_data.get('require_approval_for_tools', []))
            )
        elif policy_type == PolicyType.RATE_LIMIT:
            return RateLimitPolicy(
                **base_args,
                max_requests_per_minute=policy_data.get('max_requests_per_minute'),
                max_requests_per_hour=policy_data.get('max_requests_per_hour'),
                max_requests_per_day=policy_data.get('max_requests_per_day'),
                max_tokens_per_minute=policy_data.get('max_tokens_per_minute'),
                max_tokens_per_hour=policy_data.get('max_tokens_per_hour'),
                max_tokens_per_day=policy_data.get('max_tokens_per_day'),
                cooldown_period_seconds=policy_data.get('cooldown_period_seconds')
            )
        elif policy_type == PolicyType.CONTENT_FILTER:
            return ContentPolicy(
                **base_args,
                blocked_keywords=set(policy_data.get('blocked_keywords', [])),
                blocked_patterns=policy_data.get('blocked_patterns', []),
                max_input_length=policy_data.get('max_input_length'),
                max_output_length=policy_data.get('max_output_length'),
                allow_code_execution=policy_data.get('allow_code_execution', False),
                allow_file_access=policy_data.get('allow_file_access', False),
                allow_network_access=policy_data.get('allow_network_access', True),
                pii_detection_enabled=policy_data.get('pii_detection_enabled', False),
                profanity_filter_enabled=policy_data.get('profanity_filter_enabled', False)
            )
        elif policy_type == PolicyType.COST_LIMIT:
            return CostPolicy(
                **base_args,
                max_cost_per_request=policy_data.get('max_cost_per_request'),
                max_cost_per_session=policy_data.get('max_cost_per_session'),
                max_cost_per_day=policy_data.get('max_cost_per_day'),
                max_cost_per_user=policy_data.get('max_cost_per_user'),
                cost_alert_threshold=policy_data.get('cost_alert_threshold'),
                token_cost_per_1k=policy_data.get('token_cost_per_1k', 0.001)
            )
        elif policy_type == PolicyType.ACCESS_CONTROL:
            return AccessPolicy(
                **base_args,
                allowed_users=set(policy_data.get('allowed_users', [])),
                blocked_users=set(policy_data.get('blocked_users', [])),
                allowed_roles=set(policy_data.get('allowed_roles', [])),
                required_permissions=set(policy_data.get('required_permissions', []))
            )
        else:
            return PolicyRule(**base_args)

    def _deserialize_violation(self, row: Dict[str, Any]) -> PolicyViolationRecord:
        """Deserialize violation from database row."""
        return PolicyViolationRecord(
            violation_id=row['violation_id'],
            rule_id=row['rule_id'],
            policy_type=PolicyType(row['policy_type']),
            action_taken=PolicyAction(row['action_taken']),
            violation_details=row['violation_details'],
            user_id=row['user_id'],
            session_id=row['session_id'],
            timestamp=row['timestamp'],
            metadata=row.get('metadata', {})
        )

    def is_available(self) -> bool:
        """Check if policy store is available."""
        return self.enabled and self.pool is not None

    def close(self):
        """Close connection pool."""
        if self.pool:
            self.pool.closeall()


# Global policy store instance
_policy_store = None


def get_policy_store() -> PolicyStore:
    """Get the global policy store instance."""
    global _policy_store

    if _policy_store is None:
        try:
            _policy_store = PolicyStore()
        except Exception as e:
            print(f"⚠️  Could not initialize policy store: {e}")
            # Create disabled store
            _policy_store = PolicyStore.__new__(PolicyStore)
            _policy_store.enabled = False
            _policy_store.pool = None

    return _policy_store
