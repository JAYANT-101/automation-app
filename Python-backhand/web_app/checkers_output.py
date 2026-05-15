from flask import Blueprint, jsonify, render_template

from web_app.auth import login_required
from web_app.data_utils import show_checker_output_dashboard

bp = Blueprint("checkers_output", __name__, url_prefix="/checkers-output")


def serialize_dashboard_rows(rows):
    return [
        {
            "po_number": po_number,
            "product_name": product_name,
            "target": target,
            "produced": produced,
            "pass_count": pass_count,
            "reject_count": reject_count,
            "alter_count": alter_count,
        }
        for (
            po_number,
            product_name,
            target,
            produced,
            pass_count,
            reject_count,
            alter_count,
        ) in rows
    ]


@bp.route("/")
@login_required
def dashboard():
    return render_template(
        "checkers_output/show_checkers_output.html",
        rows=show_checker_output_dashboard(),
    )


@bp.route("/data")
@login_required
def dashboard_data():
    return jsonify(
        {
            "rows": serialize_dashboard_rows(show_checker_output_dashboard()),
        }
    )
