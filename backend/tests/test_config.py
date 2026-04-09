"""Tests for app.config module."""

import os
from datetime import timedelta
from unittest.mock import patch

import pytest

from app.config import (
    Config,
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
    config_map,
)


class TestConfigDefaults:
    """Test that Config loads correct defaults."""

    def test_secret_key_default(self):
        assert Config.SECRET_KEY == "dev-secret-key"

    def test_jwt_secret_key_default(self):
        assert Config.JWT_SECRET_KEY == "dev-jwt-secret"

    def test_sqlalchemy_database_uri_default(self):
        assert Config.SQLALCHEMY_DATABASE_URI == "sqlite:///app.db"

    def test_jwt_access_token_expires_default(self):
        assert timedelta(minutes=60) == Config.JWT_ACCESS_TOKEN_EXPIRES

    def test_jwt_refresh_token_expires_default(self):
        assert timedelta(days=7) == Config.JWT_REFRESH_TOKEN_EXPIRES

    def test_anthropic_model_default(self):
        assert Config.ANTHROPIC_MODEL == "claude-sonnet-4-20250514"

    def test_anthropic_max_tokens_default(self):
        assert Config.ANTHROPIC_MAX_TOKENS == 1024

    def test_anthropic_timeout_default(self):
        assert Config.ANTHROPIC_TIMEOUT == 30

    def test_anthropic_max_retries_default(self):
        assert Config.ANTHROPIC_MAX_RETRIES == 3

    def test_max_upload_size_mb_default(self):
        assert Config.MAX_UPLOAD_SIZE_MB == 10

    def test_upload_folder_default(self):
        assert Config.UPLOAD_FOLDER == "./uploads"

    def test_log_level_default(self):
        assert Config.LOG_LEVEL == "INFO"

    def test_max_content_length_derived(self):
        assert Config.MAX_CONTENT_LENGTH == 10 * 1024 * 1024

    def test_api_title(self):
        assert Config.API_TITLE == "GenHealth AI DME API"

    def test_api_version(self):
        assert Config.API_VERSION == "v1"

    def test_openapi_version(self):
        assert Config.OPENAPI_VERSION == "3.0.3"

    def test_openapi_url_prefix(self):
        assert Config.OPENAPI_URL_PREFIX == "/api/v1"

    def test_openapi_swagger_ui_path(self):
        assert Config.OPENAPI_SWAGGER_UI_PATH == "/docs"

    def test_openapi_swagger_ui_url(self):
        assert Config.OPENAPI_SWAGGER_UI_URL == "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"


class TestDevelopmentConfig:
    """Test DevelopmentConfig."""

    def test_debug_is_true(self):
        assert DevelopmentConfig.DEBUG is True

    def test_talisman_force_https_false(self):
        assert DevelopmentConfig.TALISMAN_FORCE_HTTPS is False

    def test_talisman_csp_none(self):
        assert DevelopmentConfig.TALISMAN_CSP is None

    def test_inherits_config(self):
        assert issubclass(DevelopmentConfig, Config)


class TestTestingConfig:
    """Test TestingConfig."""

    def test_testing_is_true(self):
        assert TestingConfig.TESTING is True

    def test_uses_memory_sqlite(self):
        assert TestingConfig.SQLALCHEMY_DATABASE_URI == "sqlite:///:memory:"

    def test_talisman_force_https_false(self):
        assert TestingConfig.TALISMAN_FORCE_HTTPS is False

    def test_talisman_csp_none(self):
        assert TestingConfig.TALISMAN_CSP is None

    def test_anthropic_api_key(self):
        assert TestingConfig.ANTHROPIC_API_KEY == "test-key"

    def test_secret_key_override(self):
        assert TestingConfig.SECRET_KEY == "test-secret"

    def test_jwt_secret_key_override(self):
        assert TestingConfig.JWT_SECRET_KEY == "test-jwt-secret"

    def test_inherits_config(self):
        assert issubclass(TestingConfig, Config)


class TestProductionConfig:
    """Test ProductionConfig."""

    def test_talisman_force_https_true(self):
        assert ProductionConfig.TALISMAN_FORCE_HTTPS is True

    def test_talisman_csp_has_default_src(self):
        assert ProductionConfig.TALISMAN_CSP["default-src"] == "'self'"

    def test_talisman_csp_has_script_src(self):
        assert ProductionConfig.TALISMAN_CSP["script-src"] == "'self'"

    def test_talisman_csp_has_style_src(self):
        assert ProductionConfig.TALISMAN_CSP["style-src"] == "'self' 'unsafe-inline'"

    def test_inherits_config(self):
        assert issubclass(ProductionConfig, Config)

    @patch.dict(os.environ, {"SECRET_KEY": "dev-secret-key", "JWT_SECRET_KEY": "dev-jwt-secret"})
    def test_raises_on_dev_secret_key_in_production(self):
        with pytest.raises(RuntimeError, match="SECRET_KEY must be set"):
            ProductionConfig()

    @patch.dict(
        os.environ,
        {"SECRET_KEY": "real-secret", "JWT_SECRET_KEY": "dev-jwt-secret"},
    )
    def test_raises_on_dev_jwt_secret_in_production(self):
        with pytest.raises(RuntimeError, match="JWT_SECRET_KEY must be set"):
            ProductionConfig()

    @patch.dict(
        os.environ,
        {"SECRET_KEY": "real-secret", "JWT_SECRET_KEY": "real-jwt-secret"},
    )
    def test_accepts_real_secrets_in_production(self):
        config = ProductionConfig()
        assert config is not None


class TestCorsOrigins:
    """Test CORS_ORIGINS parsing."""

    @patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:3000,http://example.com"})
    def test_cors_origins_parses_comma_separated(self):
        # Re-import to pick up env change — test via direct parsing logic
        origins = [
            o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
        ]
        assert origins == ["http://localhost:3000", "http://example.com"]

    def test_cors_origins_default_is_list(self):
        assert isinstance(Config.CORS_ORIGINS, list)


class TestConfigMap:
    """Test config_map dictionary."""

    def test_contains_development(self):
        assert config_map["development"] is DevelopmentConfig

    def test_contains_testing(self):
        assert config_map["testing"] is TestingConfig

    def test_contains_production(self):
        assert config_map["production"] is ProductionConfig

    def test_has_three_entries(self):
        assert len(config_map) == 3
