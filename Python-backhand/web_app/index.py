from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
bp = Blueprint('index', __name__)

@bp.route('/')
def index():
    a = "sexy website"
    return render_template('front.html',a=a)