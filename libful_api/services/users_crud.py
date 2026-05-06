from sqlalchemy.orm import Session
from sqlalchemy import ColumnElement, or_, select
from sqlalchemy.exc import IntegrityError

from libful_api.models.user import User
from libful_api.core.security import validate_email_address, hash_password
from libful_api.core.exceptions import UserAlreadyExists


class UsersCrud:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def create_user(self, *, username: str, first_name: str, last_name: str,
                    email: str | None, phone: str | None, password: str | None) -> User:
        if email is not None:
            email = validate_email_address(email)

        if self._user_exists(username=username, email=email, phone=phone):
            raise UserAlreadyExists("User with this email, phone or username already exists")

        if password is not None:
            password_hash = hash_password(password)
        else:
            password_hash = None

        try:
            user = User(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                password_hash=password_hash
            )
            self.db_session.add(user)
            self.db_session.flush()
        except IntegrityError:
            self.db_session.rollback()
            raise UserAlreadyExists("User with this email, phone or username already exists")

        return user

    def read_user(self, *, username: str) -> User | None:
        return self.db_session.scalar(
            select(User).where(User.username == username)
        )

    def list_users(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[User]:
        query = select(User).order_by(User.id).offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return list(self.db_session.scalars(query).all())

    def search_users(
        self,
        *,
        user_id: int | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[User]:
        conditions: list[ColumnElement[bool]] = []

        if user_id is not None:
            conditions.append(User.id == user_id)
        if first_name is not None:
            conditions.append(User.first_name.ilike(f"%{first_name}%"))
        if last_name is not None:
            conditions.append(User.last_name.ilike(f"%{last_name}%"))
        if email is not None:
            conditions.append(User.email.ilike(f"%{email}%"))
        if phone is not None:
            conditions.append(User.phone.ilike(f"%{phone}%"))

        query = select(User).order_by(User.id).offset(offset).limit(limit)
        if conditions:
            query = query.where(*conditions)

        return list(self.db_session.scalars(query).all())

    def update_user(
        self,
        *,
        username: str,
        new_username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        password: str | None = None,
    ) -> User | None:
        user = self.read_user(username=username)
        if user is None:
            return None

        if email is not None:
            email = validate_email_address(email)

        if self._user_exists(
            username=new_username,
            email=email,
            phone=phone,
            exclude_user_id=user.id,
        ):
            raise UserAlreadyExists("User with this email, phone or username already exists")

        if new_username is not None:
            user.username = new_username
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if email is not None:
            user.email = email
        if phone is not None:
            user.phone = phone
        if password is not None:
            user.password_hash = hash_password(password)

        try:
            self.db_session.flush()
        except IntegrityError:
            self.db_session.rollback()
            raise UserAlreadyExists("User with this email, phone or username already exists")

        return user

    def delete_user(self, *, username: str) -> bool:
        user = self.read_user(username=username)
        if user is None:
            return False

        self.db_session.delete(user)
        self.db_session.flush()
        return True

    def _user_exists(
        self,
        *,
        username: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        exclude_user_id: int | None = None,
    ) -> bool:
        conditions = []
        if username is not None:
            conditions.append(User.username == username)
        if email is not None:
            conditions.append(User.email == email)
        if phone is not None:
            conditions.append(User.phone == phone)

        if not conditions:
            return False

        query = select(User.id).where(or_(*conditions))
        if exclude_user_id is not None:
            query = query.where(User.id != exclude_user_id)

        result = self.db_session.scalar(query)
        return result is not None
