from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libful_api.core.database import Base
from libful_api.models.users_roles import users_roles

if TYPE_CHECKING:
    from libful_api.models.book_rent import BookRent
    from libful_api.models.check_in_history import CheckInHistory
    from libful_api.models.role import Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)

    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    roles: Mapped[list["Role"]] = relationship(
        secondary=users_roles,
        back_populates="users",
    )
    check_in_history: Mapped[list["CheckInHistory"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    book_rents: Mapped[list["BookRent"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
