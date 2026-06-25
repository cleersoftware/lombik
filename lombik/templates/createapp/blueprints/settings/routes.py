from flask import render_template, redirect, url_for, Blueprint, g, request
from zoneinfo import available_timezones
from models import User
from wrappers import login_required
from db import db
from . import settings_bp

@settings_bp.route("/settings")
@login_required
def settings():
    context = {
        "selected": "settings",
        "user": g.user,
        "timezones": available_timezones()

    }
    return render_template("/settings/general.html", **context)


@settings_bp.patch("/change_timezone")
@login_required
def change_timezone():
    user = User.query.filter_by(user_id=g.user.user_id).first()
    new_tz = request.form.get("user_timezone")
    if new_tz not in available_timezones():
        return '<p class="text-red-600 dark:text-red-300">Unrecognized timezone</p>'
    user.timezone = new_tz
    db.session.commit()
    return f'<p class="text-emerald-600 dark:text-emerald-300 animate-pulse">Timezone changed to {new_tz}. You may need to refresh to activate the changes.</p>'