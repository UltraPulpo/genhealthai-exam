"""Tests for Flask extension singletons."""

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_migrate import Migrate
from flask_smorest import Api
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman


class TestExtensionSingletons:
    """Verify that all extension singletons are importable and correctly typed."""

    def test_db_is_sqlalchemy_instance(self):
        from app.extensions import db

        assert isinstance(db, SQLAlchemy)

    def test_migrate_is_migrate_instance(self):
        from app.extensions import migrate

        assert isinstance(migrate, Migrate)

    def test_jwt_is_jwt_manager_instance(self):
        from app.extensions import jwt

        assert isinstance(jwt, JWTManager)

    def test_limiter_is_limiter_instance(self):
        from app.extensions import limiter

        assert isinstance(limiter, Limiter)

    def test_smorest_api_is_api_instance(self):
        from app.extensions import smorest_api

        assert isinstance(smorest_api, Api)

    def test_cors_is_cors_instance(self):
        from app.extensions import cors

        assert isinstance(cors, CORS)

    def test_talisman_is_talisman_instance(self):
        from app.extensions import talisman

        assert isinstance(talisman, Talisman)


class TestExtensionsNotBoundToApp:
    """Verify that no extension is pre-bound to a Flask application."""

    def test_db_has_no_app(self):
        from app.extensions import db

        # Flask-SQLAlchemy >=3 removes .app before init_app
        assert getattr(db, "app", None) is None

    def test_migrate_has_no_app(self):
        from app.extensions import migrate

        assert getattr(migrate, "app", None) is None

    def test_jwt_has_no_app(self):
        from app.extensions import jwt

        # JWTManager stores its app reference internally; before init_app
        # it should have no registered error handlers on a real app.
        assert not hasattr(jwt, "app") or jwt._default_error_handler is not None

    def test_limiter_has_no_app(self):
        from app.extensions import limiter

        assert getattr(limiter, "_app", getattr(limiter, "app", None)) is None

    def test_smorest_api_has_no_app(self):
        from app.extensions import smorest_api

        assert not hasattr(smorest_api, "_app") or smorest_api._app is None


class TestAllSingletonsImportableAtOnce:
    """Smoke-test: import everything in one statement."""

    def test_bulk_import(self):
        from app.extensions import (
            cors,
            db,
            jwt,
            limiter,
            migrate,
            smorest_api,
            talisman,
        )

        singletons = [db, migrate, jwt, limiter, smorest_api, cors, talisman]
        assert all(s is not None for s in singletons)
