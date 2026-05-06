from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from libful_api.core.database import get_db
from libful_api.services.users_crud import UsersCrud


def get_users_crud(db: Annotated[Session, Depends(get_db)]) -> UsersCrud:
    return UsersCrud(db)


UsersCrudDep = Annotated[UsersCrud, Depends(get_users_crud)]
