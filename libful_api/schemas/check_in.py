from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CheckInCreate(BaseModel):
    user_id: int = Field(ge=1)
    check_in_datetime: datetime | None = None


class CheckInListParams(BaseModel):
    user_id: int | None = Field(default=None, ge=1)
    limit: int | None = Field(default=None, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class CheckInRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    check_in_datetime: datetime


class UserAttendanceCount(BaseModel):
    user_id: int
    attendance_count: int
