from typing import Literal


BookCopyStatus = Literal["available", "borrowed", "lost", "damaged"]
BookRentReturnStatus = Literal["available", "damaged", "lost"]

BOOK_COPY_STATUS_AVAILABLE: BookCopyStatus = "available"
BOOK_COPY_STATUS_BORROWED: BookCopyStatus = "borrowed"
BOOK_COPY_STATUS_LOST: BookCopyStatus = "lost"
BOOK_COPY_STATUS_DAMAGED: BookCopyStatus = "damaged"

ALLOWED_BOOK_COPY_STATUSES: tuple[BookCopyStatus, ...] = (
    BOOK_COPY_STATUS_AVAILABLE,
    BOOK_COPY_STATUS_BORROWED,
    BOOK_COPY_STATUS_LOST,
    BOOK_COPY_STATUS_DAMAGED,
)

ALLOWED_BOOK_RENT_RETURN_STATUSES: tuple[BookRentReturnStatus, ...] = (
    BOOK_COPY_STATUS_AVAILABLE,
    BOOK_COPY_STATUS_DAMAGED,
    BOOK_COPY_STATUS_LOST,
)


def is_allowed_book_copy_status(status: str) -> bool:
    return status in ALLOWED_BOOK_COPY_STATUSES


def is_allowed_book_rent_return_status(status: str) -> bool:
    return status in ALLOWED_BOOK_RENT_RETURN_STATUSES
