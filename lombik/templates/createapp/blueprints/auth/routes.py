from . import auth_bp
from blueprints.auth.forms import *
from flask import render_template, redirect, url_for, session
from lombik.flash import Flash


@auth_bp.get("/login")
def login():
    context = {
        "selected": "login",
        "LoginForm": LoginForm()
    }
    return render_template("auth/login.html", **context)
