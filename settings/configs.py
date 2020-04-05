import os
import dotenv

dotenv.load_dotenv()


class BaseConfig:
    """Base app configuration class"""

    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('APP_SECRET')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_APP = 'app.py'
    CELERY_BROKER_URL = os.getenv('REDIS_SERVER_URL')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND',
                                      CELERY_BROKER_URL)


class ProductionConfig(BaseConfig):
    """Production app configuration class"""

    TESTING = False
    PROPAGATE_EXCEPTIONS = True


class StagingConfig(BaseConfig):
    """Staging app configuration class"""

    TESTING = False
    PROPAGATE_EXCEPTIONS = True


class TestingConfig(BaseConfig):
    """Testing app configuration class"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL')
    FLASK_ENV = 'testing'


class DevelopmentConfig(BaseConfig):
    """Development app configuration class"""

    DEBUG = True


ENV_MAPPER = {
    'staging': StagingConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'development': DevelopmentConfig,
}
