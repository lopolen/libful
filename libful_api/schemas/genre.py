from pydantic import BaseModel, ConfigDict, Field


class GenreCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class GenreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)


class GenreListParams(BaseModel):
    limit: int | None = Field(default=None, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class GenreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
