from flask.cli import with_appcontext
from lombik.auth import create_user
from models import register_models
from flask import session, g
from getpass import getpass
from sqlalchemy import text
from db import db
import subprocess
import os

def db_initialized():
    try:
        db.session.execute(text("SELECT 1 FROM users LIMIT 1"))
        return True
    except Exception:
        return False


def initialize_db(app):
    @app.cli.command("initdb")
    @with_appcontext
    def initdb():
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

        subprocess.run(["flask", "db", "init"])
        subprocess.run(["flask", "db", "migrate", "-m", "auto init"])
        subprocess.run(["flask", "db", "upgrade"])

        print("Database initialized.")


def create_superuser(app):
    @app.cli.command("superuser")
    @with_appcontext
    def superuser():

        if not db_initialized():
            print("Database not initialized. Initializing now...")

            subprocess.run(["flask", "db", "upgrade"], check=True)

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

        print("\nRun 'lombik module <module_name eg.: admin>' to create new module inside your bluerpints.")

        print("\nRun 'lombik model <model_name (singular) e.g: Tenant>' to create a new model and register it.")

        print("\nCreate relationships between models with a single command.")

        print("The meain idea is: lombik relate parent.field to child.field [one-to-many|many-to-one|one-to-one|many-to-many] [--lazy LAZY]")
        print("Here is what that looks like in practice:")

        print("\nlombik relate tenant.id to user.tenant_id one-to-many")
        print("lombik relate user.tenant_id to tenant.id many-to-one")
        print("lombik relate tenant.id to setting.tenant_id one-to-one")
        print("lombik relate user.id to role.user_id many-to-many")

def register_cli(app):
    initialize_db(app)
    create_superuser(app)