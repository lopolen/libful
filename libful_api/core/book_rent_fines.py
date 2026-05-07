from typing import Literal


BookRentFineType = Literal["overdue", "damage"]

BOOK_RENT_FINE_TYPE_OVERDUE: BookRentFineType = "overdue"
BOOK_RENT_FINE_TYPE_DAMAGE: BookRentFineType = "damage"

ALLOWED_BOOK_RENT_FINE_TYPES: tuple[BookRentFineType, ...] = (
    BOOK_RENT_FINE_TYPE_OVERDUE,
    BOOK_RENT_FINE_TYPE_DAMAGE,
)

OVERDUE_FINE_PER_DAY_UAH = 5
DAMAGE_FINE_UAH = 100
