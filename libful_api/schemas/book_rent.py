from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from libful_api.core.book_copy_statuses import BookRentReturnStatus


class BookRentIssue(BaseModel):
    book_copy_id: int = Field(ge=1)
    user_id: int = Field(ge=1)
    due_at: datetime | None = None
    notes: str | None = None


class BookRentReturn(BaseModel):
    return_status: BookRentReturnStatus
    returned_at: datetime | None = None
    notes: str | None = None


class BookRentHistoryParams(BaseModel):
    book_id: int | None = Field(default=None, ge=1)
    book_copy_id: int | None = Field(default=None, ge=1)
    user_id: int | None = Field(default=None, ge=1)
    rented_from: datetime | None = None
    rented_to: datetime | None = None
    limit: int | None = Field(default=None, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class BookRentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_copy_id: int
    user_id: int
    rented_at: datetime
    due_at: datetime | None
    returned_at: datetime | None
    return_status: str | None
    notes: str | None
