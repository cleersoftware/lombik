from pathlib import Path

from flask import g, redirect, render_template, request, session, url_for

from . import admin_bp
from . import services
from application import themes
from application.auth import create_user
from application.flash import Flash
from application.utils import get_countries
from models import User

GUIDE_PATH = Path(__file__).resolve().parents[2] / "application" / "guide.md"


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

    return render_template(
        "admin/errors.html",
        selected="admin",
        active="errors",
        daily=services.error_series_daily(),
        hourly=services.error_series_hourly(),
    )


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
# Pages
# --------------------------------------------------------------------------- #
@admin_bp.get("/schema")
def schema():
    guard = _superuser_or_redirect()
    if guard:
        return guard
    return render_template("admin/schema.html", selected="admin", active="schema", tables=services.schema_tables())


@admin_bp.get("/appearance")
def appearance():
    guard = _superuser_or_redirect()
    if guard:
        return guard

    active = themes.get_active_theme()
    available = themes.available_themes()
    return render_template(
        "admin/appearance.html",
        selected="admin",
        active="appearance",
        active_theme=themes.active_theme_id(),
        available_themes=available,
        custom_ids=[t["id"] for t in available if themes.is_custom(t["id"])],
        theme_tokens=themes.TOKENS,
        active_palette=active,
    )


@admin_bp.get("/guide")
def guide():
    guard = _superuser_or_redirect()
    if guard:
        return guard

    guide_html = ""
    try:
        guide_html = GUIDE_PATH.read_text(encoding="utf-8")
    except OSError:
        guide_html = "# Guide\n\nGuide content could not be loaded."

    return render_template("admin/guide.html", selected="admin", active="guide", guide_html=guide_html)


# --------------------------------------------------------------------------- #
# Live partials
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
        Flash.ok("Theme activated.")
    else:
        Flash.error("Unknown theme.")

    return redirect(url_for("admin_bp.appearance"))


@admin_bp.post("/themes")
def create_theme():
    guard = _superuser_or_redirect()
    if guard:
        return guard

    name = request.form.get("name", "")
    light = {token: request.form.get(f"light_{token}", "") for token in themes.TOKENS}
    dark = {token: request.form.get(f"dark_{token}", "") for token in themes.TOKENS}

    ok, error = themes.create_theme(name, light, dark)
    if ok:
        Flash.ok("Custom theme created.")
    else:
        Flash.error(error or "Could not create theme.")

    return redirect(url_for("admin_bp.appearance"))


@admin_bp.post("/themes/<name>/delete")
def delete_theme(name):
    guard = _superuser_or_redirect()
    if guard:
        return guard

    if themes.delete_theme(name):
        Flash.ok("Theme deleted.")
    else:
        Flash.error("Built-in themes cannot be deleted.")

    return redirect(url_for("admin_bp.appearance"))
