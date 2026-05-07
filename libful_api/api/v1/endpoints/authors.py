from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from libful_api.api.deps import AuthorsCrudDep, require_permission
from libful_api.core.permissions import Permission
from libful_api.models.author import Author
from libful_api.schemas.author import (
    AuthorCreate,
    AuthorListParams,
    AuthorRead,
    AuthorUpdate,
)


crud_router = APIRouter(prefix="/authors", tags=["Authors / CRUD"])
router = APIRouter(prefix="/authors", tags=["Authors"])


@crud_router.post(
    "/",
    response_model=AuthorRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
def create_author(
    payload: AuthorCreate,
    authors_crud: AuthorsCrudDep,
) -> Author:
    author = authors_crud.create_author(full_name=payload.full_name)
    authors_crud.db_session.commit()
    authors_crud.db_session.refresh(author)
    return author


@crud_router.get(
    "/",
    response_model=list[AuthorRead],
    dependencies=[Depends(require_permission(Permission.READ_CATALOG))],
)
def list_authors(
    params: Annotated[AuthorListParams, Depends()],
    authors_crud: AuthorsCrudDep,
) -> list[Author]:
    return authors_crud.list_authors(limit=params.limit, offset=params.offset)


@crud_router.get(
    "/{author_id}",
    response_model=AuthorRead,
    dependencies=[Depends(require_permission(Permission.READ_CATALOG))],
)
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


@crud_router.patch(
    "/{author_id}",
    response_model=AuthorRead,
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
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


@crud_router.delete(
    "/{author_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
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
