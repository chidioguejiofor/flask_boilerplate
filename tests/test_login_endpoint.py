import json
from api.utils.constants import AUTH_HASH, AUTH_LOGIN_TIME_DELTA, VERIFY_EMAIL_TIME_DELTA
from faker import Faker
from api.models import User
from api.utils.token_generator import TokenGenerator
from api.utils.cookie_manager import CookieManager
from api.utils.messages.error import serialization_error, db_errors
from api.utils.messages.success import LOGIN
from .mock import RedisMock

fake = Faker()
LOGIN_URL = '/api/auth/login'


class TestLoginEndpoint:
    def generate_api_data(self):
        user_data = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "password": fake.password(),
            "username": fake.profile()['username'][:30],
            "redirect_url": fake.url()
        }

        user = User(**user_data)
        user.save()

        api_data = {
            'username_or_email': user.email,
            'password': user_data['password']
        }

        return user, api_data

    def test_fails_when_credentials_are_not_found(self, client, init_db):
        user, api_data = self.generate_api_data()
        api_data = {
            'username_or_email': user.email,
            'password': 'some_unknown_password',
        }
        response = client.post(LOGIN_URL,
                               data=json.dumps(api_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        print(response_body)
        assert response.status_code == 404
        assert response_body['message'] == serialization_error[
            'not_found'].format('Credentials')

    def test_fails_when_required_fields_are_missing(self, client, init_db):
        response = client.post(LOGIN_URL,
                               data=json.dumps({}),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['message'] == serialization_error[
            'invalid_fields']
        assert response_body['errors']['username_or_email'][
            0] == serialization_error['required']
        assert response_body['errors']['password'][0] == serialization_error[
            'required']

    def test_user_login_when_data_is_valid(self, client, init_db):
        user, api_data = self.generate_api_data()
        response = client.post(LOGIN_URL,
                               data=json.dumps(api_data),
                               content_type="application/json")

        # Assert JSON response and db post-conditions
        response_body = json.loads(response.data)

        assert response.status_code == 200
        assert (response_body['data']['first_name'] == user.first_name)
        assert (response_body['data']['last_name'] == user.last_name)
        assert (response_body['data']['verified'] == user.verified)
        assert (response_body['data']['email'] == user.email)
        assert response_body['data']['id'] == user.id
        assert response_body['message'] == LOGIN

        # Assert Redis and Token post-conditions

        key = list(RedisMock.cache.keys())[0]
        token = RedisMock.cache.get(key)
        exp_key = list(RedisMock.expired_cache.keys())[0]
        exp_time = RedisMock.expired_cache.get(exp_key)
        assert len(RedisMock.expired_cache) == len(RedisMock.cache) == 1
        assert token
        token_data = TokenGenerator.decode_token(token)['data']
        assert key == exp_key
        assert exp_time == AUTH_LOGIN_TIME_DELTA[
            'days'] * 24 * 60 * 60  # 3 days
        assert token_data['verified'] is False
        assert token_data['email'] == user.email
        assert token_data['username'] == user.username
        assert token_data['id'] == user.id

        # Assert Redis
        cookie_mapper = CookieManager.extract_cookie_from_response(response)
        cookie_value, other_options = cookie_mapper['auth_id']
        cookie_key, cookie_user_id = cookie_value.split('|')
        assert f'{AUTH_HASH}_{user.id}' in key
        assert key == f'{AUTH_HASH}_{user.id}_{cookie_key}'
