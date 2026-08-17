from werkzeug.exceptions import HTTPException
from flask import render_template, g, request
from sqlalchemy.exc import SQLAlchemyError
from flask_wtf.csrf import CSRFError
from models import Error
from db import db
import traceback
import json


def register_error_handlers(app):

    @app.errorhandler(CSRFError)
    def csrf_error(e):
        return render_template("errors/csrf_error.html"), 400

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return e

        log_error(
            exception=str(e),
            function=request.endpoint
        )

        return render_template("errors/500.html"), 500


def log_error(exception, function=None, args=None, kwargs=None):
    try:
        error = Error(
            user_id=getattr(g, "user", None).id if getattr(g, "user", None) else None,
            endpoint=request.endpoint,
            function=function or request.endpoint,
            exception_type=str(type(exception).__name__),
            message=str(exception),
            traceback=traceback.format_exc(),
            args=json.dumps(args, default=str) if args else None,
            kwargs=json.dumps(kwargs, default=str) if kwargs else None,
        )

        db.session.add(error)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()