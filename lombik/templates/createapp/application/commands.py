from pathlib import Path

import click
from flask.cli import with_appcontext
from getpass import getpass
from sqlalchemy import text

from db import db
from models import register_models
from application.auth import create_user
from application.triggers import create_all_triggers, drop_all_triggers

import subprocess
import os
import sys


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
        subprocess.run([sys.executable, "-m", "flask", "db", "init"], check=True)

    subprocess.run([sys.executable, "-m", "flask", "db", "migrate", "-m", "auto init"], check=True)
    subprocess.run([sys.executable, "-m", "flask", "db", "upgrade"], check=True)


def initialize_db(app):
    @app.cli.command("initdb")
    @with_appcontext
    def initdb():
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")

        # Postgres (used by Railway and the bundled Docker setup) needs a URL.
        if db_uri.startswith("postgresql") and not os.getenv("DATABASE_URL"):
            print("Missing env var: DATABASE_URL")
            print("Set it in .env (local) or as a Railway service variable.")
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

        print("\nSuperuser created successfully.\n")
        print("Next steps:")
        print("  1. Run the app:      lombik run")
        print("  2. Open the admin:   http://localhost:5000/admin")
        print("  3. Add a module:     lombik module mymodule")
        print("  4. Add a model:      lombik model tenant")
        print("  5. Generate CRUD:    lombik crud tenant")
        print("  6. Create relations: lombik relate tenant.id to user.tenant_id one-to-many")
        print("  7. Migrate:          lombik db -m \"add tenants\"")
        print("\nTip: create the model, then run migrations, then generate CRUD.")


def register_triggers(app):
    @app.cli.command("triggers")
    @click.argument("action", required=False, default="create")
    @with_appcontext
    def triggers_cli(action):
        if action == "drop":
            drop_all_triggers()
            print("Dropped application triggers.")
        else:
            create_all_triggers()
            print("Created application triggers.")


def create_crud_command(app):
    @app.cli.command("crud")
    @click.argument("name")
    @with_appcontext
    def crud_cli(name):
        from application.crud import generate_crud

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
