from flask import render_template, redirect, url_for, Blueprint

auth_bp = Blueprint(
    "auth_bp", 
    __name__, 
    template_folder="templates",
    static_folder="static"
)

@auth_bp.route("/login")
def login():
    return render_template("auth/login.html")