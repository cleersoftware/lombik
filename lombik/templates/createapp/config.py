from datetime import timedelta
import os

class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY")

    # Fail fast instead of silently breaking later
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is missing")

    CRKEY = os.getenv("CRKEY")

    PERMANENT_SESSION_LIFETIME = timedelta(days=365)
    SESSION_TYPE = "filesystem"
    SESSION_USE_SIGNER = True
    SESSION_FILE_DIR = os.path.join(os.getcwd(), "flask_session")

    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300

    WTF_CSRF_TIME_LIMIT = 3 * 60 * 60

    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ConfigProd(BaseConfig):
    SESSION_COOKIE_SECURE = True

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('PROD_MYSQL_USERNAME')}:"
        f"{os.getenv('PROD_MYSQL_PASS')}@"
        f"{os.getenv('PROD_MYSQL_HOST')}/"
        f"{os.getenv('PROD_MYSQL_NAME')}"
    )


class ConfigTest(BaseConfig):
    SESSION_COOKIE_SECURE = False
    CACHE_DEFAULT_TIMEOUT = 60

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DEV_MYSQL_USERNAME')}:"
        f"{os.getenv('DEV_MYSQL_PASS')}@"
        f"{os.getenv('DEV_MYSQL_HOST')}/"
        f"{os.getenv('DEV_MYSQL_NAME')}"
    )


config_dict = {
    "prod": ConfigProd,
    "test": ConfigTest,
    "default": ConfigTest
}