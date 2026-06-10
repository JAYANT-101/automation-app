from datetime import datetime, timedelta, timezone
from functools import wraps
from secrets import token_urlsafe
from threading import RLock

from flask import Blueprint, current_app, g, jsonify, request
from werkzeug.security import check_password_hash

from web_app.data_utils import get_user_info


bp = Blueprint("user_authorization", __name__, url_prefix="/users")

AUTH_FIELDS = ("username", "password")
SESSION_COOKIE_NAME = "checker_session_key"
SESSION_KEY_BYTES = 64
SESSION_TIMEOUT_SECONDS = 8 * 60 * 60

SESSION_STORE: dict[str, dict] = {}
SESSION_STORE_LOCK = RLock()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def session_timeout_seconds() -> int:
    return int(
        current_app.config.get(
            "CHECKER_SESSION_TIMEOUT_SECONDS",
            SESSION_TIMEOUT_SECONDS,
        )
    )


def session_cookie_name() -> str:
    return current_app.config.get(
        "CHECKER_SESSION_COOKIE_NAME",
        SESSION_COOKIE_NAME,
    )


def session_cookie_secure() -> bool:
    return True


def session_cookie_samesite() -> str:
    return current_app.config.get("CHECKER_SESSION_COOKIE_SAMESITE", "Lax")


def session_public_data(session_data: dict) -> dict:
    return {
        "user_id": session_data["user_id"],
        "username": session_data["username"],
    }


def delete_expired_sessions(now: datetime | None = None) -> None:
    if now is None:
        now = utc_now()

    with SESSION_STORE_LOCK:
        for session_key, session_data in list(SESSION_STORE.items()):
            if session_data["expires_at"] <= now:
                del SESSION_STORE[session_key]


def create_user_session(user_id: int, username: str) -> str:
    now = utc_now()
    delete_expired_sessions(now)
    expires_at = now + timedelta(seconds=session_timeout_seconds())
    session_data = {
        "user_id": user_id,
        "username": username,
        "created_at": now,
        "last_seen_at": now,
        "expires_at": expires_at,
    }

    while True:
        session_key = token_urlsafe(SESSION_KEY_BYTES)
        with SESSION_STORE_LOCK:
            if session_key not in SESSION_STORE:
                SESSION_STORE[session_key] = session_data
                return session_key


def get_active_session(session_key: str | None) -> dict | None:
    if not session_key:
        return None

    now = utc_now()
    expires_at = now + timedelta(seconds=session_timeout_seconds())
    with SESSION_STORE_LOCK:
        session_data = SESSION_STORE.get(session_key)
        if session_data is None:
            return None

        if session_data["expires_at"] <= now:
            del SESSION_STORE[session_key]
            return None

        session_data["last_seen_at"] = now
        session_data["expires_at"] = expires_at
        return dict(session_data)


def delete_user_session(session_key: str | None) -> None:
    if not session_key:
        return

    with SESSION_STORE_LOCK:
        SESSION_STORE.pop(session_key, None)


def set_session_cookie(response, session_key: str):
    response.set_cookie(
        session_cookie_name(),
        session_key,
        max_age=session_timeout_seconds(),
        httponly=True,
        secure=session_cookie_secure(),
        samesite=session_cookie_samesite(),
        path="/",
    )
    return response


def clear_session_cookie(response):
    response.delete_cookie(
        session_cookie_name(),
        path="/",
    )
    return response


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


def missing_or_expired_session_response():
    return jsonify({
        "status": "unauthorized",
        "authorized": False,
        "errors": ["Missing or expired session"],
    }), 401


@bp.before_app_request
def load_checker_session():
    session_key = request.cookies.get(session_cookie_name())
    session_data = get_active_session(session_key)
    g.checker_session_key = session_key
    g.checker_user = session_data
    g.refresh_checker_session_cookie = session_data is not None


@bp.after_app_request
def refresh_checker_session_cookie(response):
    if getattr(g, "refresh_checker_session_cookie", False):
        set_session_cookie(response, g.checker_session_key)

    return response


def checker_login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.checker_user is None:
            return missing_or_expired_session_response()

        return view(**kwargs)

    return wrapped_view


@bp.route("/authorize", methods=("POST",))
def authorize_user():
    """Authorize a checker app user and create a server-side session."""
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

    delete_user_session(request.cookies.get(session_cookie_name()))
    session_key = create_user_session(user_id, username)
    g.refresh_checker_session_cookie = False
    response = jsonify({
        "status": "authorized",
        "authorized": True,
        "message": "User authorized.",
        "data": {
            "user_id": user_id,
            "username": username,
        },
    })
    return set_session_cookie(response, session_key)


@bp.route("/session", methods=("GET",))
@checker_login_required
def verify_user_session():
    """Verify the session cookie attached to the current request."""
    return jsonify({
        "status": "authorized",
        "authorized": True,
        "message": "Session is active.",
        "data": session_public_data(g.checker_user),
    })


@bp.route("/logout", methods=("POST",))
def logout_user():
    """Destroy the active checker app session and clear its cookie."""
    session_key = request.cookies.get(session_cookie_name())
    delete_user_session(session_key)
    g.checker_session_key = None
    g.checker_user = None
    g.refresh_checker_session_cookie = False

    response = jsonify({
        "status": "logged_out",
        "authorized": False,
        "message": "User logged out.",
    })
    return clear_session_cookie(response)
