from flask import render_template, redirect, url_for, Blueprint, g
from wrappers import login_required

core_bp = Blueprint(
    "core_bp", 
    __name__, 
    template_folder="templates",
    static_folder="static"
)

@core_bp.route("/")
@login_required
def home():
    from datetime import datetime, timezone
    context = {
        "selected": "home",
        "user": g.user,
        "current_ts": datetime.now(timezone.utc)
    }
    return render_template("/core/home.html", **context)
