from flask import render_template, redirect, url_for, request, Blueprint, flash, session
from lombik.auth import authenticate_user
from lombik.extensions import limiter
from tools import genflash
from . import auth_bp



@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    
    if request.method == 'POST':
        res = authenticate_user(
            email=request.form.get("email", "").strip().lower(),
            password=request.form.get("password", "")
        )

        if not res.success:
            msg, cat = genflash(res.message, "error")
            flash(msg ,cat)
            return redirect(url_for("auth_bp.login"))
        
        session["user_id"] = res.data["user_id"]
        msg, cat = genflash("Welcome", "chat")
        flash(msg, cat)
        return redirect(url_for("core_bp.home"))

    return render_template("auth/login.html")


@auth_bp.post("/logout")
def logout():
    session.clear()
    msg, cat = genflash("Bye bye!", "chat")
    flash(msg, cat)
    return redirect(url_for("auth_bp.login"))