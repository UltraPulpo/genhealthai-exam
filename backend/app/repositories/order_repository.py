"""Order repository."""

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.models.order import Order
from app.repositories.base_repository import BaseRepository


class OrderRepository(BaseRepository):
    model_class = Order

    def list_paginated(
        self, page: int, per_page: int, filters: dict | None = None
    ) -> tuple[list[Order], int]:
        """Return ``(items, total_count)`` with optional filters and sorting."""
        filters = filters or {}

        stmt = select(Order)
        count_stmt = select(func.count()).select_from(Order)

        # Apply filters
        if "status" in filters:
            stmt = stmt.where(Order.status == filters["status"])
            count_stmt = count_stmt.where(Order.status == filters["status"])

        if "patient_last_name" in filters:
            pattern = f"%{filters['patient_last_name']}%"
            stmt = stmt.where(Order.patient_last_name.ilike(pattern))
            count_stmt = count_stmt.where(Order.patient_last_name.ilike(pattern))

        if "created_after" in filters:
            stmt = stmt.where(Order.created_at >= filters["created_after"])
            count_stmt = count_stmt.where(Order.created_at >= filters["created_after"])

        if "created_before" in filters:
            stmt = stmt.where(Order.created_at <= filters["created_before"])
            count_stmt = count_stmt.where(Order.created_at <= filters["created_before"])

        # Sorting
        sort_by = filters.get("sort_by", "created_at")
        sort_order = filters.get("sort_order", "desc")

        col = Order.patient_last_name if sort_by == "patient_last_name" else Order.created_at

        stmt = stmt.order_by(col.asc() if sort_order == "asc" else col.desc())

        # Pagination
        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)

        items = self.session.execute(stmt).scalars().all()
        total = self.session.execute(count_stmt).scalar()
        return list(items), total

    def get_with_document(self, order_id: str) -> Order | None:
        """Eagerly load the related document."""
        stmt = select(Order).options(joinedload(Order.document)).where(Order.id == order_id)
        return self.session.execute(stmt).scalars().first()
