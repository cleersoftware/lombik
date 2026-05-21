from datetime import datetime, timezone
from db import db
import uuid

def utc_now():
    return datetime.now(timezone.utc)

# Your modelse here