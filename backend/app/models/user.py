"""User ORM model."""

import uuid

import bcrypt
from sqlalchemy import func

from app.extensions import db


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

    orders = db.relationship("Order", back_populates="creator")
    activity_logs = db.relationship("ActivityLog", back_populates="user")
    refresh_tokens = db.relationship("RefreshToken", back_populates="user")

    def set_password(self, plain: str) -> None:
        """Hash *plain* with bcrypt (cost factor 12) and store."""
        hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12))
        self.password_hash = hashed.decode("utf-8")

    def check_password(self, plain: str) -> bool:
        """Return ``True`` if *plain* matches the stored hash."""
        return bcrypt.checkpw(plain.encode("utf-8"), self.password_hash.encode("utf-8"))
