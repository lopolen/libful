from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libful_api.core.database import Base

if TYPE_CHECKING:
    from libful_api.models.book_rent import BookRent
    from libful_api.models.user import User


class BookRentFine(Base):
    __tablename__ = "book_rent_fines"
    __table_args__ = (
        CheckConstraint(
            "fine_type IN ('overdue', 'damage')",
            name="ck_book_rent_fines_fine_type",
        ),
        CheckConstraint("amount_uah >= 0", name="ck_book_rent_fines_amount_uah"),
        CheckConstraint(
            "days_overdue IS NULL OR days_overdue >= 0",
            name="ck_book_rent_fines_days_overdue",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    book_rent_id: Mapped[int] = mapped_column(
        ForeignKey("book_rents.id"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    fine_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount_uah: Mapped[int] = mapped_column(Integer, nullable=False)
    days_overdue: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    book_rent: Mapped["BookRent"] = relationship(back_populates="fines")
    user: Mapped["User"] = relationship(back_populates="book_rent_fines")
