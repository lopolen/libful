from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from libful_api.api.deps import AuthorsCrudDep
from libful_api.models.author import Author
from libful_api.schemas.author import (
    AuthorCreate,
    AuthorListParams,
    AuthorRead,
    AuthorUpdate,
)


router = APIRouter(prefix="/authors", tags=["authors"])


@router.post("", response_model=AuthorRead, status_code=status.HTTP_201_CREATED)
def create_author(
    payload: AuthorCreate,
    authors_crud: AuthorsCrudDep,
) -> Author:
    author = authors_crud.create_author(full_name=payload.full_name)
    authors_crud.db_session.commit()
    authors_crud.db_session.refresh(author)
    return author


@router.get("", response_model=list[AuthorRead])
def list_authors(
    params: Annotated[AuthorListParams, Depends()],
    authors_crud: AuthorsCrudDep,
) -> list[Author]:
    return authors_crud.list_authors(limit=params.limit, offset=params.offset)


@router.get("/{author_id}", response_model=AuthorRead)
def read_author(
    author_id: int,
    authors_crud: AuthorsCrudDep,
) -> Author:
    author = authors_crud.read_author(author_id=author_id)
    if author is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found",
        )
    return author


@router.patch("/{author_id}", response_model=AuthorRead)
def update_author(
    author_id: int,
    payload: AuthorUpdate,
    authors_crud: AuthorsCrudDep,
) -> Author:
    author = authors_crud.update_author(
        author_id=author_id,
        **payload.model_dump(exclude_unset=True),
    )
    if author is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found",
        )

    authors_crud.db_session.commit()
    authors_crud.db_session.refresh(author)
    return author


@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_author(
    author_id: int,
    authors_crud: AuthorsCrudDep,
) -> Response:
    deleted = authors_crud.delete_author(author_id=author_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found",
        )

    authors_crud.db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
