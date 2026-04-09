"""RefreshToken ORM model."""

import uuid

from sqlalchemy import func

from app.extensions import db


class RefreshToken(db.Model):
    __tablename__ = "refresh_token"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)
    token_hash = db.Column(db.String(255), index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=func.now())

    user = db.relationship("User", back_populates="refresh_tokens")
