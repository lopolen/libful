from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Response, status

from libful_api.api.deps import BookCopiesCrudDep, require_permission
from libful_api.core.exceptions import (
    InvalidBookCopyStatus,
    RelatedResourceNotFound,
    ResourceAlreadyExists,
)
from libful_api.core.permissions import Permission
from libful_api.models.book_copy import BookCopy
from libful_api.schemas.book_copy import (
    BookCopyCreate,
    BookCopyListParams,
    BookCopyRead,
    BookCopyUpdate,
)


crud_router = APIRouter(prefix="/book-copies", tags=["Book copies / CRUD"])
router = APIRouter(prefix="/book-copies", tags=["Book copies"])


def raise_book_copy_http_exception(
    exc: ResourceAlreadyExists | RelatedResourceNotFound | InvalidBookCopyStatus,
) -> NoReturn:
    if isinstance(exc, ResourceAlreadyExists):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    if isinstance(exc, InvalidBookCopyStatus):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(exc),
    ) from exc


@crud_router.post(
    "/",
    response_model=BookCopyRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
def create_book_copy(
    payload: BookCopyCreate,
    book_copies_crud: BookCopiesCrudDep,
) -> BookCopy:
    try:
        book_copy = book_copies_crud.create_book_copy(**payload.model_dump())
        book_copies_crud.db_session.commit()
        book_copies_crud.db_session.refresh(book_copy)
        return book_copy
    except (ResourceAlreadyExists, RelatedResourceNotFound, InvalidBookCopyStatus) as exc:
        book_copies_crud.db_session.rollback()
        raise_book_copy_http_exception(exc)


@crud_router.get(
    "/",
    response_model=list[BookCopyRead],
    dependencies=[Depends(require_permission(Permission.READ_CATALOG))],
)
def list_book_copies(
    params: Annotated[BookCopyListParams, Depends()],
    book_copies_crud: BookCopiesCrudDep,
) -> list[BookCopy]:
    try:
        return book_copies_crud.list_book_copies(
            book_id=params.book_id,
            status=params.status,
            limit=params.limit,
            offset=params.offset,
        )
    except (RelatedResourceNotFound, InvalidBookCopyStatus) as exc:
        raise_book_copy_http_exception(exc)


@crud_router.get(
    "/{book_copy_id}",
    response_model=BookCopyRead,
    dependencies=[Depends(require_permission(Permission.READ_CATALOG))],
)
def read_book_copy(
    book_copy_id: int,
    book_copies_crud: BookCopiesCrudDep,
) -> BookCopy:
    book_copy = book_copies_crud.read_book_copy(book_copy_id=book_copy_id)
    if book_copy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book copy not found",
        )
    return book_copy


@crud_router.patch(
    "/{book_copy_id}",
    response_model=BookCopyRead,
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
def update_book_copy(
    book_copy_id: int,
    payload: BookCopyUpdate,
    book_copies_crud: BookCopiesCrudDep,
) -> BookCopy:
    try:
        book_copy = book_copies_crud.update_book_copy(
            book_copy_id=book_copy_id,
            **payload.model_dump(exclude_unset=True),
        )
        if book_copy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book copy not found",
            )

        book_copies_crud.db_session.commit()
        book_copies_crud.db_session.refresh(book_copy)
        return book_copy
    except HTTPException:
        book_copies_crud.db_session.rollback()
        raise
    except (ResourceAlreadyExists, RelatedResourceNotFound, InvalidBookCopyStatus) as exc:
        book_copies_crud.db_session.rollback()
        raise_book_copy_http_exception(exc)


@crud_router.delete(
    "/{book_copy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permission.MANAGE_CATALOG))],
)
def delete_book_copy(
    book_copy_id: int,
    book_copies_crud: BookCopiesCrudDep,
) -> Response:
    deleted = book_copies_crud.delete_book_copy(book_copy_id=book_copy_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book copy not found",
        )

    book_copies_crud.db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
