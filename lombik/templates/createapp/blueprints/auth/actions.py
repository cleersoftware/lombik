from . import auth_bp
from flask import request, redirect, url_for, session
from lombik.auth import authenticate_user
from lombik.extensions import limiter
from lombik.flash import Flash
from db import db


@auth_bp.post("/login/authenticate")
@limiter.limit("10 per minute")
def authenticate():
    res = authenticate_user(
        email=request.form.get("email", "").strip().lower(),
        password=request.form.get("password", "")
    )

    if not res.success:
        Flash.error(res.message)
        return redirect(url_for("auth_bp.login"))

    session["user_id"] = res.data["user_id"]
    Flash.chat("Welcome!")
    return redirect(url_for("core_bp.home"))