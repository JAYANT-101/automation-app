import importlib.util
import sys
import types
from pathlib import Path

import pytest
from flask import Flask
from werkzeug.security import generate_password_hash


@pytest.fixture()
def user_authorization_module(monkeypatch):
    """Load user_authorization without importing real database dependencies."""
    web_app = types.ModuleType("web_app")
    web_app.__path__ = []

    data_utils = types.ModuleType("web_app.data_utils")
    data_utils.get_user_info = lambda username: []

    monkeypatch.setitem(sys.modules, "web_app", web_app)
    monkeypatch.setitem(sys.modules, "web_app.data_utils", data_utils)

    module_path = (
        Path(__file__).resolve().parents[1]
        / "web_app"
        / "user_authorization.py"
    )
    spec = importlib.util.spec_from_file_location("user_authorization", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def client(user_authorization_module):
    app = Flask(__name__)
    app.config.update(TESTING=True)
    app.register_blueprint(user_authorization_module.bp)
    return app.test_client()


def test_authorize_user_returns_user_data_for_valid_credentials(
        client,
        user_authorization_module,
        monkeypatch,
):
    seen_usernames = []
    password_hash = generate_password_hash("secret")

    def fake_get_user_info(username):
        seen_usernames.append(username)
        return [(12, username, password_hash, "2026-06-03")]

    monkeypatch.setattr(
        user_authorization_module,
        "get_user_info",
        fake_get_user_info,
    )

    response = client.post(
        "/users/authorize",
        json={
            "username": " checker ",
            "password": "secret",
        },
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "authorized",
        "authorized": True,
        "message": "User authorized.",
        "data": {
            "user_id": 12,
            "username": "checker",
        },
    }
    assert seen_usernames == ["checker"]


def test_authorize_user_rejects_wrong_password(
        client,
        user_authorization_module,
        monkeypatch,
):
    password_hash = generate_password_hash("secret")

    monkeypatch.setattr(
        user_authorization_module,
        "get_user_info",
        lambda username: [(12, username, password_hash, "2026-06-03")],
    )

    response = client.post(
        "/users/authorize",
        json={
            "username": "checker",
            "password": "wrong",
        },
    )

    assert response.status_code == 401
    assert response.get_json() == {
        "status": "unauthorized",
        "authorized": False,
        "errors": ["Invalid username or password"],
    }


def test_authorize_user_rejects_unknown_username(client):
    response = client.post(
        "/users/authorize",
        json={
            "username": "missing",
            "password": "secret",
        },
    )

    assert response.status_code == 401
    assert response.get_json() == {
        "status": "unauthorized",
        "authorized": False,
        "errors": ["Invalid username or password"],
    }


def test_authorize_user_rejects_non_json_body(client):
    response = client.post(
        "/users/authorize",
        data="not json",
        content_type="text/plain",
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "status": "error",
        "errors": ["Request body must be a JSON object"],
    }


def test_authorize_user_rejects_missing_password(client):
    response = client.post(
        "/users/authorize",
        json={
            "username": "checker",
        },
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "status": "error",
        "errors": ["password is required"],
    }


def test_authorize_user_rejects_empty_username(client):
    response = client.post(
        "/users/authorize",
        json={
            "username": " ",
            "password": "secret",
        },
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "status": "error",
        "errors": ["username cannot be empty"],
    }


def test_authorize_user_returns_error_when_database_lookup_fails(
        client,
        user_authorization_module,
        monkeypatch,
):
    def fake_get_user_info(username):
        raise Exception("database lookup failed")

    monkeypatch.setattr(
        user_authorization_module,
        "get_user_info",
        fake_get_user_info,
    )

    response = client.post(
        "/users/authorize",
        json={
            "username": "checker",
            "password": "secret",
        },
    )

    assert response.status_code == 500
    assert response.get_json() == {
        "status": "error",
        "errors": ["database lookup failed"],
    }
