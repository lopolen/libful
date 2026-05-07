from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from libful_api.core.exceptions import (
    LastAdminRoleError,
    PasswordRequiredForRole,
    UserAlreadyExists,
)
from libful_api.core.permissions import RoleName, normalize_role_name
from libful_api.core.security import hash_password, validate_email_address
from libful_api.models.role import Role
from libful_api.models.user import User


class UsersCrud:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def create_user(
        self,
        *,
        username: str,
        first_name: str,
        last_name: str,
        email: str | None,
        phone: str | None,
        password: str | None,
        role_names: list[str | RoleName] | None = None,
    ) -> User:
        role_names = role_names or []
        if email is not None:
            email = validate_email_address(email)

        if self._user_exists(username=username, email=email, phone=phone):
            raise UserAlreadyExists(
                "User with this email, phone or username already exists"
            )

        if password is not None:
            password_hash = hash_password(password)
        else:
            if role_names:
                raise PasswordRequiredForRole("Users with roles must have a password")
            password_hash = None

        try:
            roles = self._get_or_create_roles(role_names)
            user = User(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                password_hash=password_hash,
                roles=roles,
            )
            self.db_session.add(user)
            self.db_session.flush()
        except IntegrityError:
            self.db_session.rollback()
            raise UserAlreadyExists("User with this email, phone or username already exists")

        return user

    def read_user(self, *, username: str) -> User | None:
        return self.db_session.scalar(
            select(User)
            .options(selectinload(User.roles))
            .where(User.username == username)
        )

    def read_user_by_id(self, *, user_id: int) -> User | None:
        return self.db_session.scalar(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )

    def list_users(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[User]:
        query = (
            select(User)
            .options(selectinload(User.roles))
            .order_by(User.id)
            .offset(offset)
        )
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

        query = (
            select(User)
            .options(selectinload(User.roles))
            .order_by(User.id)
            .offset(offset)
            .limit(limit)
        )
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
            raise UserAlreadyExists(
                "User with this email, phone or username already exists"
            )

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
            raise UserAlreadyExists(
                "User with this email, phone or username already exists"
            )

        return user

    def delete_user(self, *, username: str) -> bool:
        user = self.read_user(username=username)
        if user is None:
            return False
        is_admin = self._user_has_role(user=user, role_name=RoleName.ADMIN)
        if is_admin and self.count_role_users(role_name=RoleName.ADMIN) <= 1:
            raise LastAdminRoleError("Cannot delete the last admin user")

        self.db_session.delete(user)
        self.db_session.flush()
        return True

    def list_user_roles(self, *, username: str) -> list[Role] | None:
        user = self.read_user(username=username)
        if user is None:
            return None

        return sorted(user.roles, key=lambda role: role.id)

    def assign_role_to_user(
        self,
        *,
        username: str,
        role_name: str | RoleName,
    ) -> User | None:
        user = self.read_user(username=username)
        if user is None:
            return None
        if user.password_hash is None:
            raise PasswordRequiredForRole("Users with roles must have a password")

        role = self._get_or_create_role(role_name=role_name)
        if role not in user.roles:
            user.roles.append(role)
            self.db_session.flush()

        return user

    def remove_role_from_user(
        self,
        *,
        username: str,
        role_name: str | RoleName,
    ) -> User | None:
        user = self.read_user(username=username)
        if user is None:
            return None

        normalized_role_name = normalize_role_name(role_name)
        if (
            normalized_role_name == RoleName.ADMIN.value
            and self._user_has_role(user=user, role_name=RoleName.ADMIN)
            and self.count_role_users(role_name=RoleName.ADMIN) <= 1
        ):
            raise LastAdminRoleError("Cannot remove the last admin role")

        user.roles = [role for role in user.roles if role.name != normalized_role_name]
        self.db_session.flush()
        return user

    def count_role_users(self, *, role_name: str | RoleName) -> int:
        normalized_role_name = normalize_role_name(role_name)
        return self.db_session.scalar(
            select(func.count(User.id))
            .join(User.roles)
            .where(Role.name == normalized_role_name)
        ) or 0

    def has_admin_user(self) -> bool:
        return self.count_role_users(role_name=RoleName.ADMIN) > 0

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

    def _get_or_create_roles(self, role_names: list[str | RoleName]) -> list[Role]:
        return [
            self._get_or_create_role(role_name=role_name)
            for role_name in dict.fromkeys(role_names)
        ]

    def _get_or_create_role(self, *, role_name: str | RoleName) -> Role:
        normalized_role_name = normalize_role_name(role_name)
        role = self.db_session.scalar(
            select(Role).where(Role.name == normalized_role_name)
        )
        if role is not None:
            return role

        role = Role(name=normalized_role_name)
        self.db_session.add(role)
        try:
            self.db_session.flush()
        except IntegrityError:
            self.db_session.rollback()
            role = self.db_session.scalar(
                select(Role).where(Role.name == normalized_role_name)
            )
            if role is None:
                raise

        return role

    def _user_has_role(self, *, user: User, role_name: str | RoleName) -> bool:
        normalized_role_name = normalize_role_name(role_name)
        return any(role.name == normalized_role_name for role in user.roles)
