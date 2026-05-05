from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
bp = Blueprint('index', __name__)

@bp.route('/')
def index():
    a = "dalde ab iser"
    return render_template('front.html',a=a)