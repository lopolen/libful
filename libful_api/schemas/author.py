from pydantic import BaseModel, ConfigDict, Field


class AuthorCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)


class AuthorUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=100)


class AuthorListParams(BaseModel):
    limit: int | None = Field(default=None, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class AuthorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
