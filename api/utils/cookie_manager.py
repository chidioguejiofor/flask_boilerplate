from flask import make_response
import os


class CookieManager:
    @staticmethod
    def extract_cookie_from_response(response):
        cookies = response.headers.getlist('Set-Cookie')
        cookie_mapper = {}
        for cookie in cookies:
            splitted = cookie.split(';', 1)
            cookie_key, value = splitted[0].split('=')
            other_options = splitted[1]
            cookie_mapper[cookie_key] = value, other_options

        return cookie_mapper

    @staticmethod
    def add_cookie_to_response(response_data,
                               status_code=200,
                               **cookie_kwargs):
        resp = make_response(response_data)
        resp.status_code = status_code
        secured = os.getenv('FLASK_ENV') == 'production'
        for key, value in cookie_kwargs.items():
            resp.set_cookie(key,
                            value,
                            path='/',
                            httponly=True,
                            secure=secured)

        return resp

    def decode_cookie(self, cookie):
        pass
