from flask import Flask
from dotenv import load_dotenv

load_dotenv()

from application import STARTED_AT
from application.configuration import register_config
from application.themes import register_themes
from application.commands import register_cli
from application.filters import register_filters
from application.extensions import register_extensions
from application.modules import register_blueprints
from application.hooks import register_hooks
from application.meta import register_metadata
from application.errors import register_error_handlers
from models import register_models


def create_app(env="default"):
    app = Flask(__name__, subdomain_matching=False)

    @app.context_processor
    def _inject_started_at():
        return {"app_started_at": STARTED_AT}

    register_models()
    register_config(app, env)
    register_cli(app)
    register_themes(app)
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