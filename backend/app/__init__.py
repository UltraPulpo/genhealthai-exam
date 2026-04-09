"""GenHealth AI – Flask application factory."""

import os

from flask import Flask
from sqlalchemy import event

from app.config import config_map
from app.extensions import cors, db, jwt, limiter, migrate, smorest_api, talisman
from app.middleware import register_middleware
from app.routes import register_blueprints
from app.utils.errors import register_error_handlers


def create_app(config_name=None):
    """Create and configure the Flask application."""
    config_name = config_name or os.environ.get("APP_CONFIG", "production")

    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    # Validate required secrets in production
    if config_name == "production":
        required = ["SECRET_KEY", "JWT_SECRET_KEY", "ANTHROPIC_API_KEY"]
        missing = [k for k in required if not app.config.get(k)]
        if missing:
            raise RuntimeError(f"Missing required config: {', '.join(missing)}")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(app, origins=app.config.get("CORS_ORIGINS", []))
    smorest_api.init_app(app)
    talisman.init_app(
        app,
        force_https=app.config.get("TALISMAN_FORCE_HTTPS", True),
        content_security_policy=app.config.get("TALISMAN_CSP"),
    )

    register_error_handlers(app)
    register_middleware(app)
    register_blueprints(smorest_api)

    # Import models so SQLAlchemy metadata discovers them
    from app import models  # noqa: F401

    # SQLite WAL mode and foreign-key enforcement
    with app.app_context():

        @event.listens_for(db.engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    os.makedirs(app.config.get("UPLOAD_FOLDER", "./uploads"), exist_ok=True)

    return app
