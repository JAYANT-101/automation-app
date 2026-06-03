from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash

from web_app.data_utils import get_user_info


bp = Blueprint("user_authorization", __name__, url_prefix="/users")

AUTH_FIELDS = ("username", "password")


def validate_authorization_data(data: dict) -> tuple[dict | None, list[str]]:
    """Validate JSON credentials sent by the Kotlin checker app."""
    errors = []
    credentials = {}

    for field_name in AUTH_FIELDS:
        value = data.get(field_name)

        if value is None:
            errors.append(f"{field_name} is required")
        elif type(value) is not str:
            errors.append(f"{field_name} must be str")
        elif not value.strip():
            errors.append(f"{field_name} cannot be empty")
        elif field_name == "username":
            credentials[field_name] = value.strip()
        else:
            credentials[field_name] = value

    if errors:
        return None, errors

    return credentials, []


def unauthorized_response():
    return jsonify({
        "status": "unauthorized",
        "authorized": False,
        "errors": ["Invalid username or password"],
    }), 401


@bp.route("/authorize", methods=("POST",))
def authorize_user():
    """Authorize a checker app user against the users table."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "errors": ["Request body must be a JSON object"],
        }), 400

    credentials, errors = validate_authorization_data(data)
    if errors:
        return jsonify({
            "status": "error",
            "errors": errors,
        }), 400

    try:
        users = get_user_info(credentials["username"])
    except Exception as e:
        return jsonify({
            "status": "error",
            "errors": [str(e)],
        }), 500

    if not users:
        return unauthorized_response()

    user_id, username, password_hash, *_ = users[0]
    if not check_password_hash(password_hash, credentials["password"]):
        return unauthorized_response()

    return jsonify({
        "status": "authorized",
        "authorized": True,
        "message": "User authorized.",
        "data": {
            "user_id": user_id,
            "username": username,
        },
    })
