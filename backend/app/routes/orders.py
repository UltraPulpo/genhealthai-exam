"""Orders routes blueprint."""

import math

from flask import request
from flask.views import MethodView
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from app.extensions import db, limiter
from app.repositories import DocumentRepository, OrderRepository
from app.schemas.order import (
    OrderCreateSchema,
    OrderQuerySchema,
    OrderResponseSchema,
    OrderUpdateSchema,
)
from app.services import ExtractionService, OrderService
from app.utils.errors import BusinessValidationError

orders_blp = Blueprint("orders", __name__, url_prefix="/api/v1/orders")

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def get_order_service() -> OrderService:
    return OrderService(
        order_repo=OrderRepository(db.session),
        doc_repo=DocumentRepository(db.session),
    )


def get_extraction_service() -> ExtractionService:
    return ExtractionService(
        order_repo=OrderRepository(db.session),
        doc_repo=DocumentRepository(db.session),
    )


@orders_blp.route("/")
class OrderListView(MethodView):
    @jwt_required()
    @orders_blp.arguments(OrderQuerySchema, location="query")
    @orders_blp.response(200)
    def get(self, query_args):
        page = query_args.pop("page", 1)
        per_page = query_args.pop("per_page", 20)
        svc = get_order_service()
        items, total = svc.list_orders(page=page, per_page=per_page, filters=query_args)
        total_pages = math.ceil(total / per_page) if per_page else 1
        serialized = OrderResponseSchema(many=True).dump(items)
        return {
            "data": serialized,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
        }

    @jwt_required()
    @orders_blp.arguments(OrderCreateSchema)
    @orders_blp.response(201, OrderResponseSchema)
    def post(self, args):
        user_id = get_jwt_identity()
        svc = get_order_service()
        return svc.create_order(user_id=user_id, data=args)


@orders_blp.route("/<order_id>")
class OrderDetailView(MethodView):
    @jwt_required()
    @orders_blp.response(200, OrderResponseSchema)
    def get(self, order_id):
        svc = get_order_service()
        return svc.get_order(order_id)

    @jwt_required()
    @orders_blp.arguments(OrderUpdateSchema)
    @orders_blp.response(200, OrderResponseSchema)
    def put(self, args, order_id):
        svc = get_order_service()
        return svc.update_order(order_id, args)

    @jwt_required()
    @orders_blp.response(204)
    def delete(self, order_id):
        svc = get_order_service()
        svc.delete_order(order_id)


@orders_blp.route("/<order_id>/upload")
class OrderUploadView(MethodView):
    @jwt_required()
    @limiter.limit("5/minute")
    @orders_blp.response(200, OrderResponseSchema)
    def post(self, order_id):
        file = request.files.get("file")
        if file is None:
            raise BusinessValidationError(
                "No file provided",
                details=[{"field": "file", "message": "File is required"}],
            )

        # Validate file type (MIME + extension)
        if file.content_type != "application/pdf" or not (
            file.filename and file.filename.lower().endswith(".pdf")
        ):
            raise BusinessValidationError(
                "Invalid file type",
                details=[{"field": "file", "message": "Only PDF files are accepted"}],
            )

        # Validate file size
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > MAX_UPLOAD_BYTES:
            raise BusinessValidationError(
                "File too large",
                details=[{"field": "file", "message": "File must be 10 MB or smaller"}],
            )

        svc = get_extraction_service()
        return svc.upload_and_extract(order_id, file)
