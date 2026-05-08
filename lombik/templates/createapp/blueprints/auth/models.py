from datetime import datetime, timezone
from db import db
import uuid

def utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    role = db.Column(
        db.String(50),
        nullable=False,
        default="user"
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="active"
    )

    password_hash = db.Column(
        db.Text,
        nullable=False
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=utc_now
    )

    last_seen = db.Column(
        db.DateTime(timezone=True), 
        default=utc_now()
    )

    failed_login_attempts = db.Column(
        db.Integer, 
        default=0
    )

    locked_until = db.Column(
        db.DateTime(timezone=True)
    )

    deactivated_at = db.Column(
        db.DateTime(timezone=True)
    )

    deleted_at = db.Column(
        db.Column.DateTime(timezone=True)
    )