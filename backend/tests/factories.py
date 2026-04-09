"""Test object factories."""

import uuid
from datetime import date

from app.models import Document, Order, OrderStatus, User


class UserFactory:
    _counter = 0

    @classmethod
    def create(cls, session, **overrides):
        cls._counter += 1
        user = User(
            id=overrides.get("id", str(uuid.uuid4())),
            email=overrides.get("email", f"user{cls._counter}@test.com"),
            first_name=overrides.get("first_name", "Test"),
            last_name=overrides.get("last_name", f"User{cls._counter}"),
            password_hash="",
        )
        user.set_password(overrides.get("password", "Password1"))
        session.add(user)
        session.commit()
        return user


class OrderFactory:
    @classmethod
    def create(cls, session, **overrides):
        order = Order(
            id=overrides.get("id", str(uuid.uuid4())),
            created_by=overrides["created_by"],
            status=overrides.get("status", OrderStatus.PENDING.value),
            patient_first_name=overrides.get("patient_first_name", "John"),
            patient_last_name=overrides.get("patient_last_name", "Doe"),
            patient_dob=overrides.get("patient_dob", date(1990, 1, 15)),
            insurance_provider=overrides.get("insurance_provider", "Medicare"),
            insurance_id=overrides.get("insurance_id", "INS123456"),
            equipment_type=overrides.get("equipment_type", "Wheelchair"),
        )
        for k, v in overrides.items():
            if hasattr(order, k) and k not in (
                "id",
                "created_by",
                "status",
                "patient_first_name",
                "patient_last_name",
                "patient_dob",
                "insurance_provider",
                "insurance_id",
                "equipment_type",
            ):
                setattr(order, k, v)
        session.add(order)
        session.commit()
        return order


class DocumentFactory:
    @classmethod
    def create(cls, session, **overrides):
        doc = Document(
            id=overrides.get("id", str(uuid.uuid4())),
            order_id=overrides["order_id"],
            original_filename=overrides.get("original_filename", "test.pdf"),
            stored_path=overrides.get("stored_path", "uploads/test.pdf"),
            file_size_bytes=overrides.get("file_size_bytes", 1024),
            content_type=overrides.get("content_type", "application/pdf"),
        )
        session.add(doc)
        session.commit()
        return doc
