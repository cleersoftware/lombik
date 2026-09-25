from flask import render_template
from . import {{ module_name }}_bp


@{{ module_name }}_bp.get("/")
def home():
    return render_template("{{ module_name }}/index.html")
