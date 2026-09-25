import os
import subprocess
from pathlib import Path

from flask import g, redirect, render_template, request, session, url_for

from . import admin_bp
from . import services
from application import themes
from application.auth import create_user
from application.flash import Flash
from application.responses import htmx_response
from application.utils import get_countries
from models import User

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GUIDE_PATH = PROJECT_ROOT / "application" / "guide.md"


def _superuser_or_redirect():
    """Return a redirect/HTMX redirect if the visitor is not a superuser."""
    user = getattr(g, "user", None)

    if not user:
        Flash.error("Log in to access admin.")
        target = url_for("auth_bp.login", next=request.path)
        return htmx_response(html="", redirect=target) if request.headers.get("HX-Request") else redirect(target)

    if user.role != "superuser":
        Flash.error("Admin is only available to superusers.")
        target = url_for("core_bp.home")
        return htmx_response(html="", redirect=target) if request.headers.get("HX-Request") else redirect(target)

    return None


def _shell(active: str):
    return render_template(
        "admin/shell.html",
        selected="admin",
        active=active,
        initial_url=url_for(f"admin_bp.page_{active}"),
    )


def _guide_html() -> str:
    try:
        return GUIDE_PATH.read_text(encoding="utf-8")
    except OSError:
        return "# Guide\n\nGuide content could not be loaded."


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

    return _shell("errors")


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
# Shell pages (full page on direct visit)
# --------------------------------------------------------------------------- #
@admin_bp.get("/schema")
def schema_page():
    guard = _superuser_or_redirect()
    if guard:
        return guard
    return _shell("schema")


@admin_bp.get("/appearance")
def appearance_page():
    guard = _superuser_or_redirect()
    if guard:
        return guard
    return _shell("appearance")


@admin_bp.get("/guide")
def guide_page():
    guard = _superuser_or_redirect()
    if guard:
        return guard
    return _shell("guide")


# --------------------------------------------------------------------------- #
# HTMX page fragments
# --------------------------------------------------------------------------- #
@admin_bp.get("/pages/errors")
def page_errors():
    guard = _superuser_or_redirect()
    if guard:
        return guard
    return render_template("admin/pages/errors.html")


@admin_bp.get("/pages/schema")
def page_schema():
    guard = _superuser_or_redirect()
    if guard:
        return guard
    return render_template("admin/pages/schema.html", tables=services.schema_tables())


@admin_bp.get("/pages/appearance")
def page_appearance():
    guard = _superuser_or_redirect()
    if guard:
        return guard

    available = themes.available_themes()
    return render_template(
        "admin/pages/appearance.html",
        active_theme=themes.active_theme_id(),
        available_themes=available,
        custom_ids=[t["id"] for t in available if themes.is_custom(t["id"])],
        theme_tokens=themes.TOKENS,
        active_palette=themes.get_active_theme(),
    )


@admin_bp.get("/pages/guide")
def page_guide():
    guard = _superuser_or_redirect()
    if guard:
        return guard
    return render_template("admin/pages/guide.html", guide_html=_guide_html())


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


@admin_bp.get("/partials/chart")
def chart_partial():
    guard = _superuser_or_redirect()
    if guard:
        return guard

    mode = request.args.get("mode", "day")
    if mode == "hour":
        data = services.error_series_hourly()
        caption = "last 24 hours"
    else:
        mode = "day"
        data = services.error_series_daily()
        caption = "last 14 days"

    return render_template("admin/partials/chart.html", mode=mode, data=data, caption=caption)


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

    return redirect(url_for("admin_bp.appearance_page"))


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

    return redirect(url_for("admin_bp.appearance_page"))


@admin_bp.post("/themes/<name>/delete")
def delete_theme(name):
    guard = _superuser_or_redirect()
    if guard:
        return guard

    if themes.delete_theme(name):
        Flash.ok("Theme deleted.")
    else:
        Flash.error("Built-in themes cannot be deleted.")

    return redirect(url_for("admin_bp.appearance_page"))


@admin_bp.post("/terminal")
def terminal():
    guard = _superuser_or_redirect()
    if guard:
        return guard

    command = (request.form.get("command") or "").strip()
    if not command:
        return render_template("admin/partials/terminal_entry.html", command="", output="(no command)", status=1)
    if len(command) > 2000:
        return render_template("admin/partials/terminal_entry.html", command=command[:2000], output="Command too long.", status=1)

    if command in ("help", "lombik help", "lombik --help"):
        help_text = (
            "Lombik commands\n"
            "----------------\n"
            "lombik createapp <name>          generate a new app\n"
            "lombik module <name>             add a blueprint module\n"
            "lombik model <name>              add + register a model\n"
            "lombik crud <model>              generate a full CRUD module\n"
            "lombik relate a.id to b.a_id     create a relationship\n"
            "lombik db -m \"message\"           migrate + upgrade\n"
            "lombik run                       start the dev server\n"
            "lombik test                      run pytest\n"
            "\n"
            "Flask commands\n"
            "--------------\n"
            "flask db migrate -m \"msg\"        create a migration\n"
            "flask db upgrade                 apply migrations\n"
            "flask routes                     list routes\n"
            "\n"
            "Terminal\n"
            "--------\n"
            "help                             show this help"
        )
        return render_template("admin/partials/terminal_entry.html", command=command, output=help_text, status=0)

    env = os.environ.copy()
    env["FLASK_APP"] = "app.py"

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return render_template("admin/partials/terminal_entry.html", command=command, output="Command timed out.", status=1)

    output = ((result.stdout or "") + (result.stderr or "")).strip()
    if len(output) > 8000:
        output = output[:8000] + "\n… (truncated)"
    if not output:
        output = "(no output)"

    return render_template("admin/partials/terminal_entry.html", command=command, output=output, status=result.returncode)
