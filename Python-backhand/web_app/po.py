from pathlib import Path
from web_app.data_from_excl import extract_data
from web_app.auth import login_required
from flask import (
    Blueprint, current_app, flash, render_template, request)
from web_app.data_utils import is_po_in_table, is_product_in_table, insert_product, insert_po, show_po_data
from werkzeug.utils import secure_filename
import pandas as pd

UPLOAD_FOLDER = Path(__file__).resolve().parent / "po_excl"


def row_exists(query_result) -> bool:
    """DB EXISTS queries return rows like [(0,)] or [(1,)]."""
    return bool(query_result and query_result[0][0])

def data_entry(po_data)->str|None:
    """This function filters the po_data and puts it in the database"""
    df = pd.DataFrame(po_data)
    error = None
    added_rows = 0
    for row in df.itertuples(index=False):
        po_number, product_name, target = row
        try:
            if not row_exists(is_product_in_table(product_name)):
                insert_product(product_name)

            if not row_exists(is_po_in_table(po_number)):
                insert_po(product_name, po_number, target)
                added_rows += 1
        except Exception as e:
            error = str(e)
            break
    if error is None:
        error = f"{added_rows} po rows added"
    return error

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
                error = data_entry(po_data)
            except Exception as e:
                error = str(e)
            finally:
                if saved_file and saved_file.exists():
                    saved_file.unlink()
        flash(error)
    return render_template('po/upload_po.html', data=show_po_data())

# @bp.route("update_po")