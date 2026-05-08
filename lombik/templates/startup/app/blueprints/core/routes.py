from flask import render_template, redirect, url_for, Blueprint, g

core_bp = Blueprint(
    "core_bp", 
    __name__, 
    template_folder="templates",
    static_folder="static"
)

@core_bp.route("/home")
def home():
    context = {
        "selected": "home",
        "user": g.user
    }
    return render_template("/core/home.html", **context)