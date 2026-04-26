import os
from dotenv import load_dotenv
from flask import Flask
from . import db
from . import auth

load_dotenv()
def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # a simple page that says hello
    @app.route('/')
    def hello():
        return 'getting things started'

    #This initialized thr database
    db.init_app(app)

    #This registers the blueprint of the auth
    app.register_blueprint(auth.bp)

    return app