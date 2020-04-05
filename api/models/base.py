from settings import db
from api.utils.exceptions import DataConflictException
from sqlalchemy.exc import IntegrityError
from psycopg2 import errors
from api.utils.id_generator import IDGenerator
from sqlalchemy.ext.declarative import declared_attr

class BaseModel(db.Model):
    __abstract__ = True
    __UNIQUE_VIOLATION_MSG = ''
    id = db.Column(db.String,
                   primary_key=True,
                   default=IDGenerator.generate_id)

    @declared_attr
    def __tablename__(cls):
        return cls.__name__

    def save(self):
        db.session.add(self)
        try:
            db.session.commit()
        except IntegrityError as e:
            if isinstance(e.orig, errors.UniqueViolation):
                raise DataConflictException(
                    message=self._UNIQUE_VIOLATION_MSG, )
            # TODO: We would handle foreign constraint exception when
            #    we get concrete examples of them here

    def update(self):
        db.session.commit()
