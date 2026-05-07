from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from libful_api.core.database import get_db
from libful_api.core.exceptions import PasswordResetRequired
from libful_api.core.permissions import Permission, permissions_for_roles
from libful_api.core.security import verify_password
from libful_api.models.user import User
from libful_api.services.authors_crud import AuthorsCrud
from libful_api.services.book_copies_crud import BookCopiesCrud
from libful_api.services.book_rents_crud import BookRentsCrud
from libful_api.services.books_crud import BooksCrud
from libful_api.services.check_ins_crud import CheckInsCrud
from libful_api.services.genres_crud import GenresCrud
from libful_api.services.roles_crud import RolesCrud
from libful_api.services.users_crud import UsersCrud


basic_auth = HTTPBasic(auto_error=False)


def get_users_crud(db: Annotated[Session, Depends(get_db)]) -> UsersCrud:
    return UsersCrud(db)


def get_roles_crud(db: Annotated[Session, Depends(get_db)]) -> RolesCrud:
    return RolesCrud(db)


def get_check_ins_crud(db: Annotated[Session, Depends(get_db)]) -> CheckInsCrud:
    return CheckInsCrud(db)


def get_authors_crud(db: Annotated[Session, Depends(get_db)]) -> AuthorsCrud:
    return AuthorsCrud(db)


def get_genres_crud(db: Annotated[Session, Depends(get_db)]) -> GenresCrud:
    return GenresCrud(db)


def get_books_crud(db: Annotated[Session, Depends(get_db)]) -> BooksCrud:
    return BooksCrud(db)


def get_book_copies_crud(db: Annotated[Session, Depends(get_db)]) -> BookCopiesCrud:
    return BookCopiesCrud(db)


def get_book_rents_crud(db: Annotated[Session, Depends(get_db)]) -> BookRentsCrud:
    return BookRentsCrud(db)


def raise_authentication_error(detail: str = "Invalid authentication credentials") -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Basic"},
    )


def get_optional_current_user(
    credentials: Annotated[HTTPBasicCredentials | None, Depends(basic_auth)],
    users_crud: Annotated[UsersCrud, Depends(get_users_crud)],
) -> User | None:
    if credentials is None:
        return None

    user = users_crud.read_user(username=credentials.username)
    if user is None or user.password_hash is None:
        raise_authentication_error()

    try:
        is_valid_password = verify_password(credentials.password, user.password_hash)
    except PasswordResetRequired:
        raise_authentication_error("Password reset required")

    if not is_valid_password:
        raise_authentication_error()

    return user


def get_current_user(
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> User:
    if current_user is None:
        raise_authentication_error()

    return current_user


def require_user_permission(user: User, permission: Permission) -> None:
    role_names = {role.name for role in user.roles}
    if permission not in permissions_for_roles(role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )


def require_permission(permission: Permission):
    def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        require_user_permission(current_user, permission)
        return current_user

    return dependency


UsersCrudDep = Annotated[UsersCrud, Depends(get_users_crud)]
RolesCrudDep = Annotated[RolesCrud, Depends(get_roles_crud)]
CheckInsCrudDep = Annotated[CheckInsCrud, Depends(get_check_ins_crud)]
AuthorsCrudDep = Annotated[AuthorsCrud, Depends(get_authors_crud)]
GenresCrudDep = Annotated[GenresCrud, Depends(get_genres_crud)]
BooksCrudDep = Annotated[BooksCrud, Depends(get_books_crud)]
BookCopiesCrudDep = Annotated[BookCopiesCrud, Depends(get_book_copies_crud)]
BookRentsCrudDep = Annotated[BookRentsCrud, Depends(get_book_rents_crud)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
OptionalCurrentUserDep = Annotated[User | None, Depends(get_optional_current_user)]
