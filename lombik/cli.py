from pathlib import Path
import secrets
import shutil
import click


BASE_DIR = Path(__file__).parent

STARTUP_TEMPLATE = BASE_DIR / "templates" / "createapp"
MODULE_TEMPLATE = BASE_DIR / "templates" / "module"
MODULE_TEMPLATE_TEMPLATES = BASE_DIR / "templates" / "module_templates"
MODEL_TEMPLATE = BASE_DIR / "templates" / "model_templates" / "template.py"

PROHIBITED_MODULE_NAMES = {"core", "auth", "admin"}


@click.group()
def cli():
    pass


def find_blueprints_dir() -> Path | None:
    current = Path.cwd()
    return next((p for p in current.rglob("blueprints") if p.is_dir()), None)


def to_snake(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def to_camel(name: str) -> str:
    return "".join(part.capitalize() for part in name.replace("-", "_").split("_"))


def format_str_list(items: list[str]) -> str:
    return ", ".join(f'"{i}"' for i in items)


def replace_placeholders(target_dir: Path, replacements: dict):
    for file in target_dir.rglob("*"):
        if not file.is_file():
            continue

        try:
            content = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for k, v in replacements.items():
            content = content.replace(k, v)

        file.write_text(content, encoding="utf-8")


def generate_from_template(template: Path, target: Path, replacements: dict):
    shutil.copytree(template, target)
    replace_placeholders(target, replacements)


@cli.command()
@click.argument("name")
def createapp(name):
    target = Path.cwd() / name

    replacements = {
        "{{SECRET_KEY}}": secrets.token_urlsafe(64),
        "{{CRKEY}}": secrets.token_urlsafe(64),
    }

    generate_from_template(STARTUP_TEMPLATE, target, replacements)

    print(f"Created app: {name}")


@cli.command()
@click.argument("name")
def module(name):
    if name in PROHIBITED_MODULE_NAMES:
        print("This name is not allowed.")
        return

    blueprints_dir = find_blueprints_dir()
    if not blueprints_dir:
        print("No blueprints folder found.")
        return

    project_root = blueprints_dir.parent

    module_path = blueprints_dir / name
    module_template_path = project_root / "templates" / name

    if module_path.exists():
        print(f"Module '{name}' already exists.")
        return

    module_template_path.parent.mkdir(exist_ok=True)

    replacements = {"{{ module_name }}": name}

    generate_from_template(MODULE_TEMPLATE, module_path, replacements)
    generate_from_template(MODULE_TEMPLATE_TEMPLATES, module_template_path, replacements)

    print(f"Created module: {name}")


def update_models_init(init_file: Path, models: list[tuple[str, str]]):
    """
    models = [(module_name, class_name), ...]
    """

    init_file.parent.mkdir(exist_ok=True)

    imports = "\n".join(
        f"from .{module} import {cls}"
        for module, cls in models
    )

    class_list = ", ".join(cls for _, cls in models)

    content = f"""{imports}


def register_models():
    \"\"\"
    Import all models in here to be supplied in app.py
    \"\"\"
    return [{class_list}]


__all__ = [{", ".join(f'"{cls}"' for _, cls in models)}]
"""

    init_file.write_text(content, encoding="utf-8")


@cli.command()
@click.argument("name")
def model(name):
    blueprints_dir = find_blueprints_dir()
    if not blueprints_dir:
        print("No project found.")
        return

    project_root = blueprints_dir.parent

    models_dir = project_root / "models"
    models_dir.mkdir(exist_ok=True)

    snake_name = to_snake(name)
    class_name = to_camel(name)

    model_file = models_dir / f"{snake_name}.py"
    init_file = models_dir / "__init__.py"

    if model_file.exists():
        print(f"Model '{name}' already exists.")
        return

    template = MODEL_TEMPLATE.read_text(encoding="utf-8")

    replacements = {
        "{{ model_name }}": snake_name,
        "{{ ModelName }}": class_name,
    }

    for k, v in replacements.items():
        template = template.replace(k, v)

    model_file.write_text(template, encoding="utf-8")

    existing = []

    if init_file.exists():
        # crude but safe parsing: re-use previous imports
        for line in init_file.read_text().splitlines():
            if line.startswith("from .") and " import " in line:
                mod = line.split(" import ")[1].strip()
                existing.append(mod)

    # add new model
    existing.append(class_name)

    # rebuild full module list
    def camel_to_snake(name: str) -> str:
        import re
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    models = [(camel_to_snake(m), m) for m in dict.fromkeys(existing)]

    update_models_init(init_file, models)

    print(f"Created model: {name}")


if __name__ == "__main__":
    cli()