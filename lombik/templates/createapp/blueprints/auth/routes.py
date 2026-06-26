from flask import render_template, redirect, url_for, request, Blueprint, flash, session
from lombik.auth import authenticate_user
from lombik.extensions import limiter
from lombik.flash import Flash
from . import auth_bp



@auth_bp.get("/login")
def login():
    context = {
        "selected": "login"
    }
    return render_template("auth/login.html", **context)


@auth_bp.post("/logout")
def logout():
    session.clear()
    Flash.chat("Bye bye!")
    return redirect(url_for("auth_bp.login"))