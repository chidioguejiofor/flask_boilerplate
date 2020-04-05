import dotenv
import os
from celery import Celery
from api.utils.constants import CELERY_TASKS
dotenv.load_dotenv()


def make_celery(app):
    celery = Celery(app.import_name,
                    backend=app.config['CELERY_RESULT_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'],
                    include=CELERY_TASKS)
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    if os.getenv('FLASK_ENV', 'development') != 'testing':
        celery.Task = ContextTask
    return celery
