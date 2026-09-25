"""Read/aggregate data for the admin panel."""
from collections import Counter
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


def _ensure_utc(dt):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def error_series_daily(days: int = 14) -> dict:
    """Return ``{label: count}`` for the last ``days`` days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.session.query(Error.created_at).filter(Error.created_at >= since).all()

    counter = Counter()
    for (created_at,) in rows:
        counter[_ensure_utc(created_at).date()] += 1

    today = datetime.now(timezone.utc).date()
    return {
        (today - timedelta(days=days - 1 - i)).strftime("%b %d"): counter.get(
            today - timedelta(days=days - 1 - i), 0
        )
        for i in range(days)
    }


def error_series_hourly(hours: int = 24) -> dict:
    """Return ``{label: count}`` for the last ``hours`` hours."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = db.session.query(Error.created_at).filter(Error.created_at >= since).all()

    counter = Counter()
    for (created_at,) in rows:
        hour = _ensure_utc(created_at).replace(minute=0, second=0, microsecond=0)
        counter[hour] += 1

    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    return {
        (now - timedelta(hours=hours - 1 - i)).strftime("%H:00"): counter.get(
            now - timedelta(hours=hours - 1 - i), 0
        )
        for i in range(hours)
    }


def schema_tables() -> list:
    return [t for t in db.metadata.sorted_tables if t.name not in SKIP_TABLES]


def clear_errors() -> int:
    count = Error.query.delete()
    db.session.commit()
    return count
