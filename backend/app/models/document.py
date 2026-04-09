"""Document ORM model."""

import uuid

from sqlalchemy import func

from app.extensions import db


class Document(db.Model):
    __tablename__ = "document"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = db.Column(db.String(36), db.ForeignKey("order.id"), nullable=False)
    original_filename = db.Column(db.String(255))
    stored_path = db.Column(db.String(255))
    content_type = db.Column(db.String(255))
    file_size_bytes = db.Column(db.Integer)
    extracted_text = db.Column(db.Text)
    extracted_data = db.Column(db.JSON)
    uploaded_at = db.Column(db.DateTime, default=func.now())

    order = db.relationship("Order", back_populates="document")
