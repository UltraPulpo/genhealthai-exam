"""Order schemas for create, update, query, and response."""

from marshmallow import Schema, fields, validate

from app.schemas.document import DocumentSchema


class OrderCreateSchema(Schema):
    """Validates order creation input. All fields optional."""

    patient_first_name = fields.String()
    patient_last_name = fields.String()
    patient_dob = fields.Date()

    insurance_provider = fields.String()
    insurance_id = fields.String()
    group_number = fields.String()

    ordering_provider_name = fields.String()
    provider_npi = fields.String()
    provider_phone = fields.String()

    equipment_type = fields.String()
    equipment_description = fields.String()
    hcpcs_code = fields.String()

    authorization_number = fields.String()
    authorization_status = fields.String()

    delivery_address = fields.String()
    delivery_date = fields.Date()
    delivery_notes = fields.String()


class OrderUpdateSchema(Schema):
    """Validates partial order update input. All fields optional."""

    patient_first_name = fields.String()
    patient_last_name = fields.String()
    patient_dob = fields.Date()

    insurance_provider = fields.String()
    insurance_id = fields.String()
    group_number = fields.String()

    ordering_provider_name = fields.String()
    provider_npi = fields.String()
    provider_phone = fields.String()

    equipment_type = fields.String()
    equipment_description = fields.String()
    hcpcs_code = fields.String()

    authorization_number = fields.String()
    authorization_status = fields.String()

    delivery_address = fields.String()
    delivery_date = fields.Date()
    delivery_notes = fields.String()


class OrderResponseSchema(Schema):
    """Order response with all fields for serialization."""

    id = fields.String(dump_only=True)
    created_by = fields.String(dump_only=True)
    status = fields.String(dump_only=True)
    error_message = fields.String(dump_only=True)

    patient_first_name = fields.String(dump_only=True)
    patient_last_name = fields.String(dump_only=True)
    patient_dob = fields.Date(dump_only=True)

    insurance_provider = fields.String(dump_only=True)
    insurance_id = fields.String(dump_only=True)
    group_number = fields.String(dump_only=True)

    ordering_provider_name = fields.String(dump_only=True)
    provider_npi = fields.String(dump_only=True)
    provider_phone = fields.String(dump_only=True)

    equipment_type = fields.String(dump_only=True)
    equipment_description = fields.String(dump_only=True)
    hcpcs_code = fields.String(dump_only=True)

    authorization_number = fields.String(dump_only=True)
    authorization_status = fields.String(dump_only=True)

    delivery_address = fields.String(dump_only=True)
    delivery_date = fields.Date(dump_only=True)
    delivery_notes = fields.String(dump_only=True)

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    document = fields.Nested(DocumentSchema, dump_only=True, allow_none=True)


class OrderQuerySchema(Schema):
    """Validates order list query parameters."""

    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))
    status = fields.String()
    patient_last_name = fields.String()
    created_after = fields.DateTime()
    created_before = fields.DateTime()
    sort_by = fields.String(load_default="created_at")
    sort_order = fields.String(load_default="desc")
