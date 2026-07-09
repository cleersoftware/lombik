from pathlib import Path
import subprocess   
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

    snake_name = to_snake(plural(name.lower()))
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

    models = [(camel_to_snake(plural(m)), m) for m in dict.fromkeys(existing)]

    update_models_init(init_file, models)

    print(f"Created model: {name}")


@cli.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("source", nargs=-1)
def relate(source):
    """
    usage:
        lombik relate user.id to client.user_id
    """

    raw = " ".join(source)

    if " to " not in raw:
        print("Invalid format. Use: user.id to client.user_id")
        return

    parent_raw, child_raw = raw.split(" to ", 1)
    parent_raw = parent_raw.strip()
    child_raw = child_raw.strip()

    try:
        parent_model, parent_field = parent_raw.split(".")
    except ValueError:
        parent_model, parent_field = parent_raw, "id"

    try:
        child_model, child_field = child_raw.split(".")
    except ValueError:
        child_model, child_field = child_raw, f"{parent_model}_id"

    blueprints_dir = find_blueprints_dir()
    if not blueprints_dir:
        print("No project found.")
        return

    project_root = blueprints_dir.parent
    models_dir = project_root / "models"

    parent_file = models_dir / f"{plural(to_snake(parent_model))}.py"
    child_file = models_dir / f"{plural(to_snake(child_model))}.py"

    if not parent_file.exists() or not child_file.exists():
        print("One or both models do not exist.")
        return

    parent_class = to_camel(parent_model)
    child_class = to_camel(child_model)

    fk_column = child_field

    parent_rel = plural(to_snake(child_model))
    child_rel = to_snake(parent_model)

    parent_table = plural(to_snake(parent_model))

    inject_foreign_key(
        child_file,
        fk_column=fk_column,
        parent_table=parent_table,
        parent_field=parent_field
    )

    inject_relationship(
        child_file,
        attr=child_rel,
        target=parent_class,
        back_populates=parent_rel,
        many=False
    )

    inject_relationship(
        parent_file,
        attr=parent_rel,
        target=child_class,
        back_populates=child_rel,
        many=True
    )

    print(f"Linked {parent_model} ↔ {child_model}")


@cli.command()
def superuser():
    subprocess.run(["flask superuser"], check=False)


@cli.command()
def initdb():
    subprocess.run(["flask initdb"], check=False)


@cli.command()
def test():
    subprocess.run(["pytest"], check=False)


@cli.command()
def test_report():
    subprocess.run(
        ["pytest", "--cov=.", "--cov-report=term-missing"],
        check=False
    )

@cli.command()
def test_report_html():
    subprocess.run(
        ["pytest", "--cov=.", "--cov-report=html"],
        check=False
    )

if __name__ == "__main__":
    cli()


def inject_foreign_key(file_path: Path, fk_column: str, parent_table: str, parent_field: str):
    content = file_path.read_text()

    fk_line = f"""
    {fk_column} = db.Column(
        db.String(36),
        db.ForeignKey("{parent_table}.{parent_field}"),
        index=True
    )
"""

    if fk_column in content:
        return  # already exists

    if "# <LOMBIK:COLUMNS>" in content:
        content = content.replace("# </LOMBIK:COLUMNS>", fk_line + "\n# </LOMBIK:COLUMNS>")
    else:
        # fallback: append inside class
        content = content.replace("class ", "class ", 1)  # noop safety
        content += fk_line

    file_path.write_text(content)


def inject_foreign_key(file_path: Path, fk_column: str, parent_table: str, parent_field: str):
    content = file_path.read_text()

    fk_line = f"""
    {fk_column} = db.Column(
        db.String(36),
        db.ForeignKey("{parent_table}.{parent_field}"),
        index=True
    )
"""

    if fk_column in content:
        return  # already exists

    if "# <LOMBIK:COLUMNS>" in content:
        content = content.replace("# </LOMBIK:COLUMNS>", fk_line + "\n# </LOMBIK:COLUMNS>")
    else:
        # fallback: append inside class
        content = content.replace("class ", "class ", 1)  # noop safety
        content += fk_line

    file_path.write_text(content)

def inject_relationship(file_path: Path, attr: str, target: str, back_populates: str, many: bool):
    content = file_path.read_text()

    rel = f"""
    {attr} = db.relationship(
        "{target}",
        back_populates="{back_populates}"{"," if many else ""}
        {"cascade='all, delete-orphan'" if many else ""}
    )
"""

    if f"{attr} =" in content:
        return

    if "# <LOMBIK:RELATIONSHIPS>" in content:
        content = content.replace(
            "# </LOMBIK:RELATIONSHIPS>",
            rel + "\n# </LOMBIK:RELATIONSHIPS>"
        )
    else:
        content += rel

    file_path.write_text(content)


def ensure_db_import(file_path: Path):
    content = file_path.read_text()

    if "db.Column" in content and "from app import db" not in content:
        content = "from app import db\n" + content
        file_path.write_text(content)

IRREGULAR = {
    # Completely irregular
    "child": "children",
    "person": "people",
    "man": "men",
    "woman": "women",
    "mouse": "mice",
    "goose": "geese",
    "tooth": "teeth",
    "foot": "feet",
    "ox": "oxen",
    "louse": "lice",

    # Doesn't change
    "sheep": "sheep",
    "deer": "deer",
    "fish": "fish",
    "series": "series",
    "species": "species",

    # -f / -fe exceptions
    "knife": "knives",
    "wife": "wives",
    "life": "lives",
    "leaf": "leaves",
    "wolf": "wolves",
    "calf": "calves",
    "half": "halves",
    "loaf": "loaves",
    "thief": "thieves",
    "shelf": "shelves",
    "self": "selves",
    "elf": "elves",

    # -o exceptions (take -es)
    "hero": "heroes",
    "potato": "potatoes",
    "tomato": "tomatoes",
    "echo": "echoes",
    "torpedo": "torpedoes",
    "veto": "vetoes",

    # -o exceptions (just add s)
    "photo": "photos",
    "piano": "pianos",
    "halo": "halos",
    "memo": "memos",
    "logo": "logos",
    "video": "videos",
    "studio": "studios",
}


def plural(word: str) -> str:
    """Return the plural form of an English noun."""

    if not word:
        return word

    lower = word.lower()

    # Preserve capitalization
    if lower in IRREGULAR:
        result = IRREGULAR[lower]
        if word.istitle():
            return result.capitalize()
        if word.isupper():
            return result.upper()
        return result

    # city -> cities
    if (
        lower.endswith("y")
        and len(lower) > 1
        and lower[-2] not in "aeiou"
    ):
        return word[:-1] + "ies"

    # bus -> buses, church -> churches, box -> boxes
    if lower.endswith(("s", "x", "z", "ch", "sh")):
        return word + "es"

    # default -o rule
    if lower.endswith("o"):
        return word + "s"

    # default
    return word + "s"