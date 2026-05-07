from datetime import datetime, timezone
from math import ceil

from sqlalchemy import select
from sqlalchemy.orm import Session

from libful_api.core.book_rent_fines import (
    BOOK_RENT_FINE_TYPE_DAMAGE,
    BOOK_RENT_FINE_TYPE_OVERDUE,
    DAMAGE_FINE_UAH,
    OVERDUE_FINE_PER_DAY_UAH,
)
from libful_api.core.book_copy_statuses import (
    BOOK_COPY_STATUS_AVAILABLE,
    BOOK_COPY_STATUS_BORROWED,
    BOOK_COPY_STATUS_DAMAGED,
    is_allowed_book_rent_return_status,
)
from libful_api.core.exceptions import (
    BookCopyUnavailable,
    BookRentAlreadyReturned,
    FineAlreadyPaid,
    InvalidBookRentReturnStatus,
    RelatedResourceNotFound,
)
from libful_api.models.book_copy import BookCopy
from libful_api.models.book_rent import BookRent
from libful_api.models.book_rent_fine import BookRentFine
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
        self._sync_return_fines(rent=rent)
        self.db_session.flush()
        return rent

    def update_deadline(
        self,
        *,
        book_rent_id: int,
        due_at: datetime,
    ) -> BookRent | None:
        rent = self.db_session.get(BookRent, book_rent_id)
        if rent is None:
            return None
        if rent.returned_at is not None:
            raise BookRentAlreadyReturned("Cannot update deadline for returned rent")

        rent.due_at = due_at
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

    def list_overdue(
        self,
        *,
        user_id: int | None = None,
        as_of: datetime | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[BookRent]:
        check_time = as_of or datetime.now(timezone.utc)

        query = select(BookRent).where(
            BookRent.returned_at.is_(None),
            BookRent.due_at.is_not(None),
            BookRent.due_at < check_time,
        )
        if user_id is not None:
            query = query.where(BookRent.user_id == user_id)

        query = query.order_by(BookRent.due_at, BookRent.id).offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return list(self.db_session.scalars(query).all())

    def preview_fines(
        self,
        *,
        book_rent_id: int,
        as_of: datetime | None = None,
        return_status: str | None = None,
    ) -> list[dict[str, int | str | None]]:
        rent = self.db_session.get(BookRent, book_rent_id)
        if rent is None:
            raise RelatedResourceNotFound("Book rent not found")
        if return_status is not None and not is_allowed_book_rent_return_status(
            return_status
        ):
            raise InvalidBookRentReturnStatus(
                "Book rent return status must be one of: available, damaged, lost"
            )

        check_time = as_of or rent.returned_at or datetime.now(timezone.utc)
        status = return_status if return_status is not None else rent.return_status
        return self._calculate_fines(
            rent=rent,
            check_time=check_time,
            return_status=status,
        )

    def list_fines(
        self,
        *,
        book_rent_id: int | None = None,
        user_id: int | None = None,
        is_paid: bool | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[BookRentFine]:
        query = select(BookRentFine).order_by(
            BookRentFine.created_at.desc(),
            BookRentFine.id.desc(),
        ).offset(offset)

        if book_rent_id is not None:
            query = query.where(BookRentFine.book_rent_id == book_rent_id)
        if user_id is not None:
            query = query.where(BookRentFine.user_id == user_id)
        if is_paid is not None:
            if is_paid:
                query = query.where(BookRentFine.paid_at.is_not(None))
            else:
                query = query.where(BookRentFine.paid_at.is_(None))
        if limit is not None:
            query = query.limit(limit)

        return list(self.db_session.scalars(query).all())

    def pay_fine(
        self,
        *,
        fine_id: int,
        paid_at: datetime | None = None,
    ) -> BookRentFine | None:
        fine = self.db_session.get(BookRentFine, fine_id)
        if fine is None:
            return None
        if fine.paid_at is not None:
            raise FineAlreadyPaid("Fine is already paid")

        fine.paid_at = paid_at or datetime.now(timezone.utc)
        self.db_session.flush()
        return fine

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

    def _sync_return_fines(self, *, rent: BookRent) -> None:
        check_time = rent.returned_at or datetime.now(timezone.utc)
        fine_items = self._calculate_fines(
            rent=rent,
            check_time=check_time,
            return_status=rent.return_status,
        )

        for item in fine_items:
            existing_fine = self.db_session.scalar(
                select(BookRentFine).where(
                    BookRentFine.book_rent_id == rent.id,
                    BookRentFine.fine_type == item["fine_type"],
                )
            )
            if existing_fine is None:
                self.db_session.add(
                    BookRentFine(
                        book_rent_id=rent.id,
                        user_id=rent.user_id,
                        fine_type=item["fine_type"],
                        amount_uah=item["amount_uah"],
                        days_overdue=item["days_overdue"],
                        notes=item["notes"],
                    )
                )
            elif existing_fine.paid_at is None:
                existing_fine.amount_uah = item["amount_uah"]
                existing_fine.days_overdue = item["days_overdue"]
                existing_fine.notes = item["notes"]

    def _calculate_fines(
        self,
        *,
        rent: BookRent,
        check_time: datetime,
        return_status: str | None,
    ) -> list[dict[str, int | str | None]]:
        fines: list[dict[str, int | str | None]] = []
        days_overdue = self._calculate_days_overdue(
            due_at=rent.due_at,
            check_time=check_time,
        )

        if days_overdue > 0:
            fines.append(
                {
                    "fine_type": BOOK_RENT_FINE_TYPE_OVERDUE,
                    "amount_uah": days_overdue * OVERDUE_FINE_PER_DAY_UAH,
                    "days_overdue": days_overdue,
                    "notes": (
                        f"Overdue for {days_overdue} day(s), "
                        f"{OVERDUE_FINE_PER_DAY_UAH} UAH per day"
                    ),
                }
            )

        if return_status == BOOK_COPY_STATUS_DAMAGED:
            fines.append(
                {
                    "fine_type": BOOK_RENT_FINE_TYPE_DAMAGE,
                    "amount_uah": DAMAGE_FINE_UAH,
                    "days_overdue": None,
                    "notes": "Book copy returned damaged",
                }
            )

        return fines

    def _calculate_days_overdue(
        self,
        *,
        due_at: datetime | None,
        check_time: datetime,
    ) -> int:
        if due_at is None:
            return 0

        normalized_due_at = self._to_utc_naive(due_at)
        normalized_check_time = self._to_utc_naive(check_time)
        seconds_overdue = (normalized_check_time - normalized_due_at).total_seconds()
        if seconds_overdue <= 0:
            return 0

        return ceil(seconds_overdue / 86400)

    def _to_utc_naive(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)
