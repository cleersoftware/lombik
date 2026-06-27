from flask import Flask
from dotenv import load_dotenv

from lombik.configuration import register_config
from lombik.filters import register_filters
from lombik.commands import register_cli
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

    register_config(app, env)
    register_cli(app)
    register_blueprints(app)
    register_extensions(app)
    register_hooks(app)
    register_error_handlers(app)
    register_filters(app)
    register_metadata(app)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)