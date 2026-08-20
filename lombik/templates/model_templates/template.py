from lombik.utils import utc_now
from db import db
import uuid


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

    # <LOMBIK:RELATIONSHIPS>