from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from libful_api.models.check_in_history import CheckInHistory
from libful_api.models.user import User


class CheckInsCrud:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def create_check_in(
        self,
        *,
        user_id: int,
        check_in_datetime: datetime | None = None,
    ) -> CheckInHistory | None:
        if not self._user_exists(user_id=user_id):
            return None

        check_in = CheckInHistory(
            user_id=user_id,
            check_in_datetime=check_in_datetime or datetime.now(timezone.utc),
        )
        self.db_session.add(check_in)
        self.db_session.flush()
        return check_in

    def list_check_ins(
        self,
        *,
        user_id: int | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[CheckInHistory] | None:
        if user_id is not None and not self._user_exists(user_id=user_id):
            return None

        query = select(CheckInHistory).order_by(
            CheckInHistory.check_in_datetime.desc(),
            CheckInHistory.id.desc(),
        ).offset(offset)

        if user_id is not None:
            query = query.where(CheckInHistory.user_id == user_id)
        if limit is not None:
            query = query.limit(limit)

        return list(self.db_session.scalars(query).all())

    def delete_check_in(self, *, check_in_id: int) -> bool:
        check_in = self.db_session.get(CheckInHistory, check_in_id)
        if check_in is None:
            return False

        self.db_session.delete(check_in)
        self.db_session.flush()
        return True

    def count_user_check_ins(self, *, user_id: int) -> int | None:
        if not self._user_exists(user_id=user_id):
            return None

        return self.db_session.scalar(
            select(func.count()).select_from(CheckInHistory).where(
                CheckInHistory.user_id == user_id
            )
        ) or 0

    def _user_exists(self, *, user_id: int) -> bool:
        return self.db_session.scalar(
            select(User.id).where(User.id == user_id)
        ) is not None
