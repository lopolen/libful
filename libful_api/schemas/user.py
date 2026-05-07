from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from libful_api.core.permissions import RoleName
from libful_api.schemas.role import RoleRead


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    password: str | None = Field(default=None, min_length=1)
    roles: list[RoleName] = Field(default_factory=list)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=100)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    password: str | None = Field(default=None, min_length=1)


class UserSearchParams(BaseModel):
    id: int | None = Field(default=None, ge=1)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=1, max_length=30)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class UserListParams(BaseModel):
    limit: int | None = Field(default=None, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    created_at: datetime
    roles: list[RoleRead] = Field(default_factory=list)
