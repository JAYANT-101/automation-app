import importlib.util
import sys
import types
from pathlib import Path

import pytest
from flask import Flask


@pytest.fixture()
def checkers_output_module(monkeypatch):
    """Load checkers_output without importing app database dependencies."""
    web_app = types.ModuleType("web_app")
    web_app.__path__ = []

    auth = types.ModuleType("web_app.auth")
    auth.login_required = lambda view: view

    data_utils = types.ModuleType("web_app.data_utils")
    data_utils.show_checker_output_dashboard = lambda: []

    monkeypatch.setitem(sys.modules, "web_app", web_app)
    monkeypatch.setitem(sys.modules, "web_app.auth", auth)
    monkeypatch.setitem(sys.modules, "web_app.data_utils", data_utils)

    module_path = (
        Path(__file__).resolve().parents[1]
        / "web_app"
        / "checkers_output.py"
    )
    spec = importlib.util.spec_from_file_location("checkers_output", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def client(checkers_output_module):
    app = Flask(__name__)
    app.config.update(TESTING=True)
    app.register_blueprint(checkers_output_module.bp)
    return app.test_client()


def test_dashboard_data_returns_serialized_rows(
        client,
        checkers_output_module,
        monkeypatch,
):
    monkeypatch.setattr(
        checkers_output_module,
        "show_checker_output_dashboard",
        lambda: [
            ("PO-001", "Shirt", 3, 1, 2),
            ("PO-002", "Pant", 0, 0, 0),
        ],
    )

    response = client.get("/checkers-output/data")

    assert response.status_code == 200
    assert response.get_json() == {
        "rows": [
            {
                "po_number": "PO-001",
                "product_name": "Shirt",
                "pass_count": 3,
                "reject_count": 1,
                "alter_count": 2,
            },
            {
                "po_number": "PO-002",
                "product_name": "Pant",
                "pass_count": 0,
                "reject_count": 0,
                "alter_count": 0,
            },
        ],
    }


def test_dashboard_data_fetches_latest_rows_each_request(
        client,
        checkers_output_module,
        monkeypatch,
):
    dashboard_snapshots = [
        [("PO-001", "Shirt", 1, 0, 0)],
        [("PO-001", "Shirt", 2, 0, 1)],
    ]

    def fake_show_checker_output_dashboard():
        return dashboard_snapshots.pop(0)

    monkeypatch.setattr(
        checkers_output_module,
        "show_checker_output_dashboard",
        fake_show_checker_output_dashboard,
    )

    first_response = client.get("/checkers-output/data")
    second_response = client.get("/checkers-output/data")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.get_json()["rows"][0] == {
        "po_number": "PO-001",
        "product_name": "Shirt",
        "pass_count": 1,
        "reject_count": 0,
        "alter_count": 0,
    }
    assert second_response.get_json()["rows"][0] == {
        "po_number": "PO-001",
        "product_name": "Shirt",
        "pass_count": 2,
        "reject_count": 0,
        "alter_count": 1,
    }


def test_serialize_dashboard_rows_returns_empty_list(checkers_output_module):
    assert checkers_output_module.serialize_dashboard_rows([]) == []
