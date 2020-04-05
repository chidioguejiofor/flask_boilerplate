from api.models import User as UserModel
from .custom_fields import fields, AlphaOnlyField, AlphanumericField, StringField
from .base import BaseSchema


class ForgotPasswordSchema(BaseSchema):
    redirect_url = StringField(load_only=True, required=True)
    email = StringField(max_length=320, required=True)


class ChangePasswordSchema(BaseSchema):
    password = StringField(load_only=True, required=True)


class UserSchema(ForgotPasswordSchema, ChangePasswordSchema):
    __MODEL__ = UserModel
    username = AlphanumericField(min_length=1, max_length=20, required=True)
    first_name = AlphaOnlyField(min_length=3, max_length=20, required=True)
    last_name = AlphaOnlyField(min_length=3, max_length=20, required=True)
    verified = fields.Boolean(dump_only=True)


class LoginSchema(ChangePasswordSchema):
    username_or_email = StringField(required=True)
