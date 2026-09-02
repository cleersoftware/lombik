from . import auth_bp

from flask import request, url_for, session, redirect, render_template, g

from lombik.auth import (
    authenticate_user,
    create_user,
    logout_user,
    request_password_reset,
    validate_reset_token,
    reset_password,
)

from lombik.extensions import limiter
from lombik.flash import Flash
from lombik.mail import send_email
from lombik.responses import htmx_response
from lombik.users import get_user_by_id, mark_user_as_deleted


def _safe_next_url(value: str | None) -> str:
    """Only allow same-site relative redirects (prevents open redirects)."""
    if value and value.startswith("/") and not value.startswith("//"):
        return value
    return ""


@auth_bp.post("/login/authenticate")
@limiter.limit("10 per minute")
def authenticate():

    next_url = _safe_next_url(request.form.get("next")) or url_for("core_bp.home")

    res = authenticate_user(
        email=request.form.get("email", ""),
        password=request.form.get("password", ""),
    )

    if not res.success:
        Flash.error(res.message)

        return htmx_response(
            html="",
            redirect=url_for("auth_bp.login", next=next_url),
        )

    session.clear()
    session["user_id"] = res.data["user_id"]

    Flash.chat("Welcome!")

    return htmx_response(
        html="",
        redirect=next_url,
    )


@auth_bp.post("/register/user")
@limiter.limit("10 per minute")
def register_user():

    data = request.form

    next_url = _safe_next_url(data.get("next")) or url_for("core_bp.home")

    password = data.get("password")
    password_confirm = data.get("confirm_password")
    if password != password_confirm:
        Flash.error("Passwords don't match!")
        return htmx_response(
            html="",
            redirect=url_for("auth_bp.register"),
        )

    res = create_user(
        username=data.get("username"),
        email=data.get("email"),
        role="user",
        password=data.get("password"),
        country=data.get("country")
    )

    if not res.success:
        Flash.error(res.message)

        return htmx_response(
            html="",
            redirect=url_for("auth_bp.register"),
        )

    session.clear()
    session["user_id"] = res.data["user_id"]

    Flash.chat("Welcome!")

    return htmx_response(
        html="",
        redirect=next_url,
    )



@auth_bp.post("/forgot-password")
@limiter.limit("5 per minute")
def forgot_password():

    email = request.form.get("email", "")
    res = request_password_reset(email)

    if res.data:
        reset_url = url_for(
            "auth_bp.reset_user_password",
            user_id=res.data["user_id"],
            token=res.data["token"],
            _external=True,
        )

        send_email(
            to=res.data["email"],
            subject="Reset your password",
            html=render_template(
                "auth/emails/password_reset.html",
                url=reset_url,
            ),
        )

    Flash.ok(res.message)

    return redirect(
        url_for("auth_bp.login")
    )


@auth_bp.get("/reset-password/<user_id>/<token>")
def reset_password_page(user_id: str, token: str):

    user = get_user_by_id(id=user_id)

    res = validate_reset_token(
        user=user,
        token=token,
    )

    if not res.success:
        Flash.error(res.message)

        return redirect(
            url_for("auth_bp.login")
        )

    return render_template(
        "auth/reset_password.html",
        user_id=user_id,
        token=token,
    )


@auth_bp.post("/reset-password")
@limiter.limit("10 per minute")
def reset_user_password():

    user_id = request.form.get("user_id", "")
    token = request.form.get("token", "")
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if password != confirm_password:
        Flash.error("Passwords do not match.")

        return redirect(
            url_for(
                "auth_bp.reset_password_page",
                user_id=user_id,
                token=token,
            )
        )

    res = reset_password(
        user_id=user_id,
        token=token,
        new_password=password,
    )

    if not res.success:
        Flash.error(res.message)

        return redirect(
            url_for(
                "auth_bp.reset_password_page",
                user_id=user_id,
                token=token,
            )
        )

    Flash.ok(
        "Password reset successfully. You can now log in."
    )

    return redirect(
        url_for("auth_bp.login")
    )


@auth_bp.post("/delete_user")
def delete_user():

    if not getattr(g, "user", None):
        return "", 401

    res = mark_user_as_deleted(
        user_id_deleting=g.user.id,
        user_id_to_delete=request.form.get("user_id_to_delete"),
    )

    if not res.success:
        return "", 400

    return htmx_response(
        html="",
        trigger="usersChange",
    )


@auth_bp.post("/logout")
def logout():

    res = logout_user()

    if not res.success:
        Flash.error("Logout failed")

        return htmx_response(
            html="",
            redirect=url_for("core_bp.home"),
        )

    Flash.ok("See you soon!")

    return htmx_response(
        html="",
        redirect=url_for("auth_bp.login"),
    )