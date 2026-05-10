from flask import Blueprint, jsonify, request
from web_app.data_utils import insert_checker_output


bp = Blueprint("get_checkr_data", __name__, url_prefix="/checker-output")

REQUIRED_FIELDS = {
    "user_id": int,
    "line": int,
    "po_id": int,
    "field_name": str,
    "defect_name": str,
    "actual_event_time": str,
}

FIELD_NAMES = {"pass", "reject", "alter"}


def validate_checker_output_data(data: dict) -> tuple[dict | None, list[str]]:
    """Validate JSON data for the checker_output table."""
    errors = []
    validated_data = {}

    for field_name, field_type in REQUIRED_FIELDS.items():
        value = data.get(field_name)
        if value is None:
            errors.append(f"{field_name} is required")
        elif type(value) is not field_type:
            errors.append(f"{field_name} must be {field_type.__name__}")
        elif field_name != "defect_name" and isinstance(value, str) and not value.strip():
            errors.append(f"{field_name} cannot be empty")
        elif isinstance(value, str):
            validated_data[field_name] = value.strip()
        else:
            validated_data[field_name] = value

    field_name = validated_data.get("field_name")
    defect_name = validated_data.get("defect_name")
    if type(field_name) is str and field_name not in FIELD_NAMES:
        errors.append("field_name must be pass, reject, or alter")
    elif field_name == "alter":
        if "defect_name" in validated_data and not defect_name:
            errors.append("defect_name cannot be empty when field_name is alter")
    elif field_name in {"pass", "reject"}:
        if defect_name:
            errors.append("defect_name is only allowed when field_name is alter")
        else:
            validated_data["defect_name"] = None

    if errors:
        return None, errors

    return validated_data, []


@bp.route("", methods=("POST",))
def receive_checker_output():
    """Receive checker output JSON from the app."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "errors": ["Request body must be a JSON object"],
        }), 400

    validated_data, errors = validate_checker_output_data(data)
    if errors:
        return jsonify({
            "status": "error",
            "errors": errors,
        }), 400

    try:
        insert_checker_output(**validated_data)
    except Exception as e:
        return jsonify({
            "status": "error",
            "errors": [str(e)],
        }), 500

    return jsonify({
        "status": "created",
        "message": "Checker output saved.",
        "data": validated_data,
    }), 201
