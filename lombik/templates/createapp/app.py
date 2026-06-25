from flask import Flask
from dotenv import load_dotenv
from config import config_dict

from lombik.filters import register_filters
from lombik.cli import initialize
from lombik.extensions import register_extensions
from lombik.modules import register_blueprints
from lombik.hooks import register_hooks
from lombik.meta import register_metadata
from lombik.errors import register_error_handlers
from models import register_models


load_dotenv()

def create_app(env="default"):
    app = Flask(__name__, subdomain_matching=False)
    register_models()

    _init_config(app, env)
    # initialize(app)

    register_blueprints(app)
    register_extensions(app)
    register_hooks(app)
    register_error_handlers(app)
    register_filters(app)
    register_metadata(app)


    return app

def _init_config(app, env):
    cfg = config_dict[env]()

    app.config.from_object(cfg)
    app.config.update(
        SECRET_KEY=cfg.SECRET_KEY,
        CACHE_TYPE=cfg.CACHE_TYPE,
        CACHE_DEFAULT_TIMEOUT=int(cfg.CACHE_DEFAULT_TIMEOUT),
    )

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)