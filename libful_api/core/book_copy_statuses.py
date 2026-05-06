from typing import Literal


BookCopyStatus = Literal["available", "borrowed", "lost", "damaged"]

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


def is_allowed_book_copy_status(status: str) -> bool:
    return status in ALLOWED_BOOK_COPY_STATUSES
