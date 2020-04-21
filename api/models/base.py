from settings import db
from api.utils.exceptions import ModelOperationException
from sqlalchemy.exc import IntegrityError
from psycopg2 import errors
from api.utils.id_generator import IDGenerator
from api.utils.messages.error import model_errors
from sqlalchemy.ext.declarative import declared_attr

class BaseModel(db.Model):
    __abstract__ = True
    __UNIQUE_VIOLATION_MSG = ''
    __missing_fk_error_msg__ = {}
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
                raise ModelOperationException(
                    message=self._UNIQUE_VIOLATION_MSG, )
            elif isinstance(e.orig, errors.ForeignKeyViolation):
                err_string = e.orig.diag.message_detail.split('=')[0]
                err_key = err_string.split('Key ')[1][1:-1]
                error_msg = model_errors['ids_not_found']
                error_msg = self.__missing_fk_error_msg__.get(
                    err_key, error_msg)
                raise ModelOperationException(
                    message=error_msg,
                    status_code=404,
                )
            elif isinstance(e.orig, errors.NotNullViolation):
                missing_column_name = e.orig.pgerror.split(
                    'ERROR:  null value in column "')
                missing_column_name = missing_column_name[1].split('"')[0]
                raise ModelOperationException(
                    message=model_errors['column_must_have_a_value'].
                    format(missing_column_name),
                    status_code=400,
                )
            else:

                raise e

    def update(self):
        db.session.commit()
