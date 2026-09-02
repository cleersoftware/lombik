from pathlib import Path

import click
from flask.cli import with_appcontext
from getpass import getpass
from sqlalchemy import text

from db import db
from models import register_models
from lombik.auth import create_user
from lombik.triggers import create_all_triggers, drop_all_triggers

import subprocess
import os


def db_initialized():
    try:
        db.session.execute(text("SELECT 1 FROM users LIMIT 1"))
        return True
    except Exception:
        return False


def run_migrations():
    """Create/refresh the migrations directory and apply migrations."""
    migrations_dir = Path.cwd() / "migrations"

    if not (migrations_dir / "alembic.ini").exists():
        subprocess.run(["flask", "db", "init"], check=True)

    subprocess.run(["flask", "db", "migrate", "-m", "auto init"], check=True)
    subprocess.run(["flask", "db", "upgrade"], check=True)


def initialize_db(app):
    @app.cli.command("initdb")
    @with_appcontext
    def initdb():
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")

        # Only require MySQL credentials when the configured URI needs them.
        if db_uri.startswith("mysql"):
            required = [
                "DEV_MYSQL_USERNAME",
                "DEV_MYSQL_PASS",
                "DEV_MYSQL_HOST",
                "DEV_MYSQL_NAME",
            ]

            missing = [x for x in required if not os.getenv(x)]
            if missing:
                print(f"Missing env vars: {', '.join(missing)}")
                return

        try:
            run_migrations()
        except subprocess.CalledProcessError:
            print("Database initialization failed.")
            return

        try:
            create_all_triggers()
        except Exception as e:
            print(f"Trigger creation failed: {e}")
            return

        print("Database initialized.")


def create_superuser(app):
    @app.cli.command("superuser")
    @with_appcontext
    def superuser():

        if not db_initialized():
            print("Database not initialized. Initializing now...")

            try:
                run_migrations()
            except subprocess.CalledProcessError:
                print("Database initialization failed.")
                return

            print("Database ready.\n")

        register_models()

        email = input("Email: ").strip().lower()
        username = input("Username: ").strip().lower()
        country = input("Country: ").strip().lower()

        while True:
            pw = getpass("Password: ")
            pw2 = getpass("Again: ")
            if pw == pw2:
                break
            print("Passwords do not match")

        res = create_user(
            username=username,
            email=email,
            role="superuser",
            country=country,
            password=pw
        )

        if not res.success:
            print(f"Error: {res.message}")
            return

        print("\nSuperuser created successfully.")

        print("\nRun 'lombik run' to start the app on localhost:5000.")

        print("\nRun 'lombik module <module_name e.g.: admin>' to create new module inside your blueprints.")

        print("\nRun 'lombik model <model_name (singular) e.g: Tenant>' to create a new model and register it.")

        print("\nCreate relationships between models with a single command.")

        print("The main idea is: lombik relate parent.field to child.field [one-to-many|many-to-one|one-to-one|many-to-many] [--lazy LAZY]")
        print("Here is what that looks like in practice:")

        print("\nlombik relate tenant.id to user.tenant_id one-to-many")
        print("lombik relate user.tenant_id to tenant.id many-to-one")
        print("lombik relate tenant.id to setting.tenant_id one-to-one")
        print("lombik relate user.id to role.user_id many-to-many")


def register_triggers(app):
    @app.cli.command("triggers")
    @click.argument("action", required=False, default="create")
    @with_appcontext
    def triggers_cli(action):
        if action == "drop":
            drop_all_triggers()
            print("Dropped Lombik triggers.")
        else:
            create_all_triggers()
            print("Created Lombik triggers.")


def create_crud_command(app):
    @app.cli.command("crud")
    @click.argument("name")
    @with_appcontext
    def crud_cli(name):
        from lombik.crud import generate_crud

        result = generate_crud(name)
        if not result.get("ok"):
            print(result.get("error", "Could not generate CRUD."))
            return

        print(result.get("message"))
        print(f"  Blueprint:  blueprints/{result['module']}/")
        print(f"  Templates:  templates/{result['module']}/")
        print(f"  Routes:     /{result['module']}/")


def register_cli(app):
    initialize_db(app)
    create_superuser(app)
    register_triggers(app)
    create_crud_command(app)
