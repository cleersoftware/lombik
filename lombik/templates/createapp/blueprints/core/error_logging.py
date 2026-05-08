from db import db
from blueprints.core.models import Error
from sqlalchemy.exc import SQLAlchemyError
from flask import g
import traceback


def log_error(
    user_id: str,
    function: str,
    action: str,
    exception: Exception
):
    try:
        db.session.add(
            Error(
                user_id=user_id,
                function=function,
                action=action,
                error_message=str(exception),
                traceback=traceback.format_exc()
            )
        )
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()