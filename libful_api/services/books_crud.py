from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from libful_api.core.exceptions import RelatedResourceNotFound, ResourceAlreadyExists
from libful_api.models.author import Author
from libful_api.models.book import Book
from libful_api.models.genre import Genre


_UNSET = object()


class BooksCrud:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def create_book(
        self,
        *,
        title: str,
        author_id: int,
        genre_id: int,
        publish_year: int | None = None,
        isbn: str | None = None,
    ) -> Book:
        self._ensure_author_exists(author_id=author_id)
        self._ensure_genre_exists(genre_id=genre_id)
        self._ensure_isbn_is_available(isbn=isbn)

        book = Book(
            title=title,
            author_id=author_id,
            publish_year=publish_year,
            genre_id=genre_id,
            isbn=isbn,
        )
        self.db_session.add(book)
        self._flush_unique()
        return book

    def read_book(self, *, book_id: int) -> Book | None:
        return self.db_session.get(Book, book_id)

    def list_books(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Book]:
        query = select(Book).order_by(Book.id).offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return list(self.db_session.scalars(query).all())

    def update_book(
        self,
        *,
        book_id: int,
        title: Any = _UNSET,
        author_id: Any = _UNSET,
        publish_year: Any = _UNSET,
        genre_id: Any = _UNSET,
        isbn: Any = _UNSET,
    ) -> Book | None:
        book = self.read_book(book_id=book_id)
        if book is None:
            return None

        if author_id is not _UNSET:
            self._ensure_author_exists(author_id=author_id)
            book.author_id = author_id
        if genre_id is not _UNSET:
            self._ensure_genre_exists(genre_id=genre_id)
            book.genre_id = genre_id
        if isbn is not _UNSET:
            self._ensure_isbn_is_available(isbn=isbn, exclude_book_id=book.id)
            book.isbn = isbn
        if title is not _UNSET:
            book.title = title
        if publish_year is not _UNSET:
            book.publish_year = publish_year

        self._flush_unique()
        return book

    def delete_book(self, *, book_id: int) -> bool:
        book = self.read_book(book_id=book_id)
        if book is None:
            return False

        self.db_session.delete(book)
        self.db_session.flush()
        return True

    def _ensure_author_exists(self, *, author_id: int) -> None:
        if self.db_session.get(Author, author_id) is None:
            raise RelatedResourceNotFound("Author not found")

    def _ensure_genre_exists(self, *, genre_id: int) -> None:
        if self.db_session.get(Genre, genre_id) is None:
            raise RelatedResourceNotFound("Genre not found")

    def _ensure_isbn_is_available(
        self,
        *,
        isbn: str | None,
        exclude_book_id: int | None = None,
    ) -> None:
        if isbn is None:
            return

        query = select(Book.id).where(Book.isbn == isbn)
        if exclude_book_id is not None:
            query = query.where(Book.id != exclude_book_id)

        if self.db_session.scalar(query) is not None:
            raise ResourceAlreadyExists("Book with this ISBN already exists")

    def _flush_unique(self) -> None:
        try:
            self.db_session.flush()
        except IntegrityError:
            self.db_session.rollback()
            raise ResourceAlreadyExists("Book with this ISBN already exists")
