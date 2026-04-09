"""Refresh-token repository."""

from datetime import datetime, timezone

from sqlalchemy import delete, select

from app.models.refresh_token import RefreshToken
from app.repositories.base_repository import BaseRepository

_utcnow = lambda: datetime.now(timezone.utc).replace(tzinfo=None)  # noqa: E731


class RefreshTokenRepository(BaseRepository):
    model_class = RefreshToken

    def create_token(self, user_id: str, token_hash: str, expires_at: datetime):
        """Create and return a new refresh token."""
        return self.create(
            {
                "user_id": user_id,
                "token_hash": token_hash,
                "expires_at": expires_at,
            }
        )

    def find_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Return a non-expired token matching *token_hash*, or None."""
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.expires_at > _utcnow(),
        )
        return self.session.execute(stmt).scalars().first()

    def delete_by_hash(self, token_hash: str) -> None:
        """Delete a token by its hash."""
        stmt = delete(RefreshToken).where(RefreshToken.token_hash == token_hash)
        self.session.execute(stmt)

    def delete_all_for_user(self, user_id: str) -> None:
        """Delete all refresh tokens for a user."""
        stmt = delete(RefreshToken).where(RefreshToken.user_id == user_id)
        self.session.execute(stmt)

    def delete_expired(self) -> int:
        """Delete expired tokens and return count deleted."""
        stmt = delete(RefreshToken).where(RefreshToken.expires_at <= _utcnow())
        result = self.session.execute(stmt)
        return result.rowcount
