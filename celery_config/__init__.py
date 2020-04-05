import os
import dotenv
from settings.service_config import make_celery
from settings import create_app
dotenv.load_dotenv()
app = create_app(os.getenv('FLASK_ENV'))

celery_app = make_celery(app)
