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
    data_utils.get_all_po_defect_counts = lambda selected_date=None: []
    data_utils.get_po_defect_counts = lambda po_number, selected_date=None: []
    data_utils.show_checker_output_dashboard = lambda selected_date=None: []

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
        lambda selected_date=None: [
            ("PO-001", "Shirt", 100, 99, 3, 1, 2),
            ("PO-002", "Pant", 50, 7, 0, 0, 0),
        ],
    )
    monkeypatch.setattr(
        checkers_output_module,
        "get_all_po_defect_counts",
        lambda selected_date=None: [
            ("Broken Stitch", 4),
            ("Oil Mark", 2),
            ("Shade Issue", 1),
            ("Loose Thread", 1),
        ],
    )

    response = client.get("/checkers-output/data")

    assert response.status_code == 200
    assert response.get_json() == {
        "rows": [
            {
                "po_number": "PO-001",
                "product_name": "Shirt",
                "target": 100,
                "total_processed": 6,
                "pass_count": 3,
                "reject_count": 1,
                "alter_count": 2,
                "defect_details_url": "/checkers-output/defects/PO-001?view=all",
            },
            {
                "po_number": "PO-002",
                "product_name": "Pant",
                "target": 50,
                "total_processed": 0,
                "pass_count": 0,
                "reject_count": 0,
                "alter_count": 0,
                "defect_details_url": "/checkers-output/defects/PO-002?view=all",
            },
        ],
        "status_totals": {
            "total_processed": 6,
            "defect_percentage": 33.33,
            "pass_count": 3,
            "reject_count": 1,
            "alter_count": 2,
        },
        "chart_labels": ["Broken Stitch", "Oil Mark", "Shade Issue"],
        "chart_counts": [4, 2, 1],
        "selected_date": None,
        "show_all": True,
    }


def test_dashboard_data_fetches_latest_rows_each_request(
        client,
        checkers_output_module,
        monkeypatch,
):
    dashboard_snapshots = [
        [("PO-001", "Shirt", 100, 99, 1, 0, 0)],
        [("PO-001", "Shirt", 100, 42, 2, 0, 1)],
    ]

    def fake_show_checker_output_dashboard(selected_date=None):
        return dashboard_snapshots.pop(0)

    monkeypatch.setattr(
        checkers_output_module,
        "show_checker_output_dashboard",
        fake_show_checker_output_dashboard,
    )
    monkeypatch.setattr(
        checkers_output_module,
        "get_all_po_defect_counts",
        lambda selected_date=None: [("Broken Stitch", 1)],
    )

    first_response = client.get("/checkers-output/data")
    second_response = client.get("/checkers-output/data")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.get_json()["rows"][0] == {
        "po_number": "PO-001",
        "product_name": "Shirt",
        "target": 100,
        "total_processed": 1,
        "pass_count": 1,
        "reject_count": 0,
        "alter_count": 0,
        "defect_details_url": "/checkers-output/defects/PO-001?view=all",
    }
    assert first_response.get_json()["status_totals"] == {
        "total_processed": 1,
        "defect_percentage": 0.0,
        "pass_count": 1,
        "reject_count": 0,
        "alter_count": 0,
    }
    assert second_response.get_json()["rows"][0] == {
        "po_number": "PO-001",
        "product_name": "Shirt",
        "target": 100,
        "total_processed": 3,
        "pass_count": 2,
        "reject_count": 0,
        "alter_count": 1,
        "defect_details_url": "/checkers-output/defects/PO-001?view=all",
    }
    assert second_response.get_json()["status_totals"] == {
        "total_processed": 3,
        "defect_percentage": 33.33,
        "pass_count": 2,
        "reject_count": 0,
        "alter_count": 1,
    }


def test_serialize_dashboard_rows_returns_empty_list(client, checkers_output_module):
    with client.application.test_request_context("/checkers-output/data"):
        assert checkers_output_module.serialize_dashboard_rows([]) == []


def test_calculate_status_totals(checkers_output_module):
    assert checkers_output_module.calculate_status_totals([
        ("PO-001", "Shirt", 100, 99, 3, 1, 2),
        ("PO-002", "Pant", 50, 42, 1, 2, 1),
    ]) == {
        "total_processed": 10,
        "defect_percentage": 30.0,
        "pass_count": 4,
        "reject_count": 3,
        "alter_count": 3,
    }


def test_calculate_status_totals_handles_zero_processed(checkers_output_module):
    assert checkers_output_module.calculate_status_totals([
        ("PO-001", "Shirt", 100, 99, 0, 0, 0),
    ]) == {
        "total_processed": 0,
        "defect_percentage": 0,
        "pass_count": 0,
        "reject_count": 0,
        "alter_count": 0,
    }


def test_prepare_top_defects_chart_limits_to_top_three(checkers_output_module):
    assert checkers_output_module.prepare_top_defects_chart([
        ("Loose Thread", 1),
        ("Broken Stitch", 4),
        ("Oil Mark", 2),
        ("Shade Issue", 3),
    ]) == {
        "chart_labels": ["Broken Stitch", "Shade Issue", "Oil Mark"],
        "chart_counts": [4, 3, 2],
    }


def test_dashboard_data_includes_line_numbers_for_date_filter(
        client,
        checkers_output_module,
        monkeypatch,
):
    monkeypatch.setattr(
        checkers_output_module,
        "show_checker_output_dashboard",
        lambda selected_date=None: [
            ("PO-001", "Shirt", 100, 1, 3, 1, 2),
            ("PO-001", "Shirt", 100, 2, 2, 0, 1),
            ("PO-002", "Pant", 50, 1, 1, 0, 0),
        ],
    )
    monkeypatch.setattr(
        checkers_output_module,
        "get_all_po_defect_counts",
        lambda selected_date=None: [("Broken Stitch", 3)],
    )

    response = client.get("/checkers-output/data?date=2026-06-17")

    assert response.status_code == 200
    assert response.get_json() == {
        "rows": [
            {
                "line_no": 1,
                "po_number": "PO-001",
                "product_name": "Shirt",
                "target": 100,
                "total_processed": 6,
                "pass_count": 3,
                "reject_count": 1,
                "alter_count": 2,
                "defect_details_url": "/checkers-output/defects/PO-001?date=2026-06-17&line=1",
            },
            {
                "line_no": 2,
                "po_number": "PO-001",
                "product_name": "Shirt",
                "target": 100,
                "total_processed": 3,
                "pass_count": 2,
                "reject_count": 0,
                "alter_count": 1,
                "defect_details_url": "/checkers-output/defects/PO-001?date=2026-06-17&line=2",
            },
            {
                "line_no": 1,
                "po_number": "PO-002",
                "product_name": "Pant",
                "target": 50,
                "total_processed": 1,
                "pass_count": 1,
                "reject_count": 0,
                "alter_count": 0,
                "defect_details_url": "/checkers-output/defects/PO-002?date=2026-06-17&line=1",
            },
        ],
        "status_totals": {
            "total_processed": 10,
            "defect_percentage": 30.0,
            "pass_count": 6,
            "reject_count": 1,
            "alter_count": 3,
        },
        "chart_labels": ["Broken Stitch"],
        "chart_counts": [3],
        "selected_date": "2026-06-17",
        "show_all": False,
    }


def test_prepare_defect_dashboard_groups_rows_by_line(checkers_output_module):
    assert checkers_output_module.prepare_defect_dashboard([
        ("Shirt", "PO-001", 1, "Broken Stitch", 2),
        ("Shirt", "PO-001", 1, "Oil Mark", 1),
        ("Shirt", "PO-001", 2, "Broken Stitch", 1),
    ], show_line=True) == {
        "defect_names": ["Broken Stitch", "Oil Mark"],
        "table_rows": [
            {
                "product_name": "Shirt",
                "po_number": "PO-001",
                "line_no": 1,
                "defects": {"Broken Stitch": 2, "Oil Mark": 1},
            },
            {
                "product_name": "Shirt",
                "po_number": "PO-001",
                "line_no": 2,
                "defects": {"Broken Stitch": 1},
            },
        ],
        "chart_labels": ["Broken Stitch", "Oil Mark"],
        "chart_counts": [3, 1],
    }
