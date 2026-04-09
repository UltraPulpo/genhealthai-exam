"""Authentication and user schemas."""

from marshmallow import Schema, fields


class RegisterSchema(Schema):
    """Validates user registration input."""

    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)


class LoginSchema(Schema):
    """Validates login input."""

    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)


class TokenSchema(Schema):
    """Token pair response."""

    access_token = fields.String(dump_only=True)
    refresh_token = fields.String(dump_only=True)


class UserSchema(Schema):
    """Public user representation."""

    id = fields.String(dump_only=True)
    email = fields.Email(dump_only=True)
    first_name = fields.String(dump_only=True)
    last_name = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
