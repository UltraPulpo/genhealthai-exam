"""Document repository."""

from sqlalchemy import delete, select

from app.models.document import Document
from app.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository):
    model_class = Document

    def get_by_order_id(self, order_id: str) -> Document | None:
        """Return the document for *order_id*, or None."""
        stmt = select(Document).where(Document.order_id == order_id)
        return self.session.execute(stmt).scalars().first()

    def delete_by_order_id(self, order_id: str) -> None:
        """Delete all documents for an order."""
        stmt = delete(Document).where(Document.order_id == order_id)
        self.session.execute(stmt)
