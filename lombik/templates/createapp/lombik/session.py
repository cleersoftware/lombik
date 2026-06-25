import os

def _init_session_dir(app):
    if app.config.get("SESSION_TYPE") == "filesystem":
        os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)