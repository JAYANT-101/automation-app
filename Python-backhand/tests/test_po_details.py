import importlib.util
import sys
import types
from pathlib import Path

import pytest
from flask import Blueprint, Flask, g


@pytest.fixture()
def po_details_module(monkeypatch):
    """Load po_details without importing real database or auth dependencies."""
    web_app = types.ModuleType("web_app")
    web_app.__path__ = []

    auth = types.ModuleType("web_app.auth")
    auth.login_required = lambda view: view

    data_utils = types.ModuleType("web_app.data_utils")
    data_utils.show_po_details = lambda: []

    monkeypatch.setitem(sys.modules, "web_app", web_app)
    monkeypatch.setitem(sys.modules, "web_app.auth", auth)
    monkeypatch.setitem(sys.modules, "web_app.data_utils", data_utils)

    module_path = Path(__file__).resolve().parents[1] / "web_app" / "po_details.py"
    spec = importlib.util.spec_from_file_location("po_details", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def app(po_details_module):
    template_folder = Path(__file__).resolve().parents[1] / "web_app" / "templates"
    static_folder = Path(__file__).resolve().parents[1] / "web_app" / "static"

    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder,
    )
    app.config.update(SECRET_KEY="test-secret", TESTING=True)

    @app.before_request
    def load_admin():
        g.admin = [(1, "Admin")]

    auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
    auth_bp.add_url_rule("/login", endpoint="login", view_func=lambda: "login")
    auth_bp.add_url_rule("/logout", endpoint="logout", view_func=lambda: "logout")
    app.register_blueprint(auth_bp)

    po_bp = Blueprint("po", __name__, url_prefix="/po")
    po_bp.add_url_rule("/upload_po", endpoint="upload_po", view_func=lambda: "upload")
    app.register_blueprint(po_bp)

    app.add_url_rule("/update_po", endpoint="update_po", view_func=lambda: "update")

    checkers_bp = Blueprint("checkers_output", __name__, url_prefix="/checkers-output")
    checkers_bp.add_url_rule("/", endpoint="dashboard", view_func=lambda: "dashboard")
    app.register_blueprint(checkers_bp)

    users_bp = Blueprint("users", __name__, url_prefix="/users")
    users_bp.add_url_rule("/add", endpoint="add_user", view_func=lambda: "add")
    users_bp.add_url_rule("/delete", endpoint="delete_user", view_func=lambda: "delete")
    app.register_blueprint(users_bp)

    app.add_url_rule("/", endpoint="front", view_func=lambda: "front")
    app.register_blueprint(po_details_module.bp)

    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_po_details_shows_running_and_completed_statuses(
        client,
        po_details_module,
        monkeypatch,
):
    monkeypatch.setattr(
        po_details_module,
        "show_po_details",
        lambda: [
            ("Shirt", "PO-001", 100, 25),
            ("Pant", "PO-002", 50, 50),
        ],
    )

    response = client.get("/po/details")

    assert response.status_code == 200
    assert b"PO Details" in response.data
    assert b"Shirt" in response.data
    assert b"PO-001" in response.data
    assert b"Running" in response.data
    assert b"text-bg-primary" in response.data
    assert b"Pant" in response.data
    assert b"PO-002" in response.data
    assert b"Completed" in response.data
    assert b"text-bg-success" in response.data
    assert b'href="/po/details"' in response.data
