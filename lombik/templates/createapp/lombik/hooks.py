from flask import session, current_app, g
from models import User
from db import db
import time


def _csrf_lifetime_tracker():
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
    if not user:
        return None

    return user

def register_hooks(app):
    @app.before_request
    def fetch_user():
        user_id = session.get("user_id")
        g.user = _load_user(user_id) if user_id else None

    app.before_request(_csrf_lifetime_tracker)
