"""GenHealth AI – Flask application factory."""

import os

from flask import Flask, send_from_directory
from sqlalchemy import event

from app.config import config_map
from app.extensions import cors, db, jwt, limiter, migrate, smorest_api, talisman
from app.middleware import register_middleware
from app.routes import register_blueprints
from app.utils.errors import register_error_handlers


def create_app(config_name=None):
    """Create and configure the Flask application."""
    config_name = config_name or os.environ.get("APP_CONFIG", "production")

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app = Flask(__name__, static_folder=static_dir, static_url_path="")
    app.url_map.strict_slashes = False
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

    # SPA catch-all: serve React index.html for non-API routes
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path):
        if path and os.path.exists(os.path.join(static_dir, path)):
            return send_from_directory(static_dir, path)
        index = os.path.join(static_dir, "index.html")
        if os.path.exists(index):
            return send_from_directory(static_dir, "index.html")
        return {"message": "GenHealth AI API", "docs": "/api/v1/docs"}, 200

    return app
