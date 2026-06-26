from flask import session, redirect, url_for, g, abort
from threading import Thread
from functools import wraps
from lombik.flash import Flash

def login_required(f):
    """
    Example usage on a route:

    @app.route("/")
    @login_required
    def index():
        ....
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session or not g.user:
            Flash.error("You must log in to visit this page")
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return wrapper


def roles_required(*roles):
    """
    Example usage on a route:

    @app.route("/")
    @roles_required("admin", "superuser", ...)
    def index():
        ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = getattr(g, "user", None)

            if not user:
                Flash.error("Login required")
                return redirect(url_for("auth_bp.login"))

            if user.role not in roles:
                Flash.error("You don't have access to this page")
                return redirect(url_for("core_bp.home"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def run_async(f):
    """
    Example usage on a function:

    @run_async
    def send_email():
        ...

    Do not use for heavyweight database transactions.
    General threading should be used fir samller tasks like sending an email, uploading a file etc.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        thread = Thread(target=f, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
    return wrapper