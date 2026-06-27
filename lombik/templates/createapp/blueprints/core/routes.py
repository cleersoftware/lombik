from . import core_bp
from flask import render_template

@core_bp.route("/")
def home():
    from datetime import datetime, timezone
    context = {
        "selected": "home",
        "version": "1.0.5",
        "current_ts": datetime.now(timezone.utc)
    }
    return render_template("/core/home.html", **context)