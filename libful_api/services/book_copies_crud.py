from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from libful_api.core.book_copy_statuses import is_allowed_book_copy_status
from libful_api.core.exceptions import (
    InvalidBookCopyStatus,
    RelatedResourceNotFound,
    ResourceAlreadyExists,
)
from libful_api.models.book import Book
from libful_api.models.book_copy import BookCopy


class BookCopiesCrud:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def create_book_copy(
        self,
        *,
        book_id: int,
        inventory_number: str,
        status: str,
    ) -> BookCopy:
        self._ensure_book_exists(book_id=book_id)
        self._ensure_status_is_allowed(status=status)
        self._ensure_inventory_number_is_available(
            inventory_number=inventory_number,
        )

        book_copy = BookCopy(
            book_id=book_id,
            inventory_number=inventory_number,
            status=status,
        )
        self.db_session.add(book_copy)
        self._flush_unique()
        return book_copy

    def read_book_copy(self, *, book_copy_id: int) -> BookCopy | None:
        return self.db_session.get(BookCopy, book_copy_id)

    def list_book_copies(
        self,
        *,
        book_id: int | None = None,
        status: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[BookCopy]:
        if book_id is not None:
            self._ensure_book_exists(book_id=book_id)
        if status is not None:
            self._ensure_status_is_allowed(status=status)

        query = select(BookCopy).order_by(BookCopy.id).offset(offset)
        if book_id is not None:
            query = query.where(BookCopy.book_id == book_id)
        if status is not None:
            query = query.where(BookCopy.status == status)
        if limit is not None:
            query = query.limit(limit)

        return list(self.db_session.scalars(query).all())

    def update_book_copy(
        self,
        *,
        book_copy_id: int,
        book_id: int | None = None,
        inventory_number: str | None = None,
        status: str | None = None,
    ) -> BookCopy | None:
        book_copy = self.read_book_copy(book_copy_id=book_copy_id)
        if book_copy is None:
            return None

        if book_id is not None:
            self._ensure_book_exists(book_id=book_id)
            book_copy.book_id = book_id
        if inventory_number is not None:
            self._ensure_inventory_number_is_available(
                inventory_number=inventory_number,
                exclude_book_copy_id=book_copy.id,
            )
            book_copy.inventory_number = inventory_number
        if status is not None:
            self._ensure_status_is_allowed(status=status)
            book_copy.status = status

        self._flush_unique()
        return book_copy

    def delete_book_copy(self, *, book_copy_id: int) -> bool:
        book_copy = self.read_book_copy(book_copy_id=book_copy_id)
        if book_copy is None:
            return False

        self.db_session.delete(book_copy)
        self.db_session.flush()
        return True

    def _ensure_book_exists(self, *, book_id: int) -> None:
        if self.db_session.get(Book, book_id) is None:
            raise RelatedResourceNotFound("Book not found")

    def _ensure_status_is_allowed(self, *, status: str) -> None:
        if not is_allowed_book_copy_status(status):
            raise InvalidBookCopyStatus(
                "Book copy status must be one of: available, borrowed, lost, damaged"
            )

    def _ensure_inventory_number_is_available(
        self,
        *,
        inventory_number: str,
        exclude_book_copy_id: int | None = None,
    ) -> None:
        query = select(BookCopy.id).where(
            BookCopy.inventory_number == inventory_number
        )
        if exclude_book_copy_id is not None:
            query = query.where(BookCopy.id != exclude_book_copy_id)

        if self.db_session.scalar(query) is not None:
            raise ResourceAlreadyExists(
                "Book copy with this inventory number already exists"
            )

    def _flush_unique(self) -> None:
        try:
            self.db_session.flush()
        except IntegrityError:
            self.db_session.rollback()
            raise ResourceAlreadyExists(
                "Book copy with this inventory number already exists"
            )
