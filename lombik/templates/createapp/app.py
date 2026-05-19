from flask import Flask, g, session, render_template, send_from_directory, current_app
from flask.cli import with_appcontext
from flask_wtf.csrf import CSRFError
from flask_wtf import CSRFProtect
from flask_session import Session
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import time
import os

from db import db, migrate

from config import config_dict
from models import load_models

# import all your bleurpints here
from blueprints.core.routes import core_bp
from blueprints.auth.routes import auth_bp
from blueprints.settings.routes import settings_bp

load_dotenv()


def create_app(env="default"):
    app = Flask(__name__, subdomain_matching=False)
    
    load_models()
    # load models first otherwise fetch will never happen
    # also, stop trying to make fetch happen
    _user_management(app)

    _init_config(app, env)
    _init_extensions(app)
    _init_session_dir(app)
    _init_filters(app)
    _init_blueprints(app)
    _init_hooks(app)
    _init_routes(app)
    _init_error_handlers(app)
    
    return app


def _init_config(app, env):
    cfg = config_dict[env]()

    app.config.from_object(cfg)
    app.config.update(
        SECRET_KEY=cfg.SECRET_KEY,
        CACHE_TYPE=cfg.CACHE_TYPE,
        CACHE_DEFAULT_TIMEOUT=int(cfg.CACHE_DEFAULT_TIMEOUT),
    )

def _init_extensions(app):
    Session(app)
    CSRFProtect(app)
    db.init_app(app)
    migrate.init_app(app, db)
    

def _init_session_dir(app):
    if app.config.get("SESSION_TYPE") == "filesystem":
        os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)


def _init_blueprints(app):
    app.register_blueprint(core_bp, url_prefix="/")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(settings_bp, url_prefix="/settings")


def _init_hooks(app):
    #app.before_request(load_user)
    app.before_request(_csrf_lifetime_tracker)


def _csrf_lifetime_tracker():
    if "csrf_last_reset" not in session:
        session["csrf_last_reset"] = int(time.time())

    session["csrf_last_reset"] = int(time.time())

    g.csrf_time_left = current_app.config.get("WTF_CSRF_TIME_LIMIT", 3600)


"""
These are all the custom templating commands you can use with lombik.

As an example, timestamps in the db are stored as UTC.
By default, lombik will create the user in the g object with the user's timezone

Now to display the UTC timestamp to the user's local timestamp all you have to do is:

{{ created_at | localtime }}

And it convert UTC to user's local.

You can also do dateonly, which by default converts it to UTC and strips out the date.
There is more.

"""
def _init_filters(app):
    from markdown import markdown

    @app.template_filter("localtimezone")
    def localtimezone(dt):
        if not dt:
            return ""

        tz = "UTC"
        if hasattr(g, "user"):
            user_timezone = g.user.timezone

        return dt.astimezone(ZoneInfo(tz))


    def _fmt(dt, fmt):
        dt = localtimezone(dt)
        return dt.strftime(fmt) if dt else ""


    @app.template_filter("onlydate")
    def onlydate(dt):
        return _fmt(dt, "%Y-%m-%d")


    @app.template_filter("onlytime")
    def onlytime(dt):
        return _fmt(dt, "%H:%M")


    @app.template_filter("localtime")
    def localtime(dt):
        return _fmt(dt, "%Y-%m-%d %H:%M")


    @app.template_filter("shortdatetime")
    def shortdatetime(dt):
        return _fmt(dt, "%b %d %H:%M").lower()
    
    
    @app.template_filter("proper")
    def proper(s):
        return s.replace("_", " ").title()
    

    @app.template_filter("possessive")
    def possessive(s):
        if not s:
            return ""
        if s.lower().endswith("s"):
            return f"{s}'"
        return f"{s}'s"
    
    

def _init_routes(app):

    @app.route("/manifest.json")
    def manifest():
        return send_from_directory("static", "manifest.json")


def _init_error_handlers(app):

    @app.errorhandler(CSRFError)
    def csrf_error(e):
        return render_template("base/csrf_error.html"), 400


    @app.errorhandler(404)
    def not_found(e):
        return render_template("base/404.html"), 404
    

def _user_management(app):
    from blueprints.auth.services import load_user, create_user

    @app.before_request
    def fetch_user():
        user_id = session.get("user_id")

        if not user_id:
            g.user = None
            return

        user = load_user(user_id)

        if not user:
            g.user = None
            return

        g.user = user

    @app.cli.command("initdb")
    @with_appcontext
    def initdb():
        import subprocess

        required = [
            "DEV_MYSQL_USERNAME",
            "DEV_MYSQL_PASS",
            "DEV_MYSQL_HOST",
            "DEV_MYSQL_NAME"
        ]

        missing = [x for x in required if not os.getenv(x)]
        if missing:
            print(f"Missing env vars: {', '.join(missing)}")
            return
        
        subprocess.run(["flask", "db", "init"])
        subprocess.run(["flask", "db", "migrate", "-m", "auto init"])
        subprocess.run(["flask", "db", "upgrade"])
        print("Database initialized.")

    @app.cli.command("superuser")
    @with_appcontext
    def superuser():
        from getpass import getpass
        import os

        print("Starting application...")

        load_models()

        email = input("Email: ").lower().strip()
        username = input("Username: ").lower().strip()

        while True:
            password = getpass("Password: ")
            password_confirm = getpass("Again: ")

            if password == password_confirm:
                break
            print("Passwords do not match")

        res = create_user(
            username=username,
            email=email,
            role="owner",
            password=password
        )

        if not res.success:
            print(f"Error: {res.message}")
            return

        print("\nSuperuser created successfully.")
        print("Run: flask run --debug")
