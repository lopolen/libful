from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from libful_api.models.user import User
from libful_api.core.security import validate_email_address, generate_short_unique_str, hash_password
from libful_api.core.exceptions import UserAlreadyExists


class UsersCrud:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def create_user(self, *, username: str, first_name:str, last_name: str, 
                    email: str | None, phone: str | None, password: str | None):
        if email is not None:
            email = validate_email_address(email)
            if self._user_exists(email=email):
                raise UserAlreadyExists
        
        if password is not None:
            password_hash = hash_password(password)
        else:
            password_hash = None

        try:
            user = User(
                username = generate_short_unique_str(),
                first_name = first_name,
                last_name = last_name,
                email = email,
                phone = phone,
                password_hash = password_hash
            )
            self.db_session.add(user)
            self.db_session.flush()
        except IntegrityError:
            raise UserAlreadyExists("User with this mail or username already exists")
        
        return user
    

    def read_user(self, *, username: str):
        ...

        
    def _user_exists(self, *, email: str) -> bool:
        result = self.db_session.scalar(
            select(User.id).where(User.email == email)
        )
        return result is not None
