from . import core_bp
from blueprints.core.forms import *
from flask import render_template

@core_bp.route("/")
def home():
    from datetime import datetime, timezone
    context = {
        "selected": "home",
        "version": "2.0.2",
        "current_ts": datetime.now(timezone.utc)
    }
    return render_template("/core/home.html", **context)



