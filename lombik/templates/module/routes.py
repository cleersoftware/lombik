from flask import render_template
from . import {{ module_name }}_bp

@{{ module_name }}_bp.route("/")
def home():
    context = {
        "selected": "{{ module_name }}",
    }
    return "Hello from {{ module_name }}"