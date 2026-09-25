from flask import current_app, g, redirect, request, session, url_for
from models import User
from db import db
import time


def _track_csrf_lifetime():
    session["csrf_last_reset"] = int(time.time())
    g.csrf_time_left = current_app.config.get("WTF_CSRF_TIME_LIMIT", 3600)


def _load_user(user_id):
    user = db.session.query(
        User.id,
        User.username,
        User.email,
        User.role,
        User.country,
        User.timezone,
        User.status,
        User.created_at
    ).filter_by(id=user_id).first()
    return user


def _ensure_owner_setup():
    """Redirect to /admin until the first owner account exists."""
    if request.method != "GET":
        return
    if not request.endpoint or request.endpoint == "static":
        return
    if request.endpoint.startswith(("admin_bp.", "auth_bp.", "static")):
        return

    try:
        if User.query.count() == 0:
            return redirect(url_for("admin_bp.index"))
    except Exception:
        # DB not initialised yet (or table missing) — nothing to guard yet.
        return


def register_hooks(app):
    @app.before_request
    def fetch_user():
        user_id = session.get("user_id")
        g.user = _load_user(user_id) if user_id else None

    app.before_request(_track_csrf_lifetime)
    app.before_request(_ensure_owner_setup)
