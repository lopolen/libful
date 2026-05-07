from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from libful_api.core.book_copy_statuses import (
    BOOK_COPY_STATUS_AVAILABLE,
    BOOK_COPY_STATUS_BORROWED,
    is_allowed_book_rent_return_status,
)
from libful_api.core.exceptions import (
    BookCopyUnavailable,
    BookRentAlreadyReturned,
    InvalidBookRentReturnStatus,
    RelatedResourceNotFound,
)
from libful_api.models.book_copy import BookCopy
from libful_api.models.book_rent import BookRent
from libful_api.models.user import User


class BookRentsCrud:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def issue_book(
        self,
        *,
        book_copy_id: int,
        user_id: int,
        due_at: datetime | None = None,
        notes: str | None = None,
    ) -> BookRent:
        book_copy = self._get_book_copy(book_copy_id=book_copy_id)
        self._ensure_user_exists(user_id=user_id)

        if book_copy.status != BOOK_COPY_STATUS_AVAILABLE:
            raise BookCopyUnavailable("Book copy is not available for rent")
        if self._active_rent_exists(book_copy_id=book_copy_id):
            raise BookCopyUnavailable("Book copy already has an active rent")

        rent = BookRent(
            book_copy_id=book_copy_id,
            user_id=user_id,
            due_at=due_at,
            notes=notes,
        )
        book_copy.status = BOOK_COPY_STATUS_BORROWED
        self.db_session.add(rent)
        self.db_session.flush()
        return rent

    def return_book(
        self,
        *,
        book_rent_id: int,
        return_status: str,
        returned_at: datetime | None = None,
        notes: str | None = None,
    ) -> BookRent | None:
        rent = self.db_session.get(BookRent, book_rent_id)
        if rent is None:
            return None

        if rent.returned_at is not None:
            raise BookRentAlreadyReturned("Book rent is already returned")
        if not is_allowed_book_rent_return_status(return_status):
            raise InvalidBookRentReturnStatus(
                "Book rent return status must be one of: available, damaged, lost"
            )

        rent.returned_at = returned_at or datetime.now(timezone.utc)
        rent.return_status = return_status
        if notes is not None:
            rent.notes = notes

        rent.book_copy.status = return_status
        self.db_session.flush()
        return rent

    def list_history(
        self,
        *,
        book_id: int | None = None,
        book_copy_id: int | None = None,
        user_id: int | None = None,
        rented_from: datetime | None = None,
        rented_to: datetime | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[BookRent]:
        query = select(BookRent).join(BookRent.book_copy)

        if book_id is not None:
            query = query.where(BookCopy.book_id == book_id)
        if book_copy_id is not None:
            query = query.where(BookRent.book_copy_id == book_copy_id)
        if user_id is not None:
            query = query.where(BookRent.user_id == user_id)
        if rented_from is not None:
            query = query.where(BookRent.rented_at >= rented_from)
        if rented_to is not None:
            query = query.where(BookRent.rented_at <= rented_to)

        query = query.order_by(BookRent.rented_at.desc(), BookRent.id.desc()).offset(
            offset
        )
        if limit is not None:
            query = query.limit(limit)

        return list(self.db_session.scalars(query).all())

    def _get_book_copy(self, *, book_copy_id: int) -> BookCopy:
        book_copy = self.db_session.get(BookCopy, book_copy_id)
        if book_copy is None:
            raise RelatedResourceNotFound("Book copy not found")
        return book_copy

    def _ensure_user_exists(self, *, user_id: int) -> None:
        if self.db_session.get(User, user_id) is None:
            raise RelatedResourceNotFound("User not found")

    def _active_rent_exists(self, *, book_copy_id: int) -> bool:
        return self.db_session.scalar(
            select(BookRent.id).where(
                BookRent.book_copy_id == book_copy_id,
                BookRent.returned_at.is_(None),
            )
        ) is not None
