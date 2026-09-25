"""Read/aggregate data for the admin panel."""
from datetime import datetime, timedelta, timezone

from db import db
from models import Error, User

SKIP_TABLES = {"alembic_version"}


def error_stats() -> dict:
    day_ago = datetime.now(timezone.utc) - timedelta(days=1)
    tables = [t for t in db.metadata.sorted_tables if t.name not in SKIP_TABLES]

    return {
        "total_errors": Error.query.count(),
        "errors_24h": Error.query.filter(Error.created_at >= day_ago).count(),
        "users": User.query.count(),
        "tables": len(tables),
    }


def recent_errors(limit: int = 100) -> list[Error]:
    return (
        Error.query
        .order_by(Error.created_at.desc())
        .limit(limit)
        .all()
    )


def schema_tables() -> list:
    return [t for t in db.metadata.sorted_tables if t.name not in SKIP_TABLES]


def clear_errors() -> int:
    count = Error.query.delete()
    db.session.commit()
    return count
