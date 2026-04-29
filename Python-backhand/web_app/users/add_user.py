from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from web_app.auth import login_required
from web_app.data_utils import insert_user_in_users_table

bp = Blueprint('users', __name__, url_prefix='/users')

bp.route('/add_user', methods=('GET','POST'))
def add_user():
    """This function adds user that are going to be using the checker application on the app"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        if error is None:
            try:
                insert_user_in_users_table(username, generate_password_hash(password))
            except Exception as e:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))
        flash(error)
    return render_template('users.add_user')