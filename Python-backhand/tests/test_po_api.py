import importlib.util
import sys
import types
from pathlib import Path

import pytest
from flask import Flask


@pytest.fixture()
def po_api_module(monkeypatch):
    """Load po_api without importing real database dependencies."""
    web_app = types.ModuleType("web_app")
    web_app.__path__ = []

    data_utils = types.ModuleType("web_app.data_utils")
    data_utils.get_all_product_names = lambda: []
    data_utils.get_po_numbers_by_product = lambda product_type: []

    monkeypatch.setitem(sys.modules, "web_app", web_app)
    monkeypatch.setitem(sys.modules, "web_app.data_utils", data_utils)

    module_path = Path(__file__).resolve().parents[1] / "web_app" / "po_api.py"
    spec = importlib.util.spec_from_file_location("po_api", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def client(po_api_module):
    app = Flask(__name__)
    app.config.update(TESTING=True)
    app.register_blueprint(po_api_module.bp)
    return app.test_client()


def test_product_types_returns_only_product_types(
        client,
        po_api_module,
        monkeypatch,
):
    monkeypatch.setattr(
        po_api_module,
        "get_all_product_names",
        lambda: ["Shirt", "Pant"],
    )

    response = client.get("/api/po/product-types")

    assert response.status_code == 200
    assert response.get_json() == {
        "product_types": ["Shirt", "Pant"],
    }


def test_po_numbers_returns_selected_product_type_pos(
        client,
        po_api_module,
        monkeypatch,
):
    seen_product_types = []

    def fake_get_po_numbers_by_product(product_type):
        seen_product_types.append(product_type)
        return [("PO-001", 100), ("PO-002", 50)]

    monkeypatch.setattr(
        po_api_module,
        "get_po_numbers_by_product",
        fake_get_po_numbers_by_product,
    )

    response = client.get("/api/po/po-numbers?product_type=Shirt")

    assert response.status_code == 200
    assert response.get_json() == {
        "product_type": "Shirt",
        "po_numbers": [
            {
                "po_number": "PO-001",
                "target": 100,
            },
            {
                "po_number": "PO-002",
                "target": 50,
            },
        ],
    }
    assert seen_product_types == ["Shirt"]


def test_po_numbers_requires_product_type(client):
    response = client.get("/api/po/po-numbers")

    assert response.status_code == 400
    assert response.get_json() == {
        "errors": ["product_type is required"],
    }


def test_product_types_returns_database_errors(
        client,
        po_api_module,
        monkeypatch,
):
    def fake_get_all_product_names():
        raise Exception("database failed")

    monkeypatch.setattr(
        po_api_module,
        "get_all_product_names",
        fake_get_all_product_names,
    )

    response = client.get("/api/po/product-types")

    assert response.status_code == 500
    assert response.get_json() == {
        "errors": ["database failed"],
    }


def test_po_numbers_returns_database_errors(
        client,
        po_api_module,
        monkeypatch,
):
    def fake_get_po_numbers_by_product(product_type):
        raise Exception("database failed")

    monkeypatch.setattr(
        po_api_module,
        "get_po_numbers_by_product",
        fake_get_po_numbers_by_product,
    )

    response = client.get("/api/po/po-numbers?product_type=Shirt")

    assert response.status_code == 500
    assert response.get_json() == {
        "errors": ["database failed"],
    }
