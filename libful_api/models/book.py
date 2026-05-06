from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libful_api.core.database import Base

if TYPE_CHECKING:
    from libful_api.models.author import Author
    from libful_api.models.book_copy import BookCopy
    from libful_api.models.genre import Genre


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"), nullable=False)
    publish_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id"), nullable=False)
    isbn: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    author: Mapped["Author"] = relationship(back_populates="books")
    genre: Mapped["Genre"] = relationship(back_populates="books")
    copies: Mapped[list["BookCopy"]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
    )
