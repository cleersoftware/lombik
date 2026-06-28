from . import auth_bp
from flask import request, redirect, url_for, session
from lombik.auth import authenticate_user, logout_user
from lombik.extensions import cache, limiter
from lombik.responses import htmx_response
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
        return htmx_response(
            html="",
            redirect=url_for("auth_bp.login")
        )

    session["user_id"] = res.data["user_id"]
    Flash.chat("Welcome!")
    return htmx_response(
        html="",
        redirect=url_for("admin_bp.admin")
    )


@auth_bp.post("/logout")
def logout():
    res = logout_user()

    if not res.success:
        Flash.error("Logout failed")
        return htmx_response(
            html="",
            redirect=url_for("core_bp.home")
        )

    Flash.ok("See you soon!")
    return htmx_response(
        html="",
        redirect=url_for("auth_bp.login")
    )