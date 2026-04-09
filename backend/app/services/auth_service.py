"""Authentication service."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from flask_jwt_extended import create_access_token

from app.repositories import RefreshTokenRepository, UserRepository
from app.utils.errors import (
    AuthenticationError,
    BusinessValidationError,
    ConflictError,
    NotFoundError,
)


def _utcnow() -> datetime:
    """Return current UTC time as a timezone-naive datetime (SQLite-compatible)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuthService:
    def __init__(self, user_repo: UserRepository, token_repo: RefreshTokenRepository):
        self.user_repo = user_repo
        self.token_repo = token_repo

    def register(self, email: str, password: str, first_name: str, last_name: str):
        if self.user_repo.email_exists(email):
            raise ConflictError("Email already registered")

        if (
            len(password) < 8
            or not any(c.isupper() for c in password)
            or not any(c.islower() for c in password)
            or not any(c.isdigit() for c in password)
        ):
            raise BusinessValidationError(
                "Password validation failed",
                details=[
                    {
                        "field": "password",
                        "message": "Password must be at least 8 characters and contain uppercase, lowercase, and a digit",
                    }
                ],
            )

        user = self.user_repo.create(
            {"email": email, "first_name": first_name, "last_name": last_name, "password_hash": ""}
        )
        user.set_password(password)
        self.user_repo.commit()
        return user

    def login(self, email: str, password: str) -> tuple[str, str]:
        user = self.user_repo.get_by_email(email)
        if user is None:
            raise AuthenticationError("Invalid credentials")

        if not user.check_password(password):
            raise AuthenticationError("Invalid credentials")

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"email": user.email},
        )

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = _utcnow() + timedelta(days=7)

        self.token_repo.create_token(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.token_repo.commit()

        return (access_token, raw_token)

    def refresh(self, raw_refresh_token: str) -> tuple[str, str]:
        token_hash = hashlib.sha256(raw_refresh_token.encode()).hexdigest()

        token = self.token_repo.find_by_hash(token_hash)
        if token is None:
            raise AuthenticationError("Invalid or expired refresh token")

        user = self.user_repo.get_by_id(token.user_id)
        if user is None:
            raise AuthenticationError("Invalid or expired refresh token")

        self.token_repo.delete_by_hash(token_hash)

        new_access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"email": user.email},
        )

        new_raw_token = secrets.token_urlsafe(32)
        new_token_hash = hashlib.sha256(new_raw_token.encode()).hexdigest()
        expires_at = _utcnow() + timedelta(days=7)

        self.token_repo.create_token(
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=expires_at,
        )
        self.token_repo.commit()

        return (new_access_token, new_raw_token)

    def logout(self, user_id: str) -> None:
        self.token_repo.delete_all_for_user(user_id)
        self.token_repo.commit()

    def get_current_user(self, user_id: str):
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user
