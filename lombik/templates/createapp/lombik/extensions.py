from flask_session import Session
from flask_wtf import CSRFProtect
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import g

from db import db, migrate
import os


cache = Cache()
csrf = CSRFProtect()
session = Session()


def rate_limit_key():
    if getattr(g, "user", None):
        return str(g.user.id)
    return get_remote_address()


limiter = Limiter(
    key_func=rate_limit_key,
    default_limits=["1000 per hour"],
    headers_enabled=True
)


def create_session_path(app):
    if app.config.get("SESSION_TYPE") == "filesystem":
        os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)


def register_extensions(app):
    cache.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)
    session.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    create_session_path(app)

    