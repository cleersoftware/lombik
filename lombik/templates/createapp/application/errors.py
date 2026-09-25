from werkzeug.exceptions import HTTPException
from flask import render_template, g, has_request_context, request
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
            exception=e,
            function=request.endpoint,
        )

        return render_template("errors/500.html"), 500


def log_error(exception, function=None, args=None, kwargs=None):
    """Persist a diagnostic error record (safe to call inside a 500 handler)."""
    try:
        exception_type = type(exception).__name__ if isinstance(exception, BaseException) else "Exception"
        message = str(exception)

        has_ctx = has_request_context()
        endpoint = request.endpoint if has_ctx else None
        current_user = getattr(g, "user", None)

        error = Error(
            user_id=getattr(current_user, "id", None),
            tenant_id=getattr(g, "tenant_id", None),
            endpoint=endpoint,
            function=function or endpoint,
            method=request.method if has_ctx else None,
            path=request.path if has_ctx else None,
            status_code=getattr(exception, "code", 500),
            exception_type=exception_type,
            message=message,
            traceback=traceback.format_exc(),
            ip=request.remote_addr if has_ctx else None,
            user_agent=request.user_agent.string if has_ctx else None,
            referrer=request.referrer if has_ctx else None,
            args=json.dumps(args, default=str) if args else None,
            kwargs=json.dumps(kwargs, default=str) if kwargs else None,
            context=json.dumps(
                {k: v for k, v in {
                    "url": request.url if has_ctx else None,
                    "query": request.query_string.decode("utf-8") if has_ctx and request.query_string else None,
                }.items() if v is not None},
                default=str,
            ) if has_ctx else None,
        )

        db.session.add(error)
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
