from flask import Blueprint

{{ module_name }}_bp = Blueprint(
    "{{ module_name }}_bp", 
    __name__, 
    template_folder="templates",
    static_folder="static"
)