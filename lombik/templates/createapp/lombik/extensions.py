from flask_session import Session
from flask_wtf import CSRFProtect
from db import db, migrate
import os

def create_session_path(app):
    if app.config.get("SESSION_TYPE") == "filesystem":
        os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)

def register_extensions(app):
    create_session_path(app)
    Session(app)
    CSRFProtect(app)
    db.init_app(app)
    migrate.init_app(app, db)