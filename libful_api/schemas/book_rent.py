from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from libful_api.core.book_rent_fines import BookRentFineType
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


class BookRentDeadlineUpdate(BaseModel):
    due_at: datetime


class BookRentHistoryParams(BaseModel):
    book_id: int | None = Field(default=None, ge=1)
    book_copy_id: int | None = Field(default=None, ge=1)
    user_id: int | None = Field(default=None, ge=1)
    rented_from: datetime | None = None
    rented_to: datetime | None = None
    limit: int | None = Field(default=None, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class BookRentOverdueParams(BaseModel):
    user_id: int | None = Field(default=None, ge=1)
    as_of: datetime | None = None
    limit: int | None = Field(default=None, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class BookRentFineListParams(BaseModel):
    book_rent_id: int | None = Field(default=None, ge=1)
    user_id: int | None = Field(default=None, ge=1)
    is_paid: bool | None = None
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


class BookRentFineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_rent_id: int
    user_id: int
    fine_type: str
    amount_uah: int
    days_overdue: int | None
    notes: str | None
    created_at: datetime
    paid_at: datetime | None


class BookRentFinePreview(BaseModel):
    fine_type: BookRentFineType
    amount_uah: int
    days_overdue: int | None = None
    notes: str | None = None
