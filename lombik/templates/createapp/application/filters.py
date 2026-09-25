from flask import g
import re
from .strings import plural
from zoneinfo import ZoneInfo
import json
from datetime import datetime, timezone, timedelta

def register_filters(app):
    
    @app.template_filter("json_nosort")
    def json_nosort(j):
        return json.dumps(j, indent=2, sort_keys=False)

    def _localize(dt):
        if not dt:
            return None

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        tz = getattr(getattr(g, "user", None), "timezone", "UTC")
        return dt.astimezone(ZoneInfo(tz))

    def _fmt(dt, fmt):
        dt = _localize(dt)
        return dt.strftime(fmt) if dt else ""

    @app.template_filter("localtimezone")
    def localtimezone(dt):
        return _localize(dt)

    @app.template_filter("dateonly")
    def dateonly(dt):
        return _fmt(dt, "%Y-%m-%d")

    @app.template_filter("timeonly")
    def timeonly(dt):
        return _fmt(dt, "%H:%M")

    @app.template_filter("localtime")
    def localtime(dt):
        return _fmt(dt, "%Y-%m-%d %H:%M")

    @app.template_filter("shortdatetime")
    def shortdatetime(dt):
        return _fmt(dt, "%b %d %H:%M").lower()

    @app.template_filter("longdate")
    def longdatetime(dt):
        return _fmt(dt, "%A, %B %d")

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


    @app.template_filter("timeuntil")
    def timeuntil(dt):
        """Time until a future event - exactly what you wanted!"""
        if not dt or not isinstance(dt, datetime):
            return ""

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        now = datetime.now(timezone.utc)
        diff = (dt - now).total_seconds()

        if diff < 0:
            return "in the past"

        if diff < 60:
            return "just now"
        if diff < 120:
            return "in a minute"
        if diff < 3600:
            minutes = round(diff / 60)
            return f"in {minutes} minute{'s' if minutes != 1 else ''}"
        if diff < 7200:
            return "in an hour"
        if diff < 86400:
            hours = round(diff / 3600)
            return f"in {hours} hour{'s' if hours != 1 else ''}"
        if diff < 172800:
            return "tomorrow"
        if diff < 2592000:
            days = round(diff / 86400)
            return f"in {days} day{'s' if days != 1 else ''}"
        if diff < 31536000:
            months = round(diff / 2592000)
            return f"in {months} month{'s' if months != 1 else ''}"
        
        years = round(diff / 31536000)
        return f"in {years} year{'s' if years != 1 else ''}"

    @app.template_filter("formatnumber")
    def formatnumber(value):
        return f"{value:,}".replace(",", ".")


    @app.template_filter("compactnumber")
    def compactnumber(value):
        if value < 1_000:
            return str(value)
        elif value < 1_000_000:
            return f"{value / 1_000:g}K"
        else:
            return f"{value / 1_000_000:g}M"


    @app.template_filter("wordcount")
    def wordcount(s):
        """Count words in string"""
        if not s:
            return 0
        return len(s.split())


    @app.template_filter("truncate")
    def truncate(s, length=50, ellipsis="..."):
        """Truncate string to max length"""
        if not s or len(s) <= length:
            return s
        return s[:length].rsplit(" ", 1)[0] + ellipsis


    @app.template_filter("sort_by")
    def sort_by(lst, key):
        """Sort list of dicts by a key"""
        if not lst:
            return []
        return sorted(lst, key=lambda x: x.get(key, ""))


    @app.template_filter("group_by")
    def group_by(lst, key):
        """Group list of dicts by a key"""
        if not lst:
            return {}
        groups = {}
        for item in lst:
            group_key = item.get(key)
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(item)
        return groups
    