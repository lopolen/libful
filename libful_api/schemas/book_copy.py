from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from libful_api.core.book_copy_statuses import BookCopyStatus


class BookCopyCreate(BaseModel):
    book_id: int = Field(ge=1)
    inventory_number: str = Field(min_length=1, max_length=50)
    status: BookCopyStatus


class BookCopyUpdate(BaseModel):
    book_id: int | None = Field(default=None, ge=1)
    inventory_number: str | None = Field(default=None, min_length=1, max_length=50)
    status: BookCopyStatus | None = None


class BookCopyListParams(BaseModel):
    book_id: int | None = Field(default=None, ge=1)
    status: BookCopyStatus | None = None
    limit: int | None = Field(default=None, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class BookCopyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    inventory_number: str
    status: str
    created_at: datetime
