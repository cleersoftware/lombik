from flask import render_template, redirect, url_for, Blueprint, g
from wrappers import login_required, bgthread

{{ module_name }}_bp = Blueprint(
    "{{ module_name }}_bp", 
    __name__, 
    template_folder="templates",
    static_folder="static"
)

@{{ module_name }}_bp.route("/")
@login_required
def main():
    
    context = {
        "selected": "{{ module_name }}",
    }
    return "Hello from {{ module_name }}"