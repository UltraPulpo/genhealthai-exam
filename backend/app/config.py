"""Flask configuration classes."""

import os
from datetime import timedelta
from typing import ClassVar

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration — loads all parameters from environment variables."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///app.db")

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    ANTHROPIC_MAX_TOKENS = int(os.environ.get("ANTHROPIC_MAX_TOKENS", "1024"))
    ANTHROPIC_TIMEOUT = int(os.environ.get("ANTHROPIC_TIMEOUT", "30"))
    ANTHROPIC_MAX_RETRIES = int(os.environ.get("ANTHROPIC_MAX_RETRIES", "3"))

    MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "10"))
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "./uploads")

    CORS_ORIGINS: ClassVar[list[str]] = [
        o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    ]

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # OpenAPI / flask-smorest settings
    API_TITLE = "GenHealth AI DME API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/api/v1"
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TALISMAN_FORCE_HTTPS = False
    TALISMAN_CSP = None


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TALISMAN_FORCE_HTTPS = False
    TALISMAN_CSP = None
    ANTHROPIC_API_KEY = "test-key"
    SECRET_KEY = "test-secret"  # noqa: S105
    JWT_SECRET_KEY = "test-jwt-secret"  # noqa: S105


class ProductionConfig(Config):
    """Production configuration."""

    # Azure App Service terminates TLS at the load balancer; the app sees HTTP.
    TALISMAN_FORCE_HTTPS = False
    TALISMAN_CSP: ClassVar[dict[str, str]] = {
        "default-src": "'self'",
        "script-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        "style-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        "img-src": "'self' data:",
        "font-src": "'self' data:",
    }


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
