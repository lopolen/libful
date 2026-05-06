from sqlalchemy import select
from sqlalchemy.orm import Session

from libful_api.models.author import Author


class AuthorsCrud:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def create_author(self, *, full_name: str) -> Author:
        author = Author(full_name=full_name)
        self.db_session.add(author)
        self.db_session.flush()
        return author

    def read_author(self, *, author_id: int) -> Author | None:
        return self.db_session.get(Author, author_id)

    def list_authors(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Author]:
        query = select(Author).order_by(Author.id).offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return list(self.db_session.scalars(query).all())

    def update_author(
        self,
        *,
        author_id: int,
        full_name: str | None = None,
    ) -> Author | None:
        author = self.read_author(author_id=author_id)
        if author is None:
            return None

        if full_name is not None:
            author.full_name = full_name

        self.db_session.flush()
        return author

    def delete_author(self, *, author_id: int) -> bool:
        author = self.read_author(author_id=author_id)
        if author is None:
            return False

        self.db_session.delete(author)
        self.db_session.flush()
        return True
