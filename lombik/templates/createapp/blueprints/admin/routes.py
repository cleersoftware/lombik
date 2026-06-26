from flask import render_template, redirect, url_for, request, Blueprint, flash, session
from lombik.wrappers import roles_required
from lombik.extensions import limiter
from . import admin_bp



@admin_bp.route("/login")
@roles_required("admin", "superuser")
def home():
    return "Admin panel"
