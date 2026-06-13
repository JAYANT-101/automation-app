import importlib.util
import sys
import types
from io import BytesIO
from pathlib import Path

import pytest
from flask import Blueprint, Flask


class FakeDataFrame:
    def __init__(self, rows):
        self.rows = rows

    def itertuples(self, index=False):
        return iter(self.rows)


@pytest.fixture()
def po_module(monkeypatch):
    """Load po without importing real database, Excel, auth, or pandas dependencies."""
    web_app = types.ModuleType("web_app")
    web_app.__path__ = []

    auth = types.ModuleType("web_app.auth")
    auth.login_required = lambda view: view

    data_from_excl = types.ModuleType("web_app.data_from_excl")
    data_from_excl.extract_data = lambda saved_file: []

    data_utils = types.ModuleType("web_app.data_utils")
    data_utils.delete_po_by_number = lambda product_name, po_number: None
    data_utils.get_all_product_names = lambda: []
    data_utils.get_po_numbers_by_product = lambda product_name: []
    data_utils.is_po_in_table = lambda po_number: [(0,)]
    data_utils.is_product_in_table = lambda product_name: [(0,)]
    data_utils.insert_product = lambda product_name: None
    data_utils.insert_po = lambda product_name, po_number, target: None
    data_utils.show_po_data = lambda: []
    data_utils.update_po_target = lambda product_name, po_number, target: None

    pandas = types.ModuleType("pandas")
    pandas.DataFrame = FakeDataFrame

    monkeypatch.setitem(sys.modules, "web_app", web_app)
    monkeypatch.setitem(sys.modules, "web_app.auth", auth)
    monkeypatch.setitem(sys.modules, "web_app.data_from_excl", data_from_excl)
    monkeypatch.setitem(sys.modules, "web_app.data_utils", data_utils)
    monkeypatch.setitem(sys.modules, "pandas", pandas)

    module_path = Path(__file__).resolve().parents[1] / "web_app" / "po.py"
    spec = importlib.util.spec_from_file_location("po", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def app(po_module, tmp_path):
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
        PO_UPLOAD_FOLDER=tmp_path,
    )

    auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
    auth_bp.add_url_rule("/login", endpoint="login", view_func=lambda: "login")
    auth_bp.add_url_rule("/regester", endpoint="register", view_func=lambda: "register")
    app.register_blueprint(auth_bp)
    app.register_blueprint(po_module.bp)

    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_row_exists_handles_exists_query_results(po_module):
    assert po_module.row_exists([(1,)]) is True
    assert po_module.row_exists([(0,)]) is False
    assert po_module.row_exists([]) is False
    assert po_module.row_exists(None) is False


def test_allowed_file_only_accepts_xlsx(po_module):
    assert po_module.allowed_file("orders.xlsx") is True
    assert po_module.allowed_file("orders.XLSX") is True
    assert po_module.allowed_file("orders.csv") is False
    assert po_module.allowed_file("orders") is False


def test_data_entry_inserts_missing_products_and_pos(
        po_module,
        monkeypatch,
):
    inserted_products = []
    inserted_pos = []

    monkeypatch.setattr(po_module, "is_product_in_table", lambda product: [(0,)])
    monkeypatch.setattr(po_module, "is_po_in_table", lambda po_number: [(0,)])
    monkeypatch.setattr(po_module, "insert_product", inserted_products.append)
    monkeypatch.setattr(
        po_module,
        "insert_po",
        lambda product_name, po_number, target: inserted_pos.append(
            (product_name, po_number, target)
        ),
    )

    message = po_module.data_entry(
        [
            ("PO-001", "Shirt", 100),
            ("PO-002", "Pant", 50),
        ]
    )

    assert message == "2 po rows added"
    assert inserted_products == ["Shirt", "Pant"]
    assert inserted_pos == [
        ("Shirt", "PO-001", 100),
        ("Pant", "PO-002", 50),
    ]


def test_data_entry_skips_existing_product_and_po(
        po_module,
        monkeypatch,
):
    inserted_products = []
    inserted_pos = []

    monkeypatch.setattr(po_module, "is_product_in_table", lambda product: [(1,)])
    monkeypatch.setattr(po_module, "is_po_in_table", lambda po_number: [(1,)])
    monkeypatch.setattr(po_module, "insert_product", inserted_products.append)
    monkeypatch.setattr(
        po_module,
        "insert_po",
        lambda product_name, po_number, target: inserted_pos.append(
            (product_name, po_number, target)
        ),
    )

    message = po_module.data_entry([("PO-001", "Shirt", 100)])

    assert message == "0 po rows added"
    assert inserted_products == []
    assert inserted_pos == []


def test_upload_po_get_renders_existing_po_rows(
        client,
        po_module,
        monkeypatch,
):
    monkeypatch.setattr(
        po_module,
        "show_po_data",
        lambda: [("Shirt", "PO-001", 100)],
    )

    response = client.get("/po/upload_po")

    assert response.status_code == 200
    assert b"PO-001" in response.data
    assert b"Shirt" in response.data
    assert b"100" in response.data


def test_upload_po_rejects_wrong_file_type(client):
    response = client.post(
        "/po/upload_po",
        data={
            "file": (BytesIO(b"not an excel file"), "orders.csv"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"wrong file type" in response.data


def test_upload_po_extracts_data_and_saves_rows(
        client,
        po_module,
        monkeypatch,
):
    seen_saved_files = []

    def fake_extract_data(saved_file):
        seen_saved_files.append(saved_file)
        assert saved_file.exists()
        return [("PO-001", "Shirt", 100)]

    monkeypatch.setattr(po_module, "extract_data", fake_extract_data)
    monkeypatch.setattr(po_module, "data_entry", lambda po_data: "1 po rows added")

    response = client.post(
        "/po/upload_po",
        data={
            "file": (BytesIO(b"excel bytes"), "orders.xlsx"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert b"1 po rows added" in response.data
    assert len(seen_saved_files) == 1
    assert not seen_saved_files[0].exists()


def test_po_numbers_returns_product_po_numbers(
        client,
        po_module,
        monkeypatch,
):
    monkeypatch.setattr(
        po_module,
        "get_po_numbers_by_product",
        lambda product_name: [(1, "PO-001", 100), (2, "PO-002", 50)],
    )

    response = client.get("/po/po_numbers/Shirt")

    assert response.status_code == 200
    assert response.get_json() == {
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


def test_update_po_get_renders_products(
        client,
        po_module,
        monkeypatch,
):
    monkeypatch.setattr(po_module, "get_all_product_names", lambda: ["Shirt", "Pant"])

    response = client.get("/po/update_po")

    assert response.status_code == 200
    assert b"Shirt" in response.data
    assert b"Pant" in response.data


def test_update_po_updates_target(
        client,
        po_module,
        monkeypatch,
):
    updated_targets = []
    monkeypatch.setattr(
        po_module,
        "update_po_target",
        lambda product_name, po_number, target: updated_targets.append(
            (product_name, po_number, target)
        ),
    )

    response = client.post(
        "/po/update_po",
        data={
            "action": "update",
            "product_name": "Shirt",
            "po_number": "PO-001",
            "target": "125",
        },
    )

    assert response.status_code == 200
    assert b"Target updated for PO PO-001" in response.data
    assert updated_targets == [("Shirt", "PO-001", 125)]


def test_update_po_rejects_invalid_target(
        client,
        po_module,
        monkeypatch,
):
    updated_targets = []
    monkeypatch.setattr(
        po_module,
        "update_po_target",
        lambda product_name, po_number, target: updated_targets.append(
            (product_name, po_number, target)
        ),
    )

    response = client.post(
        "/po/update_po",
        data={
            "action": "update",
            "product_name": "Shirt",
            "po_number": "PO-001",
            "target": "abc",
        },
    )

    assert response.status_code == 200
    assert b"Target must be a valid number" in response.data
    assert updated_targets == []


def test_update_po_deletes_po(
        client,
        po_module,
        monkeypatch,
):
    deleted_pos = []
    monkeypatch.setattr(
        po_module,
        "delete_po_by_number",
        lambda product_name, po_number: deleted_pos.append((product_name, po_number)),
    )

    response = client.post(
        "/po/update_po",
        data={
            "action": "delete",
            "product_name": "Shirt",
            "po_number": "PO-001",
        },
    )

    assert response.status_code == 200
    assert b"PO PO-001 deleted" in response.data
    assert deleted_pos == [("Shirt", "PO-001")]


def test_update_po_requires_product_and_po_number(client):
    response = client.post(
        "/po/update_po",
        data={
            "action": "update",
            "product_name": "",
            "po_number": "",
            "target": "100",
        },
    )

    assert response.status_code == 200
    assert b"Select a product and PO number" in response.data


def test_update_po_requires_valid_action(client):
    response = client.post(
        "/po/update_po",
        data={
            "action": "unknown",
            "product_name": "Shirt",
            "po_number": "PO-001",
            "target": "100",
        },
    )

    assert response.status_code == 200
    assert b"Choose update or delete" in response.data
