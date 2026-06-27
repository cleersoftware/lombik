from . import auth_bp
from flask import request, redirect, url_for, session
from lombik.auth import authenticate_user, logout_user
from lombik.extensions import cache, limiter
from lombik.flash import Flash


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


@auth_bp.post("/logout")
def logout():
    res = logout_user()

    if not res.success:
        Flash.error("Logout failed")
        return redirect(url_for("core_bp.home"))

    Flash.ok("See you soon!")
    return redirect(url_for("auth_bp.login"))