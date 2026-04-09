"""Activity log schemas."""

from marshmallow import Schema, fields, validate


class ActivityLogSchema(Schema):
    """Public activity log representation."""

    id = fields.String(dump_only=True)
    user_id = fields.String(dump_only=True)
    endpoint = fields.String(dump_only=True)
    http_method = fields.String(dump_only=True)
    status_code = fields.Integer(dump_only=True)
    ip_address = fields.String(dump_only=True)
    timestamp = fields.DateTime(dump_only=True)


class ActivityLogQuerySchema(Schema):
    """Validates activity log query parameters."""

    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))
    user_id = fields.String()
    endpoint = fields.String()
    method = fields.String()
    status_code = fields.Integer()
    date_from = fields.DateTime()
    date_to = fields.DateTime()
