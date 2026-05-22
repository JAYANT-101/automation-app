import importlib.util
import sys
import types
from pathlib import Path

import pytest
from flask import Flask
from werkzeug.security import check_password_hash, generate_password_hash


@pytest.fixture()
def fake_data_utils(monkeypatch):
    web_app = types.ModuleType("web_app")
    web_app.__path__ = []

    data_utils = types.ModuleType("web_app.data_utils")
    data_utils.insert_admin_in_admin_table = lambda username, password: None
    data_utils.get_admin_info = lambda username: []
    data_utils.get_admin_info_by_id = lambda admin_id: []

    monkeypatch.setitem(sys.modules, "web_app", web_app)
    monkeypatch.setitem(sys.modules, "web_app.data_utils", data_utils)

    return data_utils


@pytest.fixture()
def auth_module(fake_data_utils):
    module_path = Path(__file__).resolve().parents[1] / "web_app" / "auth.py"
    spec = importlib.util.spec_from_file_location("auth", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def app(auth_module):
    template_folder = Path(__file__).resolve().parents[1] / "web_app" / "templates"
    static_folder = Path(__file__).resolve().parents[1] / "web_app" / "static"

    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder,
    )
    app.config.update(
        SECRET_KEY="test-secret",
        TESTING=True,
    )
    app.register_blueprint(auth_module.bp)
    app.add_url_rule("/", endpoint="front", view_func=lambda: "front")
    app.add_url_rule("/index", endpoint="index", view_func=lambda: "index")

    @app.route("/protected")
    @auth_module.login_required
    def protected():
        return "protected"

    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_register_get_renders_form(client):
    response = client.get("/auth/regester")

    assert response.status_code == 200
    assert b"Register" in response.data


def test_register_inserts_hashed_password_and_redirects(
        client,
        auth_module,
        monkeypatch,
):
    saved_admin = {}

    def fake_insert_admin(username, password):
        saved_admin["username"] = username
        saved_admin["password"] = password

    monkeypatch.setattr(
        auth_module,
        "insert_admin_in_admin_table",
        fake_insert_admin,
    )

    response = client.post(
        "/auth/regester",
        data={
            "username": "admin",
            "password": "secret",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    assert saved_admin["username"] == "admin"
    assert saved_admin["password"] != "secret"
    assert check_password_hash(saved_admin["password"], "secret")


def test_register_shows_error_when_username_exists(
        client,
        auth_module,
        monkeypatch,
):
    def fake_insert_admin(username, password):
        raise Exception("duplicate username")

    monkeypatch.setattr(
        auth_module,
        "insert_admin_in_admin_table",
        fake_insert_admin,
    )

    response = client.post(
        "/auth/regester",
        data={
            "username": "admin",
            "password": "secret",
        },
    )

    assert response.status_code == 200
    assert b"User admin is already registered." in response.data


def test_login_get_renders_form(client):
    response = client.get("/auth/login")

    assert response.status_code == 200
    assert b"Log In" in response.data


def test_login_sets_session_and_redirects_to_front(
        client,
        auth_module,
        monkeypatch,
):
    password_hash = generate_password_hash("secret")

    monkeypatch.setattr(
        auth_module,
        "get_admin_info",
        lambda username: [(7, username, password_hash, "2026-05-15")],
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "admin",
            "password": "secret",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    with client.session_transaction() as session:
        assert session["admin_id"] == 7


def test_login_shows_error_for_unknown_username(
        client,
        auth_module,
        monkeypatch,
):
    monkeypatch.setattr(auth_module, "get_admin_info", lambda username: [])

    response = client.post(
        "/auth/login",
        data={
            "username": "missing",
            "password": "secret",
        },
    )

    assert response.status_code == 200
    assert b"Incorrect username." in response.data

    with client.session_transaction() as session:
        assert "admin_id" not in session


def test_login_shows_error_for_wrong_password(
        client,
        auth_module,
        monkeypatch,
):
    password_hash = generate_password_hash("correct-password")

    monkeypatch.setattr(
        auth_module,
        "get_admin_info",
        lambda username: [(7, username, password_hash, "2026-05-15")],
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "admin",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 200
    assert b"Incorrect password." in response.data

    with client.session_transaction() as session:
        assert "admin_id" not in session


def test_load_logged_in_user_sets_admin_on_g(
        client,
        auth_module,
        monkeypatch,
):
    monkeypatch.setattr(
        auth_module,
        "get_admin_info_by_id",
        lambda admin_id: [(admin_id, "admin", "hash", "2026-05-15")],
    )

    with client.session_transaction() as session:
        session["admin_id"] = 7

    response = client.get("/protected")

    assert response.status_code == 200
    assert response.data == b"protected"


def test_login_required_redirects_anonymous_user(client):
    response = client.get("/protected")

    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"


def test_logout_clears_session_and_redirects_to_index(client):
    with client.session_transaction() as session:
        session["admin_id"] = 7

    response = client.get("/auth/logout")

    assert response.status_code == 302
    assert response.headers["Location"] == "/index"

    with client.session_transaction() as session:
        assert "admin_id" not in session