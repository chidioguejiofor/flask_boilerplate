from marshmallow import Schema, EXCLUDE, post_load
from .custom_fields import StringField


class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    __MODEL__ = None
    id = StringField(dump_only=True)

    def generate_response_data(self, obj, message=None):
        """

        Args:
            obj:
            message:

        Returns:

        """

        res_data = {'data': self.dump(obj)}

        if message:
            res_data['message'] = message

        return res_data

    @post_load
    def create_obj(self, data, **kwargs):
        if self.__MODEL__:
            return self.__MODEL__(**data)
        return data
