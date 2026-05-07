from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, status

from libful_api.api.deps import BookRentsCrudDep
from libful_api.core.exceptions import (
    BookCopyUnavailable,
    BookRentAlreadyReturned,
    InvalidBookRentReturnStatus,
    RelatedResourceNotFound,
)
from libful_api.models.book_rent import BookRent
from libful_api.schemas.book_rent import (
    BookRentHistoryParams,
    BookRentIssue,
    BookRentRead,
    BookRentReturn,
)


router = APIRouter(prefix="/book-rents", tags=["Book rents"])


def raise_book_rent_http_exception(
    exc: (
        RelatedResourceNotFound
        | BookCopyUnavailable
        | BookRentAlreadyReturned
        | InvalidBookRentReturnStatus
    ),
) -> NoReturn:
    if isinstance(exc, RelatedResourceNotFound):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    if isinstance(exc, InvalidBookRentReturnStatus):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=str(exc),
    ) from exc


@router.get("/history", response_model=list[BookRentRead])
def list_book_rent_history(
    params: Annotated[BookRentHistoryParams, Depends()],
    book_rents_crud: BookRentsCrudDep,
) -> list[BookRent]:
    return book_rents_crud.list_history(
        book_id=params.book_id,
        book_copy_id=params.book_copy_id,
        user_id=params.user_id,
        rented_from=params.rented_from,
        rented_to=params.rented_to,
        limit=params.limit,
        offset=params.offset,
    )


@router.post("/issue", response_model=BookRentRead, status_code=status.HTTP_201_CREATED)
def issue_book(
    payload: BookRentIssue,
    book_rents_crud: BookRentsCrudDep,
) -> BookRent:
    try:
        rent = book_rents_crud.issue_book(**payload.model_dump())
        book_rents_crud.db_session.commit()
        book_rents_crud.db_session.refresh(rent)
        return rent
    except (RelatedResourceNotFound, BookCopyUnavailable) as exc:
        book_rents_crud.db_session.rollback()
        raise_book_rent_http_exception(exc)


@router.post("/{book_rent_id}/return", response_model=BookRentRead)
def return_book(
    book_rent_id: int,
    payload: BookRentReturn,
    book_rents_crud: BookRentsCrudDep,
) -> BookRent:
    try:
        rent = book_rents_crud.return_book(
            book_rent_id=book_rent_id,
            **payload.model_dump(),
        )
        if rent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book rent not found",
            )

        book_rents_crud.db_session.commit()
        book_rents_crud.db_session.refresh(rent)
        return rent
    except HTTPException:
        book_rents_crud.db_session.rollback()
        raise
    except (
        BookRentAlreadyReturned,
        InvalidBookRentReturnStatus,
        RelatedResourceNotFound,
    ) as exc:
        book_rents_crud.db_session.rollback()
        raise_book_rent_http_exception(exc)
