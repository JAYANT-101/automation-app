import importlib.util
import sys
import types
from pathlib import Path

import pytest
from flask import Flask


@pytest.fixture()
def get_checkr_data_module(monkeypatch):
    """Load get_checkr_data without importing the app database dependencies."""
    web_app = types.ModuleType("web_app")
    web_app.__path__ = []

    data_utils = types.ModuleType("web_app.data_utils")
    data_utils.insert_checker_output = lambda **kwargs: None

    monkeypatch.setitem(sys.modules, "web_app", web_app)
    monkeypatch.setitem(sys.modules, "web_app.data_utils", data_utils)

    module_path = (
        Path(__file__).resolve().parents[1]
        / "web_app"
        / "get_checkr_data.py"
    )
    spec = importlib.util.spec_from_file_location("get_checkr_data", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def client(get_checkr_data_module):
    app = Flask(__name__)
    app.config.update(TESTING=True)
    app.register_blueprint(get_checkr_data_module.bp)
    return app.test_client()


def valid_checker_output_data():
    return {
        "user_id": 1,
        "line": 2,
        "po_id": 3,
        "field_name": "pass",
        "defect_name": "",
        "actual_event_time": "2026-05-09 10:30:00",
    }


def valid_alter_checker_output_data():
    data = valid_checker_output_data()
    data["field_name"] = "alter"
    data["defect_name"] = "scratch"
    return data


def test_checker_output_api_saves_pass_with_empty_defect_name(
        client,
        get_checkr_data_module,
        monkeypatch,
):
    saved_data = {}

    def fake_insert_checker_output(**kwargs):
        saved_data.update(kwargs)

    monkeypatch.setattr(
        get_checkr_data_module,
        "insert_checker_output",
        fake_insert_checker_output,
    )

    payload = valid_checker_output_data()
    response = client.post("/checker-output", json=payload)
    expected_data = {**payload, "defect_name": None}

    assert response.status_code == 201
    assert response.get_json() == {
        "status": "created",
        "message": "Checker output saved.",
        "data": expected_data,
    }
    assert saved_data == expected_data


def test_checker_output_api_saves_alter_with_defect_name(
        client,
        get_checkr_data_module,
        monkeypatch,
):
    saved_data = {}

    def fake_insert_checker_output(**kwargs):
        saved_data.update(kwargs)

    monkeypatch.setattr(
        get_checkr_data_module,
        "insert_checker_output",
        fake_insert_checker_output,
    )

    payload = valid_alter_checker_output_data()
    response = client.post("/checker-output", json=payload)

    assert response.status_code == 201
    assert response.get_json() == {
        "status": "created",
        "message": "Checker output saved.",
        "data": payload,
    }
    assert saved_data == payload


def test_checker_output_api_strips_string_fields(
        client,
        get_checkr_data_module,
        monkeypatch,
):
    saved_data = {}

    def fake_insert_checker_output(**kwargs):
        saved_data.update(kwargs)

    monkeypatch.setattr(
        get_checkr_data_module,
        "insert_checker_output",
        fake_insert_checker_output,
    )

    payload = valid_alter_checker_output_data()
    payload["field_name"] = " alter "
    payload["defect_name"] = " scratch "
    expected_data = {**payload, "field_name": "alter", "defect_name": "scratch"}

    response = client.post("/checker-output", json=payload)

    assert response.status_code == 201
    assert response.get_json() == {
        "status": "created",
        "message": "Checker output saved.",
        "data": expected_data,
    }
    assert saved_data == expected_data


def test_checker_output_api_rejects_non_json_body(client):
    response = client.post(
        "/checker-output",
        data="not json",
        content_type="text/plain",
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "status": "error",
        "errors": ["Request body must be a JSON object"],
    }


def test_checker_output_api_rejects_missing_required_field(client):
    payload = valid_checker_output_data()
    del payload["actual_event_time"]

    response = client.post("/checker-output", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {
        "status": "error",
        "errors": ["actual_event_time is required"],
    }


def test_checker_output_api_rejects_empty_defect_name_for_alter(client):
    payload = valid_alter_checker_output_data()
    payload["defect_name"] = "   "

    response = client.post("/checker-output", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {
        "status": "error",
        "errors": ["defect_name cannot be empty when field_name is alter"],
    }


def test_checker_output_api_rejects_missing_defect_name_for_alter(client):
    payload = valid_checker_output_data()
    payload["field_name"] = "alter"
    del payload["defect_name"]

    response = client.post("/checker-output", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {
        "status": "error",
        "errors": ["defect_name is required"],
    }


def test_checker_output_api_rejects_defect_name_for_pass(client):
    payload = valid_checker_output_data()
    payload["defect_name"] = "scratch"

    response = client.post("/checker-output", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {
        "status": "error",
        "errors": ["defect_name is only allowed when field_name is alter"],
    }


def test_checker_output_api_rejects_unknown_field_name(client):
    payload = valid_checker_output_data()
    payload["field_name"] = "unknown"

    response = client.post("/checker-output", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {
        "status": "error",
        "errors": ["field_name must be pass, reject, or alter"],
    }


def test_checker_output_api_rejects_wrong_field_type(client):
    payload = valid_checker_output_data()
    payload["user_id"] = "1"

    response = client.post("/checker-output", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {
        "status": "error",
        "errors": ["user_id must be int"],
    }


def test_checker_output_api_returns_error_when_insert_fails(
        client,
        get_checkr_data_module,
        monkeypatch,
):
    def fake_insert_checker_output(**kwargs):
        raise Exception("database insert failed")

    monkeypatch.setattr(
        get_checkr_data_module,
        "insert_checker_output",
        fake_insert_checker_output,
    )

    response = client.post("/checker-output", json=valid_alter_checker_output_data())

    assert response.status_code == 500
    assert response.get_json() == {
        "status": "error",
        "errors": ["database insert failed"],
    }
