import os
from web_app.data_from_csv import extract_data
from flask import (
    Blueprint, flash, redirect, render_template, request, url_for)
from web_app.auth import login_required
from web_app.data_utils import is_po_in_table, is_product_in_table, insert_product, insert_po, show_po_data
from werkzeug.utils import secure_filename
import pandas as df

def data_entry(po_data)->bool:
    """This fuction filters the po_data and puts it in the database"""
    for row in po_data.itertuples()-> str:
        _, po_number, product_name, target = row
        try:
            if is_product_in_table(product_name):
                continue
            else:
                insert_product(product_name)
            if is_po_in_table(po_number):
                continue
            else:
                insert_po(product_name, po_number, target)
        except Exception e:
            error = str(e)
        else:
            error = "data added"
    return error

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
                error = data_entry(po_data)
            except Exception as e:
                error = str(e)
    data =
    flash(error)
    return render_template('po.upload_po', data)