from flask import request
from functools import wraps
from api.utils.constants import AUTH_HASH
from api.utils.token_generator import TokenGenerator
from api.utils.exceptions import ResponseException
from api.utils.messages.error import authentication_errors
from api.services.redis_util import RedisUtil


class Authentication:
    def __init__(self, view):
        self.view = view

    def _decode_token(self, check_user_is_verified=False):
        """Decoded a token and returns the decoded data

        Args:
            check_user_is_verified (bool): When this is true, this ensures that
                the user is also verified

        Returns:
            dict, str: The decoded token data
        """
        decoded_data = None
        auth_id = request.cookies.get('auth_id')
        if auth_id:
            redis_id, user_id = request.cookies.get('auth_id').split('|')
            hash_ = f'{AUTH_HASH}_{user_id}'
            token = RedisUtil.hget(hash_, redis_id)
            decoded_data = TokenGenerator.decode_token_or_none(token)
        if not decoded_data or not auth_id:
            raise ResponseException(
                authentication_errors['session_expired'],
                401,
            )

        #  TODO: IF we want to check if the user i verified, this is where we would
        #   do it

        return decoded_data['data']

    def _authenticate_user(self):
        view = self.view
        method = request.method.upper()

        if method in view.PROTECTED_METHODS:
            return self._decode_token()
        return None

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_data = self._authenticate_user()
            if user_data:
                return func(*args, **kwargs, user_data=user_data)
            return func(*args, **kwargs)

        return wrapper


class classproperty(object):
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)
