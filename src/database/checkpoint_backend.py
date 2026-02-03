"""
LangGraph Checkpoint Backend using PostgreSQL.

This module provides checkpoint storage for LangGraph agents,
enabling state persistence and crash recovery.
"""

import os
from typing import Optional
from contextlib import contextmanager

try:
    from langgraph.checkpoint.postgres import PostgresSaver
    CHECKPOINT_AVAILABLE = True
except ImportError:
    CHECKPOINT_AVAILABLE = False

try:
    import psycopg
    from psycopg.rows import dict_row
    PSYCOPG_AVAILABLE = True
except ImportError:
    PSYCOPG_AVAILABLE = False


class CheckpointManager:
    """
    Manager for LangGraph checkpoint storage in PostgreSQL.

    Provides:
    - Automatic checkpoint creation
    - State recovery after crashes
    - Thread-safe checkpoint operations
    - Connection pooling
    """

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize checkpoint manager.

        Args:
            connection_string: PostgreSQL connection string
        """
        if not CHECKPOINT_AVAILABLE:
            raise ImportError(
                "langgraph-checkpoint-postgres not installed. "
                "Run: pip install langgraph-checkpoint-postgres"
            )

        if not PSYCOPG_AVAILABLE:
            raise ImportError(
                "psycopg not installed. "
                "Run: pip install psycopg[binary]"
            )

        self.connection_string = connection_string or self._get_connection_string()
        self.enabled = self._check_enabled()
        self.checkpoint_saver = None

        if self.enabled:
            self._initialize_saver()

    def _get_connection_string(self) -> str:
        """Get PostgreSQL connection string from environment."""
        # Try full connection string first
        conn_str = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')

        if conn_str:
            # Convert postgresql:// to postgres:// if needed (psycopg format)
            if conn_str.startswith('postgresql://'):
                conn_str = conn_str.replace('postgresql://', 'postgres://', 1)
            return conn_str

        # Build from individual components
        user = os.getenv('POSTGRES_USER', 'postgres')
        password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        database = os.getenv('POSTGRES_DB', 'rag_chatbot')

        return f"postgres://{user}:{password}@{host}:{port}/{database}"

    def _check_enabled(self) -> bool:
        """Check if checkpointing is enabled."""
        use_postgres = os.getenv('USE_POSTGRES', 'false').lower() == 'true'
        use_checkpoints = os.getenv('USE_CHECKPOINTS', 'true').lower() == 'true'
        return use_postgres and use_checkpoints

    def _initialize_saver(self):
        """Initialize the PostgreSQL checkpoint saver."""
        try:
            # Create checkpoint saver with connection string
            self.checkpoint_saver = PostgresSaver.from_conn_string(
                self.connection_string
            )

            # Setup tables (creates checkpoint tables if they don't exist)
            self.checkpoint_saver.setup()

            print("✅ LangGraph checkpoint storage initialized")

        except Exception as e:
            print(f"⚠️  Failed to initialize checkpoint storage: {e}")
            print("📝 Checkpointing will be disabled")
            self.enabled = False
            self.checkpoint_saver = None

    def get_checkpointer(self):
        """
        Get the checkpoint saver instance.

        Returns:
            PostgresSaver instance or None if not available
        """
        return self.checkpoint_saver if self.enabled else None

    def is_available(self) -> bool:
        """Check if checkpoint storage is available."""
        return self.enabled and self.checkpoint_saver is not None

    @contextmanager
    def get_connection(self):
        """
        Get a database connection for checkpoint operations.

        Yields:
            psycopg connection
        """
        if not self.enabled:
            yield None
            return

        try:
            conn = psycopg.connect(
                self.connection_string,
                row_factory=dict_row
            )
            try:
                yield conn
            finally:
                conn.close()
        except Exception as e:
            print(f"Error getting checkpoint connection: {e}")
            yield None

    def list_checkpoints(self, thread_id: str, limit: int = 10):
        """
        List checkpoints for a thread.

        Args:
            thread_id: Thread/session identifier
            limit: Maximum number of checkpoints to return

        Returns:
            List of checkpoint metadata
        """
        if not self.is_available():
            return []

        try:
            with self.get_connection() as conn:
                if not conn:
                    return []

                cursor = conn.cursor()
                cursor.execute("""
                    SELECT thread_id, checkpoint_id, parent_checkpoint_id,
                           created_at, checkpoint_ns
                    FROM checkpoints
                    WHERE thread_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (thread_id, limit))

                return cursor.fetchall()

        except Exception as e:
            print(f"Error listing checkpoints: {e}")
            return []

    def get_checkpoint(self, thread_id: str, checkpoint_id: Optional[str] = None):
        """
        Get a specific checkpoint or the latest one.

        Args:
            thread_id: Thread/session identifier
            checkpoint_id: Specific checkpoint ID (optional, gets latest if not provided)

        Returns:
            Checkpoint data or None
        """
        if not self.is_available():
            return None

        try:
            # Use the checkpoint saver's get method
            config = {"configurable": {"thread_id": thread_id}}
            if checkpoint_id:
                config["configurable"]["checkpoint_id"] = checkpoint_id

            return self.checkpoint_saver.get(config)

        except Exception as e:
            print(f"Error getting checkpoint: {e}")
            return None

    def delete_thread_checkpoints(self, thread_id: str) -> bool:
        """
        Delete all checkpoints for a thread.

        Args:
            thread_id: Thread/session identifier

        Returns:
            True if successful
        """
        if not self.is_available():
            return False

        try:
            with self.get_connection() as conn:
                if not conn:
                    return False

                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM checkpoints WHERE thread_id = %s
                """, (thread_id,))
                conn.commit()
                return True

        except Exception as e:
            print(f"Error deleting checkpoints: {e}")
            return False

    def get_thread_history(self, thread_id: str):
        """
        Get the full execution history for a thread.

        Args:
            thread_id: Thread/session identifier

        Returns:
            List of checkpoints with states
        """
        if not self.is_available():
            return []

        try:
            checkpoints = self.list_checkpoints(thread_id, limit=100)
            history = []

            for cp in checkpoints:
                checkpoint_data = self.get_checkpoint(
                    thread_id,
                    cp['checkpoint_id']
                )
                if checkpoint_data:
                    history.append({
                        'checkpoint_id': cp['checkpoint_id'],
                        'created_at': cp['created_at'],
                        'state': checkpoint_data
                    })

            return history

        except Exception as e:
            print(f"Error getting thread history: {e}")
            return []

    def close(self):
        """Close checkpoint saver connections."""
        if self.checkpoint_saver:
            # PostgresSaver handles its own connection management
            pass


# Global checkpoint manager instance
_checkpoint_manager = None


def get_checkpoint_manager() -> CheckpointManager:
    """
    Get the global checkpoint manager instance.

    Returns:
        CheckpointManager instance
    """
    global _checkpoint_manager

    if _checkpoint_manager is None:
        try:
            _checkpoint_manager = CheckpointManager()
        except Exception as e:
            print(f"⚠️  Could not initialize checkpoint manager: {e}")
            # Create a disabled manager
            _checkpoint_manager = CheckpointManager.__new__(CheckpointManager)
            _checkpoint_manager.enabled = False
            _checkpoint_manager.checkpoint_saver = None

    return _checkpoint_manager
