from flask import render_template

from . import core_bp


@core_bp.route("/")
def home():
    context = {
        "selected": "home",
        "version": "4.4.4",
    }
    return render_template("core/home.html", **context)


@core_bp.get("/partials/quickstart")
def quickstart():
    """Small HTMX partial to demonstrate server-rendered fragments."""
    return render_template("core/partials/quickstart.html")
