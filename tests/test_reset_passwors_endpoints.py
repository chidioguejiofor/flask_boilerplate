import json
from unittest.mock import patch
from faker import Faker
from api.models import User
from api.utils.constants import RESET_HASH, RESET_PASSWORD_DELTA, AUTH_HASH, COOKIE_AUTH_KEY
from api.utils.messages.success import EMAIL_SENT, UPDATED_MSG
from api.utils.id_generator import IDGenerator
from api.services.redis_util import RedisUtil
from .mock import RedisMock
from api.utils.messages.error import serialization_error, authentication_errors
from api.utils.token_generator import TokenGenerator
from .assertion_helpers import assert_send_grid_mock_send

fake = Faker()
FORGOT_PASSWORD_URL = '/api/auth/forgot-password'
CHANGE_PASSWORD_URL = '/api/auth/change-password'
RESET_PASSWORD_URL = '/api/auth/reset-password/{}'


@patch('api.services.emails.EmailUtil.SEND_CLIENT.send', autospec=True)
class TestForgotPasswordEndpoint:
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

        api_data = {'email': user.email, 'redirect_url': 'http://some.url.com'}

        return user, api_data, json.dumps(api_data)

    def test_user_should_be_able_to_send_forgot_password_request(
        self,
        mock_send,
        client,
        mock_send_html_delay,
        init_db,
    ):
        user, api_data, api_json_data = self.generate_api_data()
        response = client.post(FORGOT_PASSWORD_URL,
                               data=api_json_data,
                               content_type="application/json")

        # Assert JSON response and db post-conditions
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == EMAIL_SENT.format(user.email)
        assert len(RedisMock.expired_cache) == len(RedisMock.cache) == 1

        key = list(RedisMock.cache.keys())[0]
        user_email = RedisMock.cache.get(key)
        exp_key = list(RedisMock.expired_cache.keys())[0]
        exp_time = RedisMock.expired_cache.get(exp_key)

        assert key == exp_key
        assert exp_time == RESET_PASSWORD_DELTA['minutes'] * 60
        assert user.email == user_email  #  assert  that redis stores user_id as the key

        # Assert HTML
        html_content = assert_send_grid_mock_send(mock_send, user.email)
        redis_id = key.split(f'{RESET_HASH}_')[1]
        redirect_url = api_data['redirect_url']
        assert redis_id in html_content
        assert f'/api/auth/reset-password/{redis_id}?redirect_url={redirect_url}' in html_content

    def test_should_return_400_when_required_fields_are_missing(
        self,
        mock_send,
        client,
        mock_send_html_delay,
        init_db,
    ):
        response = client.post(FORGOT_PASSWORD_URL,
                               data=json.dumps({}),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert mock_send.called is False
        assert mock_send_html_delay.called is False
        assert response_body['errors']['redirect_url'][
            0] == serialization_error['required']
        assert response_body['errors']['email'][0] == serialization_error[
            'required']
        assert response_body['message'] == serialization_error[
            'invalid_fields']

    def test_should_return_404_when_the_email_is_not_in_db(
        self,
        mock_send,
        client,
        mock_send_html_delay,
        init_db,
    ):
        user, api_data, api_json_data = self.generate_api_data()
        api_json_data = json.dumps({
            'redirect_url': api_data['redirect_url'],
            'email': 'unknown-email@email.com'
        })
        response = client.post(FORGOT_PASSWORD_URL,
                               data=api_json_data,
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 404
        assert mock_send.called is False
        assert mock_send_html_delay.called is False
        assert response_body['message'] == serialization_error[
            'not_found'].format('Email')


class TestClickLinkEndpoint:
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

        redis_id = IDGenerator.generate_id()
        RedisUtil.hset(RESET_HASH, redis_id, user.email)

        return user, redis_id

    def test_user_should_be_redirected_when_he_clicks_link_to_in_email(
        self,
        client,
        init_db,
    ):
        user, redis_id = self.generate_api_data()
        url = RESET_PASSWORD_URL.format(redis_id)
        redirect_url = f'http://some.com'
        url = f'{url}?redirect_url={redirect_url}'
        response = client.get(url, content_type="application/json")

        # Assert JSON response and db post-conditions
        assert response.status_code == 302
        assert response.headers.get('Location') == \
               f"{redirect_url}/{redis_id}?is_valid=true"

    def test_should_return_not_valid_when_the_redis_id_is_not_found(
        self,
        client,
        init_db,
    ):
        redis_id = 'invalid-id'
        url = RESET_PASSWORD_URL.format(redis_id)
        redirect_url = f'http://some.com'
        url = f'{url}?redirect_url={redirect_url}'
        response = client.get(url, content_type="application/json")

        # Assert JSON response and db post-conditions

        assert response.status_code == 302
        assert response.headers.get('Location') == \
               f"{redirect_url}/{redis_id}?is_valid=false"

    def test_should_return_invalid_link_when_the_redirect_url_is_missing(
        self,
        client,
        init_db,
    ):
        redis_id = 'invalid-id'
        url = RESET_PASSWORD_URL.format(redis_id)
        response = client.get(url, content_type="application/json")

        # Assert JSON response and db post-conditions
        message = serialization_error['link_clicked_is_invalid']
        assert response.status_code == 400
        assert response.data.decode() == f'"{message}"\n'


class ResetPasswordBaseTest:
    def generate_api_data(self, login_user_count=5):
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

        redis_id = IDGenerator.generate_id()
        RedisUtil.hset(RESET_HASH, redis_id, user.email)

        #  login the user several times
        for _ in range(login_user_count):
            login_id = IDGenerator.generate_id()
            hash_ = f'{AUTH_HASH}_{user.id}'
            token = TokenGenerator.create_auth_token(user, days=4)
            RedisUtil.hset(hash_, login_id, token)

        return user, redis_id, login_id


class TestResetPasswordEndpoint(ResetPasswordBaseTest):
    def test_user_reset_password_when_the_reset_id_is_valid(
        self,
        client,
        init_db,
    ):
        user, redis_id, login_id = self.generate_api_data()

        api_data = {'password': 'some-very-nice-password'}

        url = RESET_PASSWORD_URL.format(redis_id)
        response = client.post(url,
                               data=json.dumps(api_data),
                               content_type="application/json")

        response_body = json.loads(response.data)
        user = User.query.filter_by(email=user.email).first()
        login_hash = f'{AUTH_HASH}_{user.id}'
        assert response_body['message'] == UPDATED_MSG.format('Password')
        assert response.status_code == 200
        assert user.verify_password(api_data['password']) is True
        assert RedisUtil.hget(RESET_HASH, redis_id) is None
        assert len(RedisUtil.find_keys(login_hash)) == 0

    def test_should_fail_when_required_fields_are_missing(
        self,
        client,
        init_db,
    ):
        user, redis_id, _ = self.generate_api_data()
        url = RESET_PASSWORD_URL.format(redis_id)
        response = client.post(url,
                               data=json.dumps({}),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['errors']['password'][0] == serialization_error[
            'required']
        assert response_body['message'] == serialization_error[
            'invalid_fields']

    def test_should_fail_when_reset_id_is_not_found(
        self,
        client,
        init_db,
    ):
        user, _, _ = self.generate_api_data()
        url = RESET_PASSWORD_URL.format('invalid-reset_id')
        api_data = {'password': 'some-very-nice-password'}
        response = client.post(url,
                               data=json.dumps(api_data),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 404
        assert response_body['message'] == serialization_error[
            'not_found'].format('Reset id')


class TestLoggedInUserChangePasswordEndpoint(ResetPasswordBaseTest):
    def test_logged_in_user_should_be_able_to_change_password(
        self,
        client,
        init_db,
    ):
        user, redis_id, login_id = self.generate_api_data()

        api_data = {'password': 'some-very-nice-password'}
        auth_id = f'{login_id}|{user.id}'
        client.set_cookie('/', COOKIE_AUTH_KEY, auth_id)
        response = client.post(CHANGE_PASSWORD_URL,
                               data=json.dumps(api_data),
                               content_type="application/json")

        response_body = json.loads(response.data)
        user = User.query.filter_by(email=user.email).first()
        login_hash = f'{AUTH_HASH}_{user.id}'
        print(response_body)
        assert response_body['message'] == UPDATED_MSG.format('Password')
        assert response.status_code == 200
        assert user.verify_password(api_data['password']) is True
        assert len(RedisUtil.find_keys(login_hash)) == 0

    def test_should_fail_when_required_fields_are_missing(
        self,
        client,
        init_db,
    ):
        user, _, login_id = self.generate_api_data()
        auth_id = f'{login_id}|{user.id}'
        client.set_cookie('/', COOKIE_AUTH_KEY, auth_id)
        response = client.post(CHANGE_PASSWORD_URL,
                               data=json.dumps({}),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['errors']['password'][0] == serialization_error[
            'required']
        assert response_body['message'] == serialization_error[
            'invalid_fields']

    def test_should_fail_when_the_user_is_not_logged_in(
        self,
        client,
        init_db,
    ):
        user, _, _ = self.generate_api_data()
        api_data = {'password': 'some-very-nice-password'}
        response = client.post(CHANGE_PASSWORD_URL,
                               data=json.dumps(api_data),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 401

        assert response_body['message'] == authentication_errors[
            'session_expired']
