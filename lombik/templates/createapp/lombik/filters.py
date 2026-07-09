from flask import g
import re
from .strings import plural
from datetime import datetime, timezone, timedelta

def register_filters(app):
    from zoneinfo import ZoneInfo

    def _localize(dt):
        if not dt:
            return None

        tz = "UTC"
        if getattr(g, "user", None):
            tz = getattr(g.user, "timezone", "UTC")

        return dt.astimezone(ZoneInfo(tz))

    def _fmt(dt, fmt):
        dt = _localize(dt)
        return dt.strftime(fmt) if dt else ""

    @app.template_filter("localtimezone")
    def localtimezone(dt):
        return _localize(dt)

    @app.template_filter("onlydate")
    def onlydate(dt):
        return _fmt(dt, "%Y-%m-%d")

    @app.template_filter("onlytime")
    def onlytime(dt):
        return _fmt(dt, "%H:%M")

    @app.template_filter("localtime")
    def localtime(dt):
        return _fmt(dt, "%Y-%m-%d %H:%M")

    @app.template_filter("shortdatetime")
    def shortdatetime(dt):
        return _fmt(dt, "%b %d %H:%M").lower()

    @app.template_filter("proper")
    def proper(s):
        return s.replace("_", " ").title()
    
    
    @app.template_filter("normalize")
    def normalize(s: str):
        if not s:
            return ""

        s = s.lower()
        s = re.sub(r"[^a-z0-9_]+", "_", s)
        s = re.sub(r"_+", "_", s)

        return s.strip("_")
    

    @app.template_filter("possessive")
    def possessive(s):
        if not s:
            return ""
        return f"{s}'" if s.lower().endswith("s") else f"{s}'s"
    

    @app.template_filter("pluralize")
    def pluralize(s):
        if not s:
            return ""
        return plural(s)


    @app.template_filter("timesince")
    def timesince(dt):
        if not dt:
            return ""

        if not isinstance(dt, datetime):
            return ""

        # ensure UTC for comparison safety
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        now = datetime.now(timezone.utc)
        diff = (now - dt).total_seconds()

        if diff < 60:
            return "just now"

        if diff < 180:
            return "a few minutes ago"

        minute = 60
        hour = 3600
        day = 86400
        month = 2592000
        year = 31536000

        if diff < hour:
            minutes = round(diff / minute)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"

        if diff < day:
            hours = round(diff / hour)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"

        if diff < month:
            days = round(diff / day)
            return f"{days} day{'s' if days != 1 else ''} ago"

        if diff < year:
            months = round(diff / month)
            return f"{months} month{'s' if months != 1 else ''} ago"

        years = round(diff / year)
        return f"{years} year{'s' if years != 1 else ''} ago"