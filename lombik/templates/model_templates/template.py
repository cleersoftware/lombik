from datetime import datetime, timezone
from db import db
import uuid

def utc_now():
    return datetime.now(timezone.utc)

class {{ ModelName }}(db.Model):
    __tablename__ = "{{ model_name }}"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    #...build your model here

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=utc_now
    )