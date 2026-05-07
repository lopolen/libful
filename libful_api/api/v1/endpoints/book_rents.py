from datetime import datetime
from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, status

from libful_api.api.deps import BookRentsCrudDep
from libful_api.core.book_copy_statuses import BookRentReturnStatus
from libful_api.core.exceptions import (
    BookCopyUnavailable,
    BookRentAlreadyReturned,
    FineAlreadyPaid,
    InvalidBookRentReturnStatus,
    RelatedResourceNotFound,
)
from libful_api.models.book_rent_fine import BookRentFine
from libful_api.models.book_rent import BookRent
from libful_api.schemas.book_rent import (
    BookRentDeadlineUpdate,
    BookRentFineListParams,
    BookRentFinePreview,
    BookRentFineRead,
    BookRentHistoryParams,
    BookRentIssue,
    BookRentOverdueParams,
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
        | FineAlreadyPaid
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


@router.get("/overdue", response_model=list[BookRentRead])
def list_overdue_book_rents(
    params: Annotated[BookRentOverdueParams, Depends()],
    book_rents_crud: BookRentsCrudDep,
) -> list[BookRent]:
    return book_rents_crud.list_overdue(
        user_id=params.user_id,
        as_of=params.as_of,
        limit=params.limit,
        offset=params.offset,
    )


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


@router.get("/fines", response_model=list[BookRentFineRead])
def list_book_rent_fines(
    params: Annotated[BookRentFineListParams, Depends()],
    book_rents_crud: BookRentsCrudDep,
) -> list[BookRentFine]:
    return book_rents_crud.list_fines(
        book_rent_id=params.book_rent_id,
        user_id=params.user_id,
        is_paid=params.is_paid,
        limit=params.limit,
        offset=params.offset,
    )


@router.post("/fines/{fine_id}/pay", response_model=BookRentFineRead)
def pay_book_rent_fine(
    fine_id: int,
    book_rents_crud: BookRentsCrudDep,
) -> BookRentFine:
    try:
        fine = book_rents_crud.pay_fine(fine_id=fine_id)
        if fine is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fine not found",
            )

        book_rents_crud.db_session.commit()
        book_rents_crud.db_session.refresh(fine)
        return fine
    except HTTPException:
        book_rents_crud.db_session.rollback()
        raise
    except FineAlreadyPaid as exc:
        book_rents_crud.db_session.rollback()
        raise_book_rent_http_exception(exc)


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


@router.get("/{book_rent_id}/fines/preview", response_model=list[BookRentFinePreview])
def preview_book_rent_fines(
    book_rent_id: int,
    book_rents_crud: BookRentsCrudDep,
    as_of: datetime | None = None,
    return_status: BookRentReturnStatus | None = None,
) -> list[dict[str, int | str | None]]:
    try:
        return book_rents_crud.preview_fines(
            book_rent_id=book_rent_id,
            as_of=as_of,
            return_status=return_status,
        )
    except RelatedResourceNotFound as exc:
        raise_book_rent_http_exception(exc)


@router.patch("/{book_rent_id}/deadline", response_model=BookRentRead)
def update_book_rent_deadline(
    book_rent_id: int,
    payload: BookRentDeadlineUpdate,
    book_rents_crud: BookRentsCrudDep,
) -> BookRent:
    try:
        rent = book_rents_crud.update_deadline(
            book_rent_id=book_rent_id,
            due_at=payload.due_at,
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
    except BookRentAlreadyReturned as exc:
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
