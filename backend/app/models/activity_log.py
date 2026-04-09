"""ActivityLog ORM model."""

import uuid

from sqlalchemy import func

from app.extensions import db


class ActivityLog(db.Model):
    __tablename__ = "activity_log"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=True, index=True)
    endpoint = db.Column(db.String(255))
    http_method = db.Column(db.String(10))
    status_code = db.Column(db.Integer)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=func.now(), index=True)

    user = db.relationship("User", back_populates="activity_logs")
