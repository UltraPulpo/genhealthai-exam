"""Admin routes blueprint."""

import math

from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.extensions import db
from app.repositories import ActivityLogRepository
from app.schemas.activity_log import ActivityLogQuerySchema, ActivityLogSchema
from app.services import ActivityService

admin_blp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")


def get_activity_service() -> ActivityService:
    return ActivityService(log_repo=ActivityLogRepository(db.session))


@admin_blp.route("/activity-logs")
class ActivityLogListView(MethodView):
    @jwt_required()
    @admin_blp.arguments(ActivityLogQuerySchema, location="query")
    @admin_blp.response(200)
    def get(self, query_args):
        page = query_args.pop("page", 1)
        per_page = query_args.pop("per_page", 20)
        svc = get_activity_service()
        items, total = svc.list_logs(page=page, per_page=per_page, filters=query_args)
        total_pages = math.ceil(total / per_page) if per_page else 1
        serialized = ActivityLogSchema(many=True).dump(items)
        return {
            "data": serialized,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
        }
