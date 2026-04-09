"""Auth routes blueprint."""

from marshmallow import Schema
from marshmallow import fields as ma_fields
from flask.views import MethodView
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from app.extensions import db, limiter
from app.repositories import RefreshTokenRepository, UserRepository
from app.schemas.auth import LoginSchema, RegisterSchema, TokenSchema, UserSchema
from app.services import AuthService

auth_blp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


class RefreshTokenBodySchema(Schema):
    refresh_token = ma_fields.String(required=True)


def get_auth_service() -> AuthService:
    return AuthService(
        user_repo=UserRepository(db.session),
        token_repo=RefreshTokenRepository(db.session),
    )


@auth_blp.route("/register")
class RegisterView(MethodView):
    @limiter.limit("10/minute")
    @auth_blp.arguments(RegisterSchema)
    @auth_blp.response(201, UserSchema)
    def post(self, args):
        svc = get_auth_service()
        return svc.register(
            email=args["email"],
            password=args["password"],
            first_name=args["first_name"],
            last_name=args["last_name"],
        )


@auth_blp.route("/login")
class LoginView(MethodView):
    @limiter.limit("10/minute")
    @auth_blp.arguments(LoginSchema)
    @auth_blp.response(200, TokenSchema)
    def post(self, args):
        svc = get_auth_service()
        access_token, refresh_token = svc.login(args["email"], args["password"])
        return {"access_token": access_token, "refresh_token": refresh_token}


@auth_blp.route("/refresh")
class RefreshView(MethodView):
    @auth_blp.arguments(RefreshTokenBodySchema)
    @auth_blp.response(200, TokenSchema)
    def post(self, args):
        svc = get_auth_service()
        access_token, new_refresh_token = svc.refresh(args["refresh_token"])
        return {"access_token": access_token, "refresh_token": new_refresh_token}


@auth_blp.route("/logout")
class LogoutView(MethodView):
    @jwt_required()
    @auth_blp.response(204)
    def post(self):
        user_id = get_jwt_identity()
        svc = get_auth_service()
        svc.logout(user_id)


@auth_blp.route("/me")
class MeView(MethodView):
    @jwt_required()
    @auth_blp.response(200, UserSchema)
    def get(self):
        user_id = get_jwt_identity()
        svc = get_auth_service()
        return svc.get_current_user(user_id)
