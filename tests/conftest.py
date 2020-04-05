"""Module for Pytest Configuration"""

# system imports
from os import getenv, environ
from unittest.mock import Mock
from .mock import RedisMock
# third party imports
import pytest
# local import
from settings import db, create_app

TEST_ENV = 'testing'
environ['FLASK_ENV'] = TEST_ENV
ENV = getenv('FLASK_ENV')


@pytest.fixture(scope='session')
def flask_app():
    """Create a flask application instance for Pytest.
	Returns:
		Object: Flask application object
	"""

    # create an application instance
    _app = create_app(ENV)

    # Establish an application context before running the tests.
    ctx = _app.app_context()
    ctx.push()

    # yield the application context for making requests
    yield _app

    ctx.pop()


@pytest.fixture
def client(flask_app):
    """Setup client for making http requests, this will be run on every
	test function.
	Args:
		flask_app (func): Flask application instance
	Returns:
		Object: flask application client instance
	"""

    # initialize the flask test_client from the flask application instance
    client = flask_app.test_client()

    yield client


@pytest.fixture
def init_db(flask_app):
    """Fixture to initialize the database"""
    with flask_app.app_context():
        db.create_all()
        RedisMock.flush_all()
        yield db
        db.session.close()
        db.drop_all()


@pytest.fixture(scope='function')
def mock_send_html_delay():
    from api.services.emails import EmailUtil
    EmailUtil.send_mail_as_html.delay = Mock(
        side_effect=EmailUtil.send_mail_as_html)
    return EmailUtil.send_mail_as_html.delay
