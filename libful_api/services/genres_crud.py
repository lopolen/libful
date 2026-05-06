from sqlalchemy import select
from sqlalchemy.orm import Session

from libful_api.models.genre import Genre


class GenresCrud:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def create_genre(self, *, name: str) -> Genre:
        genre = Genre(name=name)
        self.db_session.add(genre)
        self.db_session.flush()
        return genre

    def read_genre(self, *, genre_id: int) -> Genre | None:
        return self.db_session.get(Genre, genre_id)

    def list_genres(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Genre]:
        query = select(Genre).order_by(Genre.id).offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return list(self.db_session.scalars(query).all())

    def update_genre(
        self,
        *,
        genre_id: int,
        name: str | None = None,
    ) -> Genre | None:
        genre = self.read_genre(genre_id=genre_id)
        if genre is None:
            return None

        if name is not None:
            genre.name = name

        self.db_session.flush()
        return genre

    def delete_genre(self, *, genre_id: int) -> bool:
        genre = self.read_genre(genre_id=genre_id)
        if genre is None:
            return False

        self.db_session.delete(genre)
        self.db_session.flush()
        return True
