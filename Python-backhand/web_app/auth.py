import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from web_app.data_utils import insert_admin_in_admin_table,get_admin_info,get_admin_info_by_id

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/regester', methods=('GET','POST'))
def register():
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
                insert_admin_in_admin_table(username, generate_password_hash(password))
            except Exception as e:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))
        flash(error)
    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        admin = get_admin_info(username)
        id, _, rpassword, _ = list(admin[0])

        if admin is None:
            error = 'Incorrect username.'
        elif not check_password_hash(rpassword, password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['admin_id'] = id
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    admin_id = session.get('admin_id')

    if admin_id is None:
        g.admin = None
    else:
        g.admin = get_admin_info_by_id(admin_id)

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.admin is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view