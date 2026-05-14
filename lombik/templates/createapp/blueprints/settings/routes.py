from flask import render_template, redirect, url_for, Blueprint, g
from wrappers import login_required

settings_bp = Blueprint(
    "settings_bp", 
    __name__, 
    template_folder="templates",
    static_folder="static"
)

@settings_bp.route("/settings")
@login_required
def settings():
    context = {
        "selected": "settings",
        "user": g.user,

    }
    return render_template("/settings/general.html", **context)