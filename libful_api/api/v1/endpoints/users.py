from typing import Annotated, Any, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from libful_api.api.deps import (
    OptionalCurrentUserDep,
    UsersCrudDep,
    raise_authentication_error,
    require_permission,
    require_user_permission,
)
from libful_api.core.exceptions import (
    InvalidEmail,
    LastAdminRoleError,
    PasswordRequiredForRole,
    UserAlreadyExists,
)
from libful_api.core.permissions import Permission, RoleName
from libful_api.models.user import User
from libful_api.models.role import Role
from libful_api.schemas.role import RoleRead
from libful_api.schemas.user import (
    UserCreate,
    UserListParams,
    UserRead,
    UserSearchParams,
    UserUpdate,
)


crud_router = APIRouter(prefix="/users", tags=["Users / CRUD"])
router = APIRouter(prefix="/users", tags=["Users"])


def dump_payload(payload: BaseModel, *, exclude_unset: bool = False) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(exclude_unset=exclude_unset)
    return payload.dict(exclude_unset=exclude_unset)


def raise_user_http_exception(
    exc: UserAlreadyExists | InvalidEmail | PasswordRequiredForRole,
) -> NoReturn:
    if isinstance(exc, UserAlreadyExists):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    if isinstance(exc, PasswordRequiredForRole):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Invalid email address",
    ) from exc


def raise_last_admin_http_exception(exc: LastAdminRoleError) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=str(exc),
    ) from exc


@crud_router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    users_crud: UsersCrudDep,
    current_user: OptionalCurrentUserDep,
) -> User:
    is_bootstrap_user = not users_crud.has_admin_user()
    role_names = list(payload.roles)

    if is_bootstrap_user:
        if RoleName.ADMIN not in role_names:
            role_names.append(RoleName.ADMIN)
    else:
        if current_user is None:
            raise_authentication_error()
        require_user_permission(current_user, Permission.MANAGE_USERS)

    data = dump_payload(payload)
    data.pop("roles", None)

    try:
        user = users_crud.create_user(**data, role_names=role_names)
        users_crud.db_session.commit()
        users_crud.db_session.refresh(user)
        return user
    except (UserAlreadyExists, InvalidEmail, PasswordRequiredForRole) as exc:
        users_crud.db_session.rollback()
        raise_user_http_exception(exc)


@crud_router.get(
    "/",
    response_model=list[UserRead],
    dependencies=[Depends(require_permission(Permission.READ_USERS))],
)
def list_users(
    params: Annotated[UserListParams, Depends()],
    users_crud: UsersCrudDep,
) -> list[User]:
    return users_crud.list_users(limit=params.limit, offset=params.offset)


@router.get(
    "/search",
    response_model=list[UserRead],
    dependencies=[Depends(require_permission(Permission.READ_USERS))],
)
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


@crud_router.get(
    "/{username}",
    response_model=UserRead,
    dependencies=[Depends(require_permission(Permission.READ_USERS))],
)
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


@crud_router.patch(
    "/{username}",
    response_model=UserRead,
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
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
    except (UserAlreadyExists, InvalidEmail, PasswordRequiredForRole) as exc:
        users_crud.db_session.rollback()
        raise_user_http_exception(exc)


@crud_router.delete(
    "/{username}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
def delete_user(
    username: str,
    users_crud: UsersCrudDep,
) -> Response:
    try:
        deleted = users_crud.delete_user(username=username)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
    except LastAdminRoleError as exc:
        users_crud.db_session.rollback()
        raise_last_admin_http_exception(exc)

    users_crud.db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{username}/roles",
    response_model=list[RoleRead],
    dependencies=[Depends(require_permission(Permission.READ_USERS))],
)
def list_user_roles(
    username: str,
    users_crud: UsersCrudDep,
) -> list[Role]:
    roles = users_crud.list_user_roles(username=username)
    if roles is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return roles


@router.put(
    "/{username}/roles/{role_name}",
    response_model=UserRead,
    dependencies=[Depends(require_permission(Permission.MANAGE_ROLES))],
)
def assign_user_role(
    username: str,
    role_name: RoleName,
    users_crud: UsersCrudDep,
) -> User:
    try:
        user = users_crud.assign_role_to_user(username=username, role_name=role_name)
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
    except PasswordRequiredForRole as exc:
        users_crud.db_session.rollback()
        raise_user_http_exception(exc)


@router.delete(
    "/{username}/roles/{role_name}",
    response_model=UserRead,
    dependencies=[Depends(require_permission(Permission.MANAGE_ROLES))],
)
def remove_user_role(
    username: str,
    role_name: RoleName,
    users_crud: UsersCrudDep,
) -> User:
    try:
        user = users_crud.remove_role_from_user(username=username, role_name=role_name)
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
    except LastAdminRoleError as exc:
        users_crud.db_session.rollback()
        raise_last_admin_http_exception(exc)
