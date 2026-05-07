from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libful_api.core.database import Base

if TYPE_CHECKING:
    from libful_api.models.book_copy import BookCopy
    from libful_api.models.user import User


class BookRent(Base):
    __tablename__ = "book_rents"
    __table_args__ = (
        CheckConstraint(
            "return_status IS NULL OR return_status IN "
            "('available', 'damaged', 'lost')",
            name="ck_book_rents_return_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    book_copy_id: Mapped[int] = mapped_column(
        ForeignKey("book_copies.id"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    rented_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    returned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    return_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    book_copy: Mapped["BookCopy"] = relationship(back_populates="rents")
    user: Mapped["User"] = relationship(back_populates="book_rents")
