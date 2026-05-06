from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    author_id: int = Field(ge=1)
    publish_year: int | None = Field(default=None, ge=0)
    genre_id: int = Field(ge=1)
    isbn: str | None = Field(default=None, min_length=1, max_length=20)


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    author_id: int | None = Field(default=None, ge=1)
    publish_year: int | None = Field(default=None, ge=0)
    genre_id: int | None = Field(default=None, ge=1)
    isbn: str | None = Field(default=None, min_length=1, max_length=20)


class BookListParams(BaseModel):
    limit: int | None = Field(default=None, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author_id: int
    publish_year: int | None
    genre_id: int
    isbn: str | None
    created_at: datetime
