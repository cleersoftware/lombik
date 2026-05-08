from pathlib import Path
import shutil
import click
import secrets


BASE_DIR = Path(__file__).parent
<<<<<<< HEAD
STARTUP_TEMPLATE = BASE_DIR / "templates" / "startup"
=======
STARTUP_TEMPLATE = BASE_DIR / "templates" / "createapp"
>>>>>>> rescue


@click.group()
def cli():
    pass


<<<<<<< HEAD
=======
def is_text_file(path: Path) -> bool:
    try:
        path.read_text(encoding="utf-8")
        return True
    except UnicodeDecodeError:
        return False
    except Exception:
        return False


>>>>>>> rescue
def replace_placeholders(target_dir, replacements):

    for file in Path(target_dir).rglob("*"):

<<<<<<< HEAD
        if file.is_file():

            content = file.read_text()

            for key, value in replacements.items():
                content = content.replace(key, value)

            file.write_text(content)
=======
        if not file.is_file():
            continue

        try:
            content = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for key, value in replacements.items():
            content = content.replace(key, value)

        file.write_text(content, encoding="utf-8")
>>>>>>> rescue


@cli.command()
@click.argument("name")
<<<<<<< HEAD
def startup(name):
=======
def createapp(name):
>>>>>>> rescue

    target = Path.cwd() / name

    replacements = {
        "{{SECRET_KEY}}": secrets.token_urlsafe(64),
        "{{CRKEY}}": secrets.token_urlsafe(64)
    }

    shutil.copytree(STARTUP_TEMPLATE, target)

    replace_placeholders(target, replacements)

    print(f"Created app: {name}")


if __name__ == "__main__":
    cli()