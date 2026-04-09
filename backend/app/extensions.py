"""Flask extension singletons, initialized without an app.

Each extension is bound to an application via ``init_app()`` inside the
application factory (see :func:`app.create_app`).
"""

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_smorest import Api
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)
smorest_api = Api()
cors = CORS()
talisman = Talisman()
