import os
import jwt
from datetime import datetime, timedelta


class TokenGenerator:
    SECRET = os.getenv('JWT_SECRET')

    @classmethod
    def decode_token(cls, token, verify=True):
        token_data = jwt.decode(token,
                                cls.SECRET,
                                algorithms=['HS256'],
                                verify=verify)
        return token_data

    @classmethod
    def decode_token_or_none(cls, token, verify=True):
        try:
            return cls.decode_token(token, verify=verify)
        except jwt.PyJWTError:
            return None

    @classmethod
    def create_auth_token(cls, user_data, **exp_timedelta):
        """This generates an auth token either from a user model or
        from a dictionary

        Args:
            user_data: This can be a dict or User model

        Returns:
            String representation of a token
        """
        if not isinstance(user_data, dict):
            user_data = {
                'id': user_data.id,
                'username': user_data.username,
                'email': user_data.email,
                'verified': user_data.verified,
                'redirect_url': user_data.redirect_url,
            }
        token_data = {
            'id': user_data['id'],
            'username': user_data['username'],
            'email': user_data['email'],
            'verified': user_data['verified'],
            'redirect_url': user_data['redirect_url'],
        }
        return cls.create_token(token_data, **exp_timedelta)

    @classmethod
    def create_token(cls, token_data, **timedelta_kwargs):
        if not timedelta_kwargs:
            timedelta_kwargs = {'days': 2}
        current_time = datetime.utcnow()
        payload = {
            'data': token_data,
            'exp': current_time + timedelta(**timedelta_kwargs),
            'iat': current_time,
        }
        return jwt.encode(payload, cls.SECRET,
                          algorithm='HS256').decode('utf-8')
