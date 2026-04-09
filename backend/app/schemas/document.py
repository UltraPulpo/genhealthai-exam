"""Document schema."""

from marshmallow import Schema, fields


class DocumentSchema(Schema):
    """Public document representation."""

    id = fields.String(dump_only=True)
    original_filename = fields.String(dump_only=True)
    content_type = fields.String(dump_only=True)
    file_size_bytes = fields.Integer(dump_only=True)
    extracted_data = fields.Dict(dump_only=True)
    uploaded_at = fields.DateTime(dump_only=True)
