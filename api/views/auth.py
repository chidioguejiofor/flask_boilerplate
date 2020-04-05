from settings import endpoint
from flask import request, redirect
from flask_restplus import Resource
from api.schemas.user import (UserSchema, LoginSchema, ForgotPasswordSchema,
                              ChangePasswordSchema)
from api.models import User
from api.utils.exceptions import ResponseException
from api.utils.token_generator import TokenGenerator
from api.utils.id_generator import IDGenerator
from api.utils.cookie_manager import CookieManager
from api.utils.constants import (AUTH_HASH, VERIFY_EMAIL_HASH,
                                 AUTH_LOGIN_TIME_DELTA, RESET_HASH,
                                 VERIFY_EMAIL_TIME_DELTA)
from api.utils.messages.success import REGISTER, LOGIN, EMAIL_SENT, UPDATED_MSG
from api.utils.messages.error import serialization_error
from api.services.redis_util import RedisUtil
from .base import BaseView


@endpoint('/auth/register')
class RegisterView(BaseView):
    def post(self):
        from api.services.emails import EmailUtil
        schema = UserSchema()
        user = schema.load(request.get_json())
        user.save()
        hash_ = f'{VERIFY_EMAIL_HASH}_{user.id}'  #  with this we can clear easily on pwd reset
        redis_key = IDGenerator.generate_id()
        RedisUtil.hset(hash_, redis_key, user.id, **VERIFY_EMAIL_TIME_DELTA)
        confirm_link = f'{request.host_url}api/auth/confirm/{redis_key}'
        EmailUtil.send_email_from_template(
            'Verify your Email',
            'confirm-email',
            user.email,
            confirm_link=confirm_link,
        )
        return {'message': REGISTER}, 201


@endpoint('/auth/login')
class LoginView(BaseView):
    @staticmethod
    def post():
        schema = LoginSchema()
        request_dict = schema.load(request.get_json())
        username_or_email = request_dict['username_or_email']
        password = request_dict['password']
        if '@' in username_or_email:
            user = User.query.filter_by(email=username_or_email).first()
        else:
            user = User.query.filter_by(username=username_or_email).first()
        if not user or not user.verify_password(password):
            raise ResponseException(
                message=serialization_error['not_found'].format('Credentials'),
                status_code=404)
        schema = UserSchema()
        data = schema.generate_response_data(user, LOGIN)
        token = TokenGenerator.create_auth_token(user, **AUTH_LOGIN_TIME_DELTA)
        hash_ = f'{AUTH_HASH}_{user.id}'
        redis_key = IDGenerator.generate_id()
        RedisUtil.hset(hash_, redis_key, token, **AUTH_LOGIN_TIME_DELTA)
        auth_id = f'{redis_key}|{user.id}'
        return CookieManager.add_cookie_to_response(data, auth_id=auth_id)


@endpoint('/auth/forgot-password')
class ForgotPasswordView(BaseView):
    @staticmethod
    def post():
        from api.services.emails import EmailUtil
        schema = ForgotPasswordSchema()
        request_dict = schema.load(request.get_json())
        user = User.query.filter_by(email=request_dict['email']).first()
        if not user:
            raise ResponseException(
                message=serialization_error['not_found'].format('Email'),
                status_code=404,
            )
        redirect_url = request_dict['redirect_url']
        redis_key = IDGenerator.generate_id()
        RedisUtil.hset(RESET_HASH, redis_key, user.email, minutes=15)
        reset_link = f'{request.host_url}api/auth/reset-password/{redis_key}?redirect_url={redirect_url}'
        EmailUtil.send_email_from_template(
            'Reset your Email',
            'reset-email',
            user.email,
            reset_link=reset_link,
        )

        return {'message': EMAIL_SENT.format(user.email)}


@endpoint('/auth/reset-password/<string:reset_id>')
class ConfirmResetLinkView(BaseView):
    @staticmethod
    def get(reset_id):
        redirect_url = request.args.get('redirect_url')
        email = RedisUtil.hget(RESET_HASH, reset_id)
        if not redirect_url:
            return serialization_error['link_clicked_is_invalid'], 400
        url = redirect_url + '/' + reset_id
        if not email:
            return redirect(f'{url}?is_valid=false')

        return redirect(f'{url}?is_valid=true')

    @staticmethod
    def post(reset_id):
        schema = ChangePasswordSchema()
        request_dict = schema.load(request.get_json())
        email = RedisUtil.hget(RESET_HASH, reset_id)
        if not email:
            raise ResponseException(
                message=serialization_error['not_found'].format('Reset id'),
                status_code=404)
        user = User.query.filter_by(email=email).first()
        user.password = request_dict['password']
        user.update()
        RedisUtil.hdel(RESET_HASH, reset_id)
        RedisUtil.delete_hash(F'{AUTH_HASH}_{user.id}')
        return {
            'message': UPDATED_MSG.format('Password'),
        }


@endpoint('/auth/change-password')
class ChangePassword(BaseView):
    PROTECTED_METHODS = ['POST']

    def post(self, user_data):
        schema = ChangePasswordSchema()
        request_dict = schema.load(request.get_json())
        user = User.query.filter_by(id=user_data['id']).first()
        user.password = request_dict['password']
        user.update()
        RedisUtil.delete_hash(f'{AUTH_HASH}_{user.id}')
        return {
            'message': UPDATED_MSG.format('Password'),
        }