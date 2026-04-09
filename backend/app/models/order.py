"""Order ORM model and OrderStatus enum."""

import enum
import uuid

from sqlalchemy import func

from app.extensions import db


class OrderStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Order(db.Model):
    __tablename__ = "order"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_by = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(50), default=OrderStatus.PENDING.value)
    error_message = db.Column(db.Text, nullable=True)

    # Patient fields
    patient_first_name = db.Column(db.String(255), nullable=True)
    patient_last_name = db.Column(db.String(255), nullable=True)
    patient_dob = db.Column(db.Date, nullable=True)

    # Insurance fields
    insurance_provider = db.Column(db.String(255), nullable=True)
    insurance_id = db.Column(db.String(255), nullable=True)
    group_number = db.Column(db.String(255), nullable=True)

    # Provider fields
    ordering_provider_name = db.Column(db.String(255), nullable=True)
    provider_npi = db.Column(db.String(255), nullable=True)
    provider_phone = db.Column(db.String(255), nullable=True)

    # Equipment fields
    equipment_type = db.Column(db.String(255), nullable=True)
    equipment_description = db.Column(db.String(255), nullable=True)
    hcpcs_code = db.Column(db.String(255), nullable=True)

    # Authorization fields
    authorization_number = db.Column(db.String(255), nullable=True)
    authorization_status = db.Column(db.String(255), nullable=True)

    # Delivery fields
    delivery_address = db.Column(db.String(255), nullable=True)
    delivery_notes = db.Column(db.String(255), nullable=True)
    delivery_date = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

    document = db.relationship("Document", uselist=False, back_populates="order")
    creator = db.relationship("User", back_populates="orders")
