from datetime import date, datetime

from flask import Blueprint, jsonify, render_template, request

from web_app.auth import login_required
from web_app.data_utils import show_checker_output_dashboard

bp = Blueprint("checkers_output", __name__, url_prefix="/checkers-output")


def get_dashboard_filter():
    if request.args.get("view") == "all":
        return None, True

    selected_date = request.args.get("date", "").strip()

    if not selected_date:
        return None, True

    try:
        datetime.strptime(selected_date, "%Y-%m-%d")
    except ValueError:
        return None, True

    return selected_date, False


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
    selected_date, show_all = get_dashboard_filter()
    return render_template(
        "checkers_output/show_checkers_output.html",
        rows=show_checker_output_dashboard(selected_date),
        selected_date=selected_date or "",
        show_all=show_all,
        today_date=date.today().isoformat(),
    )


@bp.route("/data")
@login_required
def dashboard_data():
    selected_date, show_all = get_dashboard_filter()
    return jsonify(
        {
            "rows": serialize_dashboard_rows(show_checker_output_dashboard(selected_date)),
            "selected_date": selected_date,
            "show_all": show_all,
        }
    )
