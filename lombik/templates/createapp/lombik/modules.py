from pathlib import Path
import importlib


def register_blueprints(app):
    base_path = Path(__file__).resolve().parent.parent
    blueprints_path = base_path / "blueprints"

    for blueprint_dir in blueprints_path.iterdir():

        if not blueprint_dir.is_dir():
            continue

        module_name = blueprint_dir.name  # core, settings, etc

        # import blueprint
        bp_module = importlib.import_module(f"blueprints.{module_name}")

        # import all route files AFTER blueprint exists
        for file in blueprint_dir.glob("*.py"):
            if file.name == "__init__.py":
                continue

            importlib.import_module(
                f"blueprints.{module_name}.{file.stem}"
            )

        # 3. register blueprint
        for attr in dir(bp_module):
            if not attr.endswith("_bp"):
                continue

            bp = getattr(bp_module, attr)

            name = bp.name.replace("_bp", "")
            url_prefix = "/" if name == "core" else f"/{name}"

            app.register_blueprint(bp, url_prefix=url_prefix)