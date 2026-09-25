from sqlalchemy.exc import SQLAlchemyError

from db import db
from application.responses import Result


def apply_drag_change(instance, field, value):
    """Generic in-place update for a drag-and-drop field change."""
    if not hasattr(instance, field):
        return Result(success=False, message=f"Unknown field: {field}")

    setattr(instance, field, value)
    try:
        db.session.commit()
        return Result(success=True, data={"id": getattr(instance, "id", None)})
    except SQLAlchemyError:
        db.session.rollback()
        return Result(success=False, message="Could not save drag change.")