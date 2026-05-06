from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from libful_api.api.deps import GenresCrudDep
from libful_api.models.genre import Genre
from libful_api.schemas.genre import (
    GenreCreate,
    GenreListParams,
    GenreRead,
    GenreUpdate,
)


crud_router = APIRouter(prefix="/genres", tags=["Genres / CRUD"])
router = APIRouter(prefix="/genres", tags=["Genres"])


@crud_router.post("/", response_model=GenreRead, status_code=status.HTTP_201_CREATED)
def create_genre(
    payload: GenreCreate,
    genres_crud: GenresCrudDep,
) -> Genre:
    genre = genres_crud.create_genre(name=payload.name)
    genres_crud.db_session.commit()
    genres_crud.db_session.refresh(genre)
    return genre


@crud_router.get("/", response_model=list[GenreRead])
def list_genres(
    params: Annotated[GenreListParams, Depends()],
    genres_crud: GenresCrudDep,
) -> list[Genre]:
    return genres_crud.list_genres(limit=params.limit, offset=params.offset)


@crud_router.get("/{genre_id}", response_model=GenreRead)
def read_genre(
    genre_id: int,
    genres_crud: GenresCrudDep,
) -> Genre:
    genre = genres_crud.read_genre(genre_id=genre_id)
    if genre is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Genre not found",
        )
    return genre


@crud_router.patch("/{genre_id}", response_model=GenreRead)
def update_genre(
    genre_id: int,
    payload: GenreUpdate,
    genres_crud: GenresCrudDep,
) -> Genre:
    genre = genres_crud.update_genre(
        genre_id=genre_id,
        **payload.model_dump(exclude_unset=True),
    )
    if genre is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Genre not found",
        )

    genres_crud.db_session.commit()
    genres_crud.db_session.refresh(genre)
    return genre


@crud_router.delete("/{genre_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_genre(
    genre_id: int,
    genres_crud: GenresCrudDep,
) -> Response:
    deleted = genres_crud.delete_genre(genre_id=genre_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Genre not found",
        )

    genres_crud.db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
