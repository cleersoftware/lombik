from pathlib import Path
import subprocess
import secrets
import shutil
import re
import click


BASE_DIR = Path(__file__).parent

STARTUP_TEMPLATE = BASE_DIR / "templates" / "createapp"
MODULE_TEMPLATE = BASE_DIR / "templates" / "module"
MODULE_TEMPLATE_TEMPLATES = BASE_DIR / "templates" / "module_templates"
MODEL_TEMPLATE = BASE_DIR / "templates" / "model_templates" / "template.py"

PROHIBITED_MODULE_NAMES = {"core", "auth"}



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


# Pluralization support
IRREGULAR = {
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

    "sheep": "sheep",
    "deer": "deer",
    "fish": "fish",
    "series": "series",
    "species": "species",

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

    "hero": "heroes",
    "potato": "potatoes",
    "tomato": "tomatoes",
    "echo": "echoes",
    "torpedo": "torpedoes",
    "veto": "vetoes",

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

    if lower in IRREGULAR:
        result = IRREGULAR[lower]
        if word.istitle():
            return result.capitalize()
        if word.isupper():
            return result.upper()
        return result

    if lower.endswith("y") and len(lower) > 1 and lower[-2] not in "aeiou":
        return word[:-1] + "ies"

    if lower.endswith(("s", "x", "z", "ch", "sh")):
        return word + "es"

    if lower.endswith("o"):
        return word + "s"

    return word + "s"


def ensure_db_import(file_path: Path):
    """Add `from app import db` if not already present."""
    content = file_path.read_text()
    if "db.Column" in content and "from app import db" not in content:
        content = "from app import db\n" + content
        file_path.write_text(content)


def detect_primary_key_type(model_file: Path) -> str:
    """Return the SQLAlchemy column type of the primary key."""
    content = model_file.read_text()
    for line in content.splitlines():
        if "primary_key=True" in line and "db.Column" in line:
            match = re.search(r"db\.Column\(\s*([^,]+)", line)
            if match:
                return match.group(1).strip()
    return "db.String(36)"


def inject_foreign_key(
    file_path: Path,
    fk_column: str,
    parent_table: str,
    parent_field: str,
    unique: bool = False,
    pk_type: str = "db.String(36)",
):
    """Inject a foreign key column into the child model."""
    content = file_path.read_text()

    fk_line = (
        f"\n    {fk_column} = db.Column({pk_type}, "
        f'db.ForeignKey("{parent_table}.{parent_field}")'
        f"{', unique=True' if unique else ''}, index=True)\n"
    )

    if fk_column in content:
        return

    marker = "# <LOMBIK:COLUMNS>"
    if marker not in content:
        raise RuntimeError(f"Missing {marker} marker in {file_path.name}")

    content = content.replace(marker, marker + fk_line)
    file_path.write_text(content)


def inject_relationship(
    file_path: Path,
    attr: str,
    target: str,
    back_populates: str,
    many: bool,
    lazy: str = "select",
    secondary: str = None,
):
    """Inject a db.relationship into a model."""
    content = file_path.read_text()

    options = []
    if not many:
        options.append("uselist=False")
    options.append(f"lazy='{lazy}'")
    if secondary:
        options.insert(0, f"secondary=\"{secondary}\"")

    rel = (
        f"\n    {attr} = db.relationship(\"{target}\", "
        f"back_populates=\"{back_populates}\", {', '.join(options)})\n"
    )

    if f"{attr} =" in content:
        return

    marker = "# <LOMBIK:RELATIONSHIPS>"
    if marker not in content:
        raise RuntimeError(f"Missing {marker} marker in {file_path.name}")

    content = content.replace(marker, marker + rel)
    file_path.write_text(content)


def create_association_table(
    models_dir: Path,
    table_name: str,
    left_table: str,
    right_table: str,
    left_fk: str,
    right_fk: str,
):
    """Create a new association table model file (composite PK, no extra id)."""
    association_file = models_dir / f"{table_name}.py"
    if association_file.exists():
        return

    content = f'''from app import db


class {to_camel(table_name)}(db.Model):
    __tablename__ = "{table_name}"

    # Composite primary key
    {left_fk} = db.Column(db.String(36), db.ForeignKey("{left_table}.id"), primary_key=True)
    {right_fk} = db.Column(db.String(36), db.ForeignKey("{right_table}.id"), primary_key=True)

    # <LOMBIK:COLUMNS>
    # </LOMBIK:COLUMNS>

    # <LOMBIK:RELATIONSHIPS>
    # </LOMBIK:RELATIONSHIPS>
'''
    association_file.write_text(content)



@click.group()
@click.version_option(version="3.1.4", prog_name="lombik")
def cli():
    pass


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
        for line in init_file.read_text().splitlines():
            if line.startswith("from .") and " import " in line:
                cls = line.split(" import ")[1].strip()
                existing.append(cls)

    existing.append(class_name)

    def camel_to_snake(name: str) -> str:
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    models = [(camel_to_snake(plural(m)), m) for m in dict.fromkeys(existing)]

    update_models_init(init_file, models)

    print(f"Created model: {name}")


@cli.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("source", nargs=-1)
def relate(source):
    """
    Create relationships between models.

    Usage:
        lombik relate parent.field to child.field [relationship_type] [--lazy lazy_option]

    Relationship types: one-to-many (default), many-to-one, one-to-one, many-to-many
    Lazy options: select, joined, subquery, dynamic, noload, raise, ...
    """
    raw = " ".join(source)

    lazy = "select"
    if "--lazy" in raw:
        parts = raw.split("--lazy", 1)
        raw = parts[0].strip()
        lazy_part = parts[1].strip()
        lazy = lazy_part.split()[0] if lazy_part else lazy

    if " to " not in raw:
        print("Invalid format. Use: parent.field to child.field [type] [--lazy lazy]")
        return

    parent_raw, child_raw = raw.split(" to ", 1)
    parent_raw = parent_raw.strip()
    child_raw = child_raw.strip()

    parts = child_raw.split()
    rel_type = "one-to-many"
    if len(parts) > 1 and parts[-1] in {"one-to-many", "many-to-one", "one-to-one", "many-to-many"}:
        rel_type = parts[-1]
        child_raw = " ".join(parts[:-1])

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

    # For many-to-one, swap so that the first model is the "parent"
    if rel_type == "many-to-one":
        parent_file, child_file = child_file, parent_file
        parent_model, child_model = child_model, parent_model
        parent_class, child_class = child_class, parent_class
        parent_field, child_field = child_field, parent_field

    parent_table = plural(to_snake(parent_model))
    child_table = plural(to_snake(child_model))
    pk_type = detect_primary_key_type(parent_file)

    ensure_db_import(parent_file)
    ensure_db_import(child_file)

    if rel_type in ("one-to-many", "many-to-one"):
        fk_column = child_field
        parent_rel = plural(to_snake(child_model))
        child_rel = to_snake(parent_model)

        inject_foreign_key(child_file, fk_column, parent_table, parent_field, pk_type=pk_type)
        inject_relationship(child_file, child_rel, parent_class, back_populates=parent_rel, many=False, lazy=lazy)
        inject_relationship(parent_file, parent_rel, child_class, back_populates=child_rel, many=True, lazy=lazy)

    elif rel_type == "one-to-one":
        fk_column = child_field
        parent_rel = to_snake(child_model)
        child_rel = to_snake(parent_model)

        inject_foreign_key(child_file, fk_column, parent_table, parent_field, unique=True, pk_type=pk_type)
        inject_relationship(child_file, child_rel, parent_class, back_populates=parent_rel, many=False, lazy=lazy)
        inject_relationship(parent_file, parent_rel, child_class, back_populates=child_rel, many=False, lazy=lazy)

    elif rel_type == "many-to-many":
        assoc_table_name = f"{parent_table}_{child_table}"
        left_fk = f"{to_snake(parent_model)}_id"
        right_fk = f"{to_snake(child_model)}_id"

        create_association_table(models_dir, assoc_table_name, parent_table, child_table, left_fk, right_fk)

        assoc_class = to_camel(assoc_table_name)
        init_file = models_dir / "__init__.py"
        existing_models = []
        if init_file.exists():
            for line in init_file.read_text().splitlines():
                if line.startswith("from .") and " import " in line:
                    cls = line.split(" import ")[1].strip()
                    module_name = line.split(" ")[1].replace(".", "")
                    existing_models.append((module_name, cls))
        existing_models.append((assoc_table_name, assoc_class))
        update_models_init(init_file, existing_models)

        parent_rel = plural(to_snake(child_model))
        child_rel = plural(to_snake(parent_model))

        inject_relationship(
            parent_file, parent_rel, child_class,
            back_populates=child_rel, many=True, lazy=lazy, secondary=assoc_table_name
        )
        inject_relationship(
            child_file, child_rel, parent_class,
            back_populates=parent_rel, many=True, lazy=lazy, secondary=assoc_table_name
        )

    print(f"Linked {parent_model} ↔ {child_model} ({rel_type}) with lazy='{lazy}'")


@cli.command()
def superuser():
    subprocess.run(["flask", "superuser"], check=False)


@cli.command()
def initdb():
    subprocess.run(["flask", "initdb"], check=False)


@cli.command()
@click.option("-m", "--message", default="migration", help="Migration message")
def db(message):
    subprocess.run(["flask", "db", "migrate", "-m", message], check=True)
    subprocess.run(["flask", "db", "upgrade"], check=True)


@cli.command()
def run():
    subprocess.run(["flask", "run", "--debug"], check=False)


@cli.command()
def test():
    subprocess.run(["pytest"], check=False)


@cli.command()
def test_report():
    subprocess.run(["pytest", "--cov=.", "--cov-report=term-missing"], check=False)


@cli.command()
def test_report_html():
    subprocess.run(["pytest", "--cov=.", "--cov-report=html"], check=False)


if __name__ == "__main__":
    cli()