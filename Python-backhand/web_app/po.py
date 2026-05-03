import os
from web_app.data_from_csv import extract_data
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for)
from web_app.auth import login_required
# from web_app.data_utils import
from werkzeug.utils import secure_filename

ALLOWED_EXTENSION = {'csv'}

def allowed_file(filename: str)-> bool:
    """This function checks of the file type is csv"""
    return '.' in filename and \
           filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSION

bp = Blueprint("po", __name__ , url_prefix="/po")

@bp.route("/upload_po", method=('GET', 'POST'))
@login_required
def upload_po():
    """This function takes po_file """
    if request.method == 'POST':
        po_file = request.files['po_file']
        error = None
        if po_file and allowed_file(po_file.filename):
            try:
                filename = secure_filename(po_file.filename)
                po_file.save(os.path.join('po_excl', filename))
                po_data = extract_data(filename)

            except Exception as e:
                error = str(e)
                flash(error)
        return redirect(url_for('po.show_po'))
    return render_template('po.upload_po')