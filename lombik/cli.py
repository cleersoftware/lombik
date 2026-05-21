from getpass import getpass
from pathlib import Path
import secrets
import shutil
import click


BASE_DIR = Path(__file__).parent

STARTUP_TEMPLATE = BASE_DIR / "templates" / "createapp"
MODULE_TEMPLATE = BASE_DIR / "templates" / "module"


@click.group()
def cli():
    pass

def is_text_file(path: Path) -> bool:
    try:
        path.read_text(encoding="utf-8")
        return True
    except UnicodeDecodeError:
        return False
    except Exception:
        return False


def replace_placeholders(target_dir, replacements):

    for file in Path(target_dir).rglob("*"):

        if not file.is_file():
            continue

        try:
            content = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for key, value in replacements.items():
            content = content.replace(key, value)

        file.write_text(content, encoding="utf-8")


@cli.command()
@click.argument("name")
def createapp(name):

    target = Path.cwd() / name

    replacements = {
        "{{SECRET_KEY}}": secrets.token_urlsafe(64),
        "{{CRKEY}}": secrets.token_urlsafe(64)
    }

    shutil.copytree(STARTUP_TEMPLATE, target)

    replace_placeholders(target, replacements)

    print(f"Created app: {name}")
    

@cli.command()
@click.argument("name")
def module(name):
    PROHIBITED_MODULE_NAMES = [
        "core",
        "auth",
        "settings"
    ]

    if name in PROHIBITED_MODULE_NAMES:
        print("This name is not allowed by default.")
        return

    current = Path.cwd()

    blueprints_dir = None

    for path in current.rglob("blueprints"):
        if path.is_dir():
            blueprints_dir = path
            break

    if not blueprints_dir:
        print("No blueprints folder found.")
        return

    module_path = blueprints_dir / name

    if module_path.exists():
        print(f"Module '{name}' already exists.")
        return

    replacements = {
        "{{ module_name }}": name
    }

    shutil.copytree(MODULE_TEMPLATE, module_path)

    replace_placeholders(module_path, replacements)

    print(f"Created module: {name}")


if __name__ == "__main__":
    cli()