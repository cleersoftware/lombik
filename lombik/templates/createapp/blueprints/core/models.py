from datetime import datetime, timezone
from db import db
import uuid


def utc_now():
    return datetime.now(timezone.utc)


class Error(db.Model):
    __tablename__="errors"

    error_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.user_id"))
    function = db.Column(db.String(100))
    action = db.Column(db.String(100))
    error = db.Column(db.Text)
    traceback = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, index=True)

    user = db.relationship("User")
