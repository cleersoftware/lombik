from application.utils import utc_now
from db import db
import uuid


class Error(db.Model):
    __tablename__ = "errors"

    error_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), index=True)
    tenant_id = db.Column(db.String(36), index=True)

    endpoint = db.Column(db.String(200))
    function = db.Column(db.String(200))

    method = db.Column(db.String(10))
    path = db.Column(db.String(500))
    status_code = db.Column(db.Integer)

    exception_type = db.Column(db.String(200))
    message = db.Column(db.Text)

    traceback = db.Column(db.Text)

    ip = db.Column(db.String(100))
    user_agent = db.Column(db.String(500))
    referrer = db.Column(db.String(500))

    args = db.Column(db.Text)
    kwargs = db.Column(db.Text)
    context = db.Column(db.JSON)

    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now)

    # <LOMBIK:COLUMNS>
    # </LOMBIK:COLUMNS>

    # <LOMBIK:RELATIONSHIPS>
    # </LOMBIK:RELATIONSHIPS>

    user = db.relationship("User")
