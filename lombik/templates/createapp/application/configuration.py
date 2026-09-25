from datetime import timedelta
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY")

    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is missing")

    CRKEY = os.getenv("CRKEY")

    PERMANENT_SESSION_LIFETIME = timedelta(days=365)
    SESSION_TYPE = "filesystem"
    SESSION_USE_SIGNER = True
    SESSION_FILE_DIR = os.path.join(os.getcwd(), "flask_session")

    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300

    RATELIMIT_STORAGE_URI = "memory://"

    WTF_CSRF_TIME_LIMIT = 3 * 60 * 60

    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ConfigProd(BaseConfig):
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")


class ConfigTest(BaseConfig):
    SESSION_COOKIE_SECURE = False
    # Local development falls back to SQLite when no DATABASE_URL is set.
    SQLALCHEMY_DATABASE_URI = (
        os.getenv("DATABASE_URL") or f"sqlite:///{ROOT / 'dev.db'}"
    )


config_dict = {
    "prod": ConfigProd,
    "test": ConfigTest,
    "default": ConfigTest,
}


def register_config(app, env):
    cfg = config_dict[env]()

    app.config.from_object(cfg)
    app.config.update(
        SECRET_KEY=cfg.SECRET_KEY
    )
