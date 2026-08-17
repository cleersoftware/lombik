from datetime import datetime, timezone
from db import db
import uuid

def utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )
    
    first_name = db.Column(
        db.String(100)
    )

    last_name = db.Column(
        db.String(100)
    )

    birthday = db.Column(db.Date)

    role = db.Column(
        db.String(50),
        nullable=False,
        default="user"
    )

    country = db.Column(
        db.String(255)
    )

    timezone = db.Column(
        db.String(100),
        nullable=False,
        default="utc"
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
        default=utc_now
    )

    failed_login_attempts = db.Column(
        db.Integer, 
        default=0
    )

    locked_until = db.Column(
        db.DateTime(timezone=True)
    )

    reset_token_hash = db.Column(
        db.Text(),
    )

    reset_token_expires_at = db.Column(
        db.DateTime(timezone=True)
    )

    deactivated_at = db.Column(
        db.DateTime(timezone=True)
    )

    delete_at = db.Column(
        db.DateTime(timezone=True)
    )