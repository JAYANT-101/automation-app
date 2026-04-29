from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from web_app.auth import login_required
from web_app.data_utils import insert_user_in_users_table, get_all_users_data, delete_user_by_username

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
bp.route('/show_users')
def show_users():
    try:
        users = get_all_users_data()
    except Exception as e:
        flash(str(e))
    data = [name for _,name,*_ in users]
    return render_template('users.show_users', data=data)

bp.route('/delete_user')
def delete_user(username: str):
    if request.method == 'POST':
        username = request.form['username']
        error = None
        if not username:
            error = 'Username is required.'
        if error is None:
            try:
                delete_user_by_username(username)
            except Exception as e:
                error = f"User {username} dose not exist"
        flash(error)
    return render_template('users.delete_user')