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
        print("\nRun 'flask run --debug' to start the app on localhost:5000.")


def register_cli(app):
    initialize_db(app)
    create_superuser(app)