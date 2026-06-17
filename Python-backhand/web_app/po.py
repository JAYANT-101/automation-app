from pathlib import Path
from web_app.data_from_excl import extract_data
from web_app.auth import login_required
from flask import (
    Blueprint, current_app, flash, jsonify, render_template, request)
from web_app.data_utils import (
    delete_po_by_number,
    get_all_product_names,
    get_po_numbers_by_product,
    is_po_in_table,
    is_product_in_table,
    insert_product,
    insert_po,
    update_po_target,
)
from werkzeug.utils import secure_filename
import pandas as pd

UPLOAD_FOLDER = Path(__file__).resolve().parent / "po_excl"


def row_exists(query_result) -> bool:
    """DB EXISTS queries return rows like [(0,)] or [(1,)]."""
    return bool(query_result and query_result[0][0])

def data_entry(po_data)->str|None:
    """This function filters the po_data and puts it in the database"""
    message, _ = insert_new_po_data(po_data)
    return message

def insert_new_po_data(po_data)->tuple[str|None, list[tuple]]:
    """Insert only new PO rows and return the rows added to the database."""
    df = pd.DataFrame(po_data)
    error = None
    added_rows = []
    for row in df.itertuples(index=False):
        po_number, product_name, target = row
        try:
            if not row_exists(is_product_in_table(product_name)):
                insert_product(product_name)

            if not row_exists(is_po_in_table(po_number)):
                insert_po(product_name, po_number, target)
                added_rows.append((product_name, po_number, target))
        except Exception as e:
            error = str(e)
            break
    if error is None:
        error = f"{len(added_rows)} po rows added"
    return error, added_rows

ALLOWED_EXTENSION = {'xlsx'}

def allowed_file(filename: str)-> bool:
    """This function checks of the file type is csv"""
    return '.' in filename and \
           filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSION

bp = Blueprint("po", __name__ , url_prefix="/po")

@bp.route("/upload_po", methods=('GET', 'POST'))
@login_required
def upload_po():
    """This function takes po_file """
    data = None
    if request.method == 'POST':
        file = request.files.get('file')
        error = 'wrong file type'
        if file and allowed_file(file.filename):
            saved_file = None
            try:
                filename = secure_filename(file.filename)
                upload_folder = Path(current_app.config.get("PO_UPLOAD_FOLDER", UPLOAD_FOLDER))
                upload_folder.mkdir(parents=True, exist_ok=True)
                saved_file = upload_folder / filename
                file.save(saved_file)
                po_data = extract_data(saved_file)
                error, data = insert_new_po_data(po_data)
            except Exception as e:
                error = str(e)
            finally:
                if saved_file and saved_file.exists():
                    saved_file.unlink()
        flash(error)
    return render_template('po/upload_po.html', data=data)

@bp.route("/po_numbers/<path:product_name>")
@login_required
def po_numbers(product_name):
    """Return PO numbers for the selected product."""
    po_rows = get_po_numbers_by_product(product_name)
    return jsonify({
        "po_numbers": [
            {"po_number": po_number, "target": target}
            for _, po_number, target, _ in po_rows
        ]
    })

@bp.route("/update_po", methods=('GET', 'POST'))
@login_required
def update_po():
    """Update target or delete a selected PO number."""
    if request.method == 'POST':
        action = request.form.get('action')
        product_name = request.form.get('product_name')
        po_number = request.form.get('po_number')
        target = request.form.get('target')

        if not product_name or not po_number:
            flash("Select a product and PO number")
        elif action == "delete":
            delete_po_by_number(product_name, po_number)
            flash(f"PO {po_number} deleted")
        elif action == "update":
            try:
                update_po_target(product_name, po_number, int(target))
                flash(f"Target updated for PO {po_number}")
            except (TypeError, ValueError):
                flash("Target must be a valid number")
        else:
            flash("Choose update or delete")

    return render_template(
        'po/update_po.html',
        products=get_all_product_names(),
    )
