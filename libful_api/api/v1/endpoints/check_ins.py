from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from libful_api.api.deps import CheckInsCrudDep
from libful_api.models.check_in_history import CheckInHistory
from libful_api.schemas.check_in import (
    CheckInCreate,
    CheckInListParams,
    CheckInRead,
    UserAttendanceCount,
)


crud_router = APIRouter(prefix="/check-ins", tags=["Check-ins / CRUD"])
router = APIRouter(prefix="/check-ins", tags=["Check-ins"])


@crud_router.post("/", response_model=CheckInRead, status_code=status.HTTP_201_CREATED)
def create_check_in(
    payload: CheckInCreate,
    check_ins_crud: CheckInsCrudDep,
) -> CheckInHistory:
    check_in = check_ins_crud.create_check_in(
        user_id=payload.user_id,
        check_in_datetime=payload.check_in_datetime,
    )
    if check_in is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    check_ins_crud.db_session.commit()
    check_ins_crud.db_session.refresh(check_in)
    return check_in


@crud_router.get("/", response_model=list[CheckInRead])
def list_check_ins(
    params: Annotated[CheckInListParams, Depends()],
    check_ins_crud: CheckInsCrudDep,
) -> list[CheckInHistory]:
    check_ins = check_ins_crud.list_check_ins(
        user_id=params.user_id,
        limit=params.limit,
        offset=params.offset,
    )
    if check_ins is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return check_ins


@router.get("/users/{user_id}/count", response_model=UserAttendanceCount)
def count_user_check_ins(
    user_id: int,
    check_ins_crud: CheckInsCrudDep,
) -> UserAttendanceCount:
    attendance_count = check_ins_crud.count_user_check_ins(user_id=user_id)
    if attendance_count is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserAttendanceCount(user_id=user_id, attendance_count=attendance_count)


@crud_router.delete("/{check_in_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_check_in(
    check_in_id: int,
    check_ins_crud: CheckInsCrudDep,
) -> Response:
    deleted = check_ins_crud.delete_check_in(check_in_id=check_in_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check-in record not found",
        )

    check_ins_crud.db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
