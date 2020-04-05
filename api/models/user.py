from settings import db
from api.utils.messages.error import db_errors
from sqlalchemy import UniqueConstraint
from .base import BaseModel
from passlib.hash import pbkdf2_sha512


class User(BaseModel):
    _UNIQUE_VIOLATION_MSG = db_errors['already_exists'].format(
        'Username or Email')
    username = db.Column(
        db.String(20),
        nullable=False,
    )
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(320), nullable=False)
    password_hash = db.Column(db.VARCHAR(130), nullable=False)
    verified = db.Column(db.BOOLEAN, default=False, nullable=False)
    _password = None
    redirect_url = None

    # Constraints
    UniqueConstraint(email, name='user_unique_email')
    UniqueConstraint(username, name='user_unique_username')

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password_str):
        self._password = password_str
        self.password_hash = pbkdf2_sha512.hash(password_str)

    def verify_password(self, password_str):
        return pbkdf2_sha512.verify(password_str, self.password_hash)
