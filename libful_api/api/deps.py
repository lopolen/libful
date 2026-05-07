from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from libful_api.core.database import get_db
from libful_api.services.authors_crud import AuthorsCrud
from libful_api.services.book_copies_crud import BookCopiesCrud
from libful_api.services.book_rents_crud import BookRentsCrud
from libful_api.services.books_crud import BooksCrud
from libful_api.services.check_ins_crud import CheckInsCrud
from libful_api.services.genres_crud import GenresCrud
from libful_api.services.users_crud import UsersCrud


def get_users_crud(db: Annotated[Session, Depends(get_db)]) -> UsersCrud:
    return UsersCrud(db)


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


UsersCrudDep = Annotated[UsersCrud, Depends(get_users_crud)]
CheckInsCrudDep = Annotated[CheckInsCrud, Depends(get_check_ins_crud)]
AuthorsCrudDep = Annotated[AuthorsCrud, Depends(get_authors_crud)]
GenresCrudDep = Annotated[GenresCrud, Depends(get_genres_crud)]
BooksCrudDep = Annotated[BooksCrud, Depends(get_books_crud)]
BookCopiesCrudDep = Annotated[BookCopiesCrud, Depends(get_book_copies_crud)]
BookRentsCrudDep = Annotated[BookRentsCrud, Depends(get_book_rents_crud)]
