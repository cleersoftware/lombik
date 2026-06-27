from . import admin_bp
from flask import render_template, redirect, url_for, request, Blueprint, flash, session
from lombik.wrappers import roles_required
from lombik.extensions import limiter



@admin_bp.route("/controller")
@roles_required("admin", "superuser")
def controller():
    return "Admin panel"
