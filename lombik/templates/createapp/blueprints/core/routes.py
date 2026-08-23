from . import core_bp
from blueprints.core.forms import *
from flask import render_template
from lombik.utils import utc_now

@core_bp.route("/")
def home():
    context = {
        "selected": "home",
        "version": "3.2.2",
        "current_ts": utc_now()
    }
    return render_template("/core/home.html", **context)



