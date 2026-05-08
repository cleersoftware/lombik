from pathlib import Path
import shutil
import click
import secrets


BASE_DIR = Path(__file__).parent
STARTUP_TEMPLATE = BASE_DIR / "templates" / "startup"


@click.group()
def cli():
    pass


def replace_placeholders(target_dir, replacements):

    for file in Path(target_dir).rglob("*"):

        if file.is_file():

            content = file.read_text()

            for key, value in replacements.items():
                content = content.replace(key, value)

            file.write_text(content)


@cli.command()
@click.argument("name")
def startup(name):

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