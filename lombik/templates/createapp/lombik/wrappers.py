from flask import session, redirect, url_for, flash, g
from threading import Thread
from functools import wraps
from tools import genflash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not g.user:
            msg, cat = genflash("You must log in to visit this page", "error")
            flash(msg, cat)
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function


def bgthread(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
    return wrapper