from flask import Blueprint, render_template

from web_app.auth import login_required
from web_app.data_utils import show_checker_output_dashboard

bp = Blueprint("checkers_output", __name__, url_prefix="/checkers-output")


@bp.route("/")
@login_required
def dashboard():
    return render_template(
        "checkers_output/show_checkers_output.html",
        rows=show_checker_output_dashboard(),
    )
