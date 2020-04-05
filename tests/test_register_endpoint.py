import json
from unittest.mock import patch
from faker import Faker
from api.models import User
from api.utils.constants import VERIFY_EMAIL_HASH, VERIFY_EMAIL_TIME_DELTA
from api.utils.messages.success import REGISTER
from api.utils.messages.error import serialization_error, db_errors
from .mock import RedisMock
from .assertion_helpers import assert_send_grid_mock_send
fake = Faker()
REGISTER_URL = '/api/auth/register'


@patch('api.services.emails.EmailUtil.SEND_CLIENT.send', autospec=True)
class TestRegisterEndpoint:
    def generate_api_data(self):
        api_data = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "password": fake.password(),
            "username": fake.profile()['username'][:30],
            "redirect_url": fake.url()
        }

        return json.dumps(api_data), api_data

    def test_new_user_should_register_successfully_when_valid_data_is_provided_and_should_be_added_to_the_db(
        self,
        mock_send,
        client,
        mock_send_html_delay,
        init_db,
    ):
        # print(flask_app.url_map)
        api_json_data, api_data = self.generate_api_data()
        response = client.post(REGISTER_URL,
                               data=api_json_data,
                               content_type="application/json")

        # Assert JSON response and db post-conditions
        response_body = json.loads(response.data)
        assert response.status_code == 201
        user = User.query.filter_by(email=api_data['email']).first()

        assert response_body['message'] == REGISTER

        # Assert Redis and Token post-conditions
        assert len(RedisMock.expired_cache) == len(RedisMock.cache) == 1

        key = list(RedisMock.cache.keys())[0]
        user_id = RedisMock.cache.get(key)
        exp_key = list(RedisMock.expired_cache.keys())[0]
        exp_time = RedisMock.expired_cache.get(exp_key)

        assert key == exp_key
        assert exp_time == VERIFY_EMAIL_TIME_DELTA['minutes'] * 60
        assert user.id == user_id  #  assert  that redis stores user_id as the key

        # Assert HTML
        html_content = assert_send_grid_mock_send(mock_send, user.email)
        redis_id = key.split(f'{VERIFY_EMAIL_HASH}_')[0]
        assert redis_id in html_content
        assert f'api/auth/confirm/{redis_id}' in html_content

    def test_should_return_400_when_required_fields_are_missing(
        self,
        mock_send,
        client,
        mock_send_html_delay,
        init_db,
    ):
        response = client.post(REGISTER_URL,
                               data=json.dumps({}),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert mock_send.called is False
        assert mock_send_html_delay.called is False
        assert response_body['errors']['username'][0] == serialization_error[
            'required']
        assert response_body['errors']['email'][0] == serialization_error[
            'required']
        assert response_body['errors']['first_name'][0] == serialization_error[
            'required']
        assert response_body['errors']['last_name'][0] == serialization_error[
            'required']
        assert response_body['message'] == serialization_error[
            'invalid_fields']

    def test_should_return_409_when_the_user_already_exists_in_the_app(
        self,
        mock_send,
        client,
        mock_send_html_delay,
        init_db,
    ):
        api_json_data, api_data = self.generate_api_data()
        User(**api_data).save()  # save user to db
        response = client.post(REGISTER_URL,
                               data=api_json_data,
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 409
        assert mock_send.called is False
        assert mock_send_html_delay.called is False
        assert response_body['message'] == db_errors['already_exists'].format(
            'Username or Email')
