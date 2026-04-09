"""Order service."""

import os

from app.repositories import DocumentRepository, OrderRepository
from app.utils.errors import NotFoundError


class OrderService:
    def __init__(self, order_repo: OrderRepository, doc_repo: DocumentRepository):
        self.order_repo = order_repo
        self.doc_repo = doc_repo

    def create_order(self, user_id: str, data: dict):
        data = {**data, "status": "pending", "created_by": user_id}
        order = self.order_repo.create(data)
        self.order_repo.commit()
        return order

    def list_orders(self, page: int, per_page: int, filters: dict) -> tuple[list, int]:
        return self.order_repo.list_paginated(page, per_page, filters)

    def get_order(self, order_id: str):
        order = self.order_repo.get_with_document(order_id)
        if order is None:
            raise NotFoundError("Order not found")
        return order

    def update_order(self, order_id: str, data: dict):
        order = self.order_repo.get_by_id(order_id)
        if order is None:
            raise NotFoundError("Order not found")

        filtered_data = {
            k: v for k, v in data.items() if k not in ("id", "created_by", "created_at")
        }
        self.order_repo.update(order, filtered_data)
        self.order_repo.commit()
        return order

    def delete_order(self, order_id: str) -> None:
        order = self.order_repo.get_by_id(order_id)
        if order is None:
            raise NotFoundError("Order not found")

        doc = self.doc_repo.get_by_order_id(order_id)
        if doc is not None:
            try:
                os.remove(doc.stored_path)
            except (FileNotFoundError, OSError):
                pass
            self.doc_repo.delete(doc)

        self.order_repo.delete(order)
        self.order_repo.commit()
