"""System / health-check routes blueprint."""

from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy import text

from app.extensions import db

system_blp = Blueprint("system", __name__, url_prefix="/api/v1")


@system_blp.route("/health")
class HealthView(MethodView):
    def get(self):
        try:
            db.session.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "connected"}
        except Exception:
            return jsonify({"status": "unhealthy"}), 503
