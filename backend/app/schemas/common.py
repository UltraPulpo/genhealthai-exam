"""Common schemas shared across the API."""

from marshmallow import Schema, fields


class ErrorSchema(Schema):
    """Standard error response envelope."""

    code = fields.String()
    message = fields.String()
    details = fields.List(fields.Dict())
