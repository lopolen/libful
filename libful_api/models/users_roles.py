from sqlalchemy import Column, ForeignKey, Integer, Table

from libful_api.core.database import Base


users_roles = Table(
    "users_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)
