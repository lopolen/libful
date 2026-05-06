from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Response, status

from libful_api.api.deps import BooksCrudDep
from libful_api.core.exceptions import RelatedResourceNotFound, ResourceAlreadyExists
from libful_api.models.book import Book
from libful_api.schemas.book import (
    BookCopiesCount,
    BookCreate,
    BookListParams,
    BookRead,
    BookSearchParams,
    BookUpdate,
)


crud_router = APIRouter(prefix="/books", tags=["Books / CRUD"])
router = APIRouter(prefix="/books", tags=["Books"])


def raise_book_http_exception(
    exc: ResourceAlreadyExists | RelatedResourceNotFound,
) -> NoReturn:
    if isinstance(exc, ResourceAlreadyExists):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(exc),
    ) from exc


@router.get("/search", response_model=list[BookRead])
def search_books(
    params: Annotated[BookSearchParams, Depends()],
    books_crud: BooksCrudDep,
) -> list[Book]:
    return books_crud.search_books(
        title=params.title,
        author=params.author,
        isbn=params.isbn,
        limit=params.limit,
        offset=params.offset,
    )


@router.get("/{book_id}/copies/count", response_model=BookCopiesCount)
def count_book_copies(
    book_id: int,
    books_crud: BooksCrudDep,
) -> BookCopiesCount:
    copies_count = books_crud.count_book_copies(book_id=book_id)
    if copies_count is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    return BookCopiesCount(book_id=book_id, copies_count=copies_count)


@crud_router.post("/", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book(
    payload: BookCreate,
    books_crud: BooksCrudDep,
) -> Book:
    try:
        book = books_crud.create_book(**payload.model_dump())
        books_crud.db_session.commit()
        books_crud.db_session.refresh(book)
        return book
    except (ResourceAlreadyExists, RelatedResourceNotFound) as exc:
        books_crud.db_session.rollback()
        raise_book_http_exception(exc)


@crud_router.get("/", response_model=list[BookRead])
def list_books(
    params: Annotated[BookListParams, Depends()],
    books_crud: BooksCrudDep,
) -> list[Book]:
    return books_crud.list_books(limit=params.limit, offset=params.offset)


@crud_router.get("/{book_id}", response_model=BookRead)
def read_book(
    book_id: int,
    books_crud: BooksCrudDep,
) -> Book:
    book = books_crud.read_book(book_id=book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )
    return book


@crud_router.patch("/{book_id}", response_model=BookRead)
def update_book(
    book_id: int,
    payload: BookUpdate,
    books_crud: BooksCrudDep,
) -> Book:
    try:
        book = books_crud.update_book(
            book_id=book_id,
            **payload.model_dump(exclude_unset=True),
        )
        if book is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found",
            )

        books_crud.db_session.commit()
        books_crud.db_session.refresh(book)
        return book
    except HTTPException:
        books_crud.db_session.rollback()
        raise
    except (ResourceAlreadyExists, RelatedResourceNotFound) as exc:
        books_crud.db_session.rollback()
        raise_book_http_exception(exc)


@crud_router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    books_crud: BooksCrudDep,
) -> Response:
    deleted = books_crud.delete_book(book_id=book_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    books_crud.db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
