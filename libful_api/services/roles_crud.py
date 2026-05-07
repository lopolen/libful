from sqlalchemy import select
from sqlalchemy.orm import Session

from libful_api.core.permissions import DEFAULT_ROLE_NAMES
from libful_api.models.role import Role


class RolesCrud:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def list_roles(self) -> list[Role]:
        query = select(Role).where(Role.name.in_(DEFAULT_ROLE_NAMES)).order_by(Role.id)
        return list(self.db_session.scalars(query).all())
