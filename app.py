"""API Entry Module"""

import os
import dotenv
from settings import create_app

dotenv.load_dotenv()

# gets the current environment and creates a flask app instance
ENV = os.getenv('FLASK_ENV', 'development')
app = create_app(ENV)

if __name__ == '__main__':
    app.run()
