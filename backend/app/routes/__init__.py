"""Route registration for all blueprints."""

from app.routes.admin import admin_blp
from app.routes.auth import auth_blp
from app.routes.orders import orders_blp
from app.routes.system import system_blp


def register_blueprints(api):
    api.register_blueprint(auth_blp)
    api.register_blueprint(orders_blp)
    api.register_blueprint(admin_blp)
    api.register_blueprint(system_blp)
