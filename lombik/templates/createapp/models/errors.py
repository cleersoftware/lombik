from datetime import datetime, timezone
from lombik.utils import utc_now
from db import db
import uuid


class Error(db.Model):
    __tablename__ = "errors"

    error_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)

    endpoint = db.Column(db.String(100))
    function = db.Column(db.String(100))

    exception_type = db.Column(db.String(200))
    message = db.Column(db.Text)

    traceback = db.Column(db.Text)

    args = db.Column(db.Text)
    kwargs = db.Column(db.Text)

    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, index=True)

    user = db.relationship("User")