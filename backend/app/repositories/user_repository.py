"""User repository."""

from sqlalchemy import func, select

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    model_class = User

    def get_by_email(self, email: str) -> User | None:
        """Case-insensitive email lookup."""
        stmt = select(User).where(func.lower(User.email) == email.lower())
        return self.session.execute(stmt).scalars().first()

    def email_exists(self, email: str) -> bool:
        """Optimized existence check."""
        stmt = select(select(User).where(func.lower(User.email) == email.lower()).exists())
        return self.session.execute(stmt).scalar()
