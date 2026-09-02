from . import auth_bp
from blueprints.auth.forms import *
from flask import render_template, request
from lombik.flash import Flash


@auth_bp.get("/login")
def login():
    context = {
        "selected": "login",
        "login_form": LoginForm(),
        "next": request.args.get("next", ""),
    }
    return render_template("auth/login.html", **context)


@auth_bp.get("/register")
def register():
    context = {
        "selected": "register",
        "register_form": RegisterForm(),
        "next": request.args.get("next", ""),
    }
    return render_template("auth/register.html", **context)


@auth_bp.get("/forgot_password")
def forgot_password_page():
    context = {
        "selected": "forgot_password"
    }
    return render_template("auth/forgot_password.html", **context)