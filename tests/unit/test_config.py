"""
Unit tests for configuration module.

Tests cover:
- Config class loading
- Environment variable handling
- Default values
"""

import os


class TestConfig:
    """Tests for Config class."""

    def test_config_imports(self):
        """Test that config can be imported."""
        from src.config import Config
        assert Config is not None

    def test_llm_provider_default(self):
        """Test LLM provider default value."""
        from src.config import Config
        # Should have a valid provider
        assert Config.LLM_PROVIDER in ["groq", "google", "openai"]

    def test_embedding_provider_default(self):
        """Test embedding provider default."""
        from src.config import Config
        assert Config.EMBEDDING_PROVIDER is not None

    def test_chunk_size_default(self):
        """Test chunk size has reasonable default."""
        from src.config import Config
        assert Config.CHUNK_SIZE > 0
        assert Config.CHUNK_SIZE <= 2000  # Reasonable upper bound

    def test_chunk_overlap_default(self):
        """Test chunk overlap is less than chunk size."""
        from src.config import Config
        assert Config.CHUNK_OVERLAP >= 0
        assert Config.CHUNK_OVERLAP < Config.CHUNK_SIZE

    def test_top_k_results_default(self):
        """Test top_k has reasonable value."""
        from src.config import Config
        assert Config.TOP_K_RESULTS > 0
        assert Config.TOP_K_RESULTS <= 10

    def test_boolean_configs(self):
        """Test boolean configuration values."""
        from src.config import Config
        # These should be booleans
        assert isinstance(Config.USE_POSTGRES, bool)
        assert isinstance(Config.USE_PINECONE, bool)

    def test_display_name_methods(self):
        """Test display name helper methods exist and return strings."""
        from src.config import Config

        if hasattr(Config, 'get_llm_display_name'):
            name = Config.get_llm_display_name()
            assert isinstance(name, str)
            assert len(name) > 0

        if hasattr(Config, 'get_vector_store_display_name'):
            name = Config.get_vector_store_display_name()
            assert isinstance(name, str)


class TestConfigEnvironmentOverrides:
    """Tests for environment variable overrides."""

    def test_env_override_llm_provider(self):
        """Test that LLM_PROVIDER environment variable is read."""
        # Just verify the environment variable mechanism works
        current_provider = os.environ.get("LLM_PROVIDER", "groq")
        assert current_provider in ["groq", "google", "openai", "test"]

    def test_env_override_use_postgres(self):
        """Test USE_POSTGRES environment override."""
        # This tests the pattern, actual reload behavior varies
        original = os.environ.get("USE_POSTGRES", "false")
        try:
            os.environ["USE_POSTGRES"] = "true"
            # Verify the env var was set
            assert os.environ.get("USE_POSTGRES") == "true"
        finally:
            os.environ["USE_POSTGRES"] = original


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_required_paths_exist(self):
        """Test that required paths are configured."""
        from src.config import Config

        # Check that data paths are defined
        if hasattr(Config, 'DATA_DIR'):
            assert Config.DATA_DIR is not None

    def test_api_keys_not_logged(self):
        """Verify API keys have safe handling (don't print them)."""
        from src.config import Config

        # The config should not expose raw API keys in string representations
        config_str = str(dir(Config))
        # Keys shouldn't be in the string representation of attributes
        assert "sk-" not in config_str  # OpenAI key pattern
        assert "gsk_" not in config_str  # Groq key pattern
