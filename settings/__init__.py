"""API Initialization Module"""

from flask import Flask, jsonify, Blueprint

from flask_restplus import Api
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import dotenv

from api.utils.eror_handler import error_handlers
from .configs import ENV_MAPPER

db = SQLAlchemy()
dotenv.load_dotenv()

api_blueprint = Blueprint('api_bp', __name__, url_prefix='/api')
api = Api(api_blueprint)

endpoint = api.route


def register_blueprints(application):
    """Registers all blueprints
    
    Args:
        application (Obj): Flask Instance

    Returns:
        None
    """

    application.register_blueprint(api_blueprint)


def create_app(current_env='development'):
    """Creates the flask application instance

    Args:
        current_env (string): The current environment

    Returns:
        Object: Flask instance
    """
    app = Flask(__name__)
    origins = ['*']

    if current_env == 'development':
        import logging
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    CORS(app, origins=origins, supports_credentials=True)
    app.config.from_object(ENV_MAPPER[current_env])
    db.init_app(app)
    migrate = Migrate(app, db)

    register_blueprints(app)
    error_handlers(app)

    import api.views
    import api.models

    @app.route('/', methods=['GET'])
    def health():
        """Index Route"""

        return jsonify(data={
            "status":
            'success',
            "message":
            'API service is healthy, Goto to /api/'
        }, )

    return app
