from flask import Blueprint, render_template

from web_app.auth import login_required
from web_app.data_utils import show_po_details

bp = Blueprint("po_details", __name__, url_prefix="/po")


@bp.route("/details")
@login_required
def po_details():
    """Show all PO rows with running/completed status."""
    rows = []
    for product_name, po_number, target, produced in show_po_details():
        is_completed = produced >= target
        rows.append({
            "product_name": product_name,
            "po_number": po_number,
            "target": target,
            "status": "Completed" if is_completed else "Running",
            "status_class": "text-bg-success" if is_completed else "text-bg-primary",
        })

    return render_template("po_details/details.html", rows=rows)
