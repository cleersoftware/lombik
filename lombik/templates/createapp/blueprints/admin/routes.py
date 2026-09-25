from flask import g, redirect, render_template, request, session, url_for

from . import admin_bp
from . import services
from application import themes
from application.auth import create_user
from application.flash import Flash
from application.utils import get_countries
from models import User


def _superuser_or_redirect():
    """Return a redirect if the visitor is not a logged-in superuser."""
    user = getattr(g, "user", None)

    if not user:
        Flash.error("Log in to access admin.")
        return redirect(url_for("auth_bp.login", next=request.path))

    if user.role != "superuser":
        Flash.error("Admin is only available to superusers.")
        return redirect(url_for("core_bp.home"))

    return None


# --------------------------------------------------------------------------- #
# First-run owner setup
# --------------------------------------------------------------------------- #
@admin_bp.get("/")
def index():
    if User.query.count() == 0:
        return render_template("admin/setup.html", countries=get_countries())

    guard = _superuser_or_redirect()
    if guard:
        return guard

    return render_template("admin/dashboard.html", selected="admin")


@admin_bp.post("/setup")
def complete_setup():
    if User.query.count() > 0:
        return redirect(url_for("admin_bp.index"))

    data = request.form

    if data.get("password") != data.get("confirm_password"):
        Flash.error("Passwords don't match!")
        return redirect(url_for("admin_bp.index"))

    res = create_user(
        username=data.get("username"),
        email=data.get("email"),
        role="superuser",
        password=data.get("password"),
        country=data.get("country"),
    )

    if not res.success:
        Flash.error(res.message)
        return redirect(url_for("admin_bp.index"))

    session.clear()
    session["user_id"] = res.data["user_id"]
    Flash.ok("Welcome! Your admin panel is ready.")
    return redirect(url_for("admin_bp.index"))


# --------------------------------------------------------------------------- #
# Live dashboard partials
# --------------------------------------------------------------------------- #
@admin_bp.get("/partials/stats")
def stats():
    guard = _superuser_or_redirect()
    if guard:
        return guard
    return render_template("admin/partials/stats.html", stats=services.error_stats())


@admin_bp.get("/partials/errors")
def errors():
    guard = _superuser_or_redirect()
    if guard:
        return guard
    return render_template("admin/partials/errors.html", errors=services.recent_errors())


@admin_bp.get("/partials/schema")
def schema():
    guard = _superuser_or_redirect()
    if guard:
        return guard
    return render_template("admin/partials/schema.html", tables=services.schema_tables())


# --------------------------------------------------------------------------- #
# Actions
# --------------------------------------------------------------------------- #
@admin_bp.post("/errors/clear")
def clear_errors():
    guard = _superuser_or_redirect()
    if guard:
        return guard

    count = services.clear_errors()
    Flash.ok(f"Cleared {count} error record(s).")
    return redirect(url_for("admin_bp.index"))


@admin_bp.post("/theme")
def update_theme():
    guard = _superuser_or_redirect()
    if guard:
        return guard

    name = request.form.get("theme", "")
    if themes.save_theme(name):
        Flash.ok("Theme updated.")
    else:
        Flash.error("Unknown theme.")

    return redirect(url_for("admin_bp.index"))
