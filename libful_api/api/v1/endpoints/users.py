from typing import Annotated, Any, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from libful_api.api.deps import UsersCrudDep
from libful_api.core.exceptions import InvalidEmail, UserAlreadyExists
from libful_api.models.user import User
from libful_api.schemas.user import (
    UserCreate,
    UserListParams,
    UserRead,
    UserSearchParams,
    UserUpdate,
)


router = APIRouter(prefix="/users", tags=["users"])


def dump_payload(payload: BaseModel, *, exclude_unset: bool = False) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(exclude_unset=exclude_unset)
    return payload.dict(exclude_unset=exclude_unset)


def raise_user_http_exception(exc: UserAlreadyExists | InvalidEmail) -> NoReturn:
    if isinstance(exc, UserAlreadyExists):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Invalid email address",
    ) from exc


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    users_crud: UsersCrudDep,
) -> User:
    try:
        user = users_crud.create_user(**dump_payload(payload))
        users_crud.db_session.commit()
        users_crud.db_session.refresh(user)
        return user
    except (UserAlreadyExists, InvalidEmail) as exc:
        users_crud.db_session.rollback()
        raise_user_http_exception(exc)


@router.get("", response_model=list[UserRead])
def list_users(
    params: Annotated[UserListParams, Depends()],
    users_crud: UsersCrudDep,
) -> list[User]:
    return users_crud.list_users(limit=params.limit, offset=params.offset)


@router.get("/search", response_model=list[UserRead])
def search_users(
    filters: Annotated[UserSearchParams, Depends()],
    users_crud: UsersCrudDep,
) -> list[User]:
    return users_crud.search_users(
        user_id=filters.id,
        first_name=filters.first_name,
        last_name=filters.last_name,
        email=filters.email,
        phone=filters.phone,
        limit=filters.limit,
        offset=filters.offset,
    )


@router.get("/{username}", response_model=UserRead)
def read_user(
    username: str,
    users_crud: UsersCrudDep,
) -> User:
    user = users_crud.read_user(username=username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.patch("/{username}", response_model=UserRead)
def update_user(
    username: str,
    payload: UserUpdate,
    users_crud: UsersCrudDep,
) -> User:
    data = dump_payload(payload, exclude_unset=True)
    new_username = data.pop("username", None)

    try:
        user = users_crud.update_user(
            username=username,
            new_username=new_username,
            **data,
        )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        users_crud.db_session.commit()
        users_crud.db_session.refresh(user)
        return user
    except HTTPException:
        users_crud.db_session.rollback()
        raise
    except (UserAlreadyExists, InvalidEmail) as exc:
        users_crud.db_session.rollback()
        raise_user_http_exception(exc)


@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    username: str,
    users_crud: UsersCrudDep,
) -> Response:
    deleted = users_crud.delete_user(username=username)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    users_crud.db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
