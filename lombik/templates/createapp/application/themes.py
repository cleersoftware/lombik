"""
Color themes for generated apps.

Built-in themes plus user-created custom themes. The active theme is persisted
to ``instance/theme.json`` (filesystem-local, not the database) and injected
into templates as an inline ``<style>`` block. Managing themes is a
superuser-only action.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INSTANCE_DIR = PROJECT_ROOT / "instance"
THEME_FILE = INSTANCE_DIR / "theme.json"

DEFAULT_THEME = "coral"

# Every token a theme must define. Used by the theme editor and chart theming.
TOKENS = [
    "canvas", "surface", "raised", "line", "line-strong",
    "ink", "ink-muted", "brand", "brand-ink",
    "success", "warning", "danger",
]


def _palette(light, dark):
    return {"light": light, "dark": dark}


BUILTIN_THEMES = {
    "coral": {
        "name": "Coral",
        "palette": _palette(
            {
                "canvas": "#F8F6F2", "surface": "#FCFBF9", "raised": "#FFFFFF",
                "line": "#E8E5E0", "line-strong": "#D9D4CC",
                "ink": "#2E2C2A", "ink-muted": "#7C7873",
                "brand": "#FF6B5A", "brand-ink": "#FFFFFF",
                "success": "#768E64", "warning": "#D1A054", "danger": "#C6685B",
            },
            {
                "canvas": "#262833", "surface": "#2F3140", "raised": "#2A2C38",
                "line": "#404358", "line-strong": "#4D5064",
                "ink": "#E9EAF0", "ink-muted": "#9598AD",
                "brand": "#FF6B5A", "brand-ink": "#262833",
                "success": "#6F9B7A", "warning": "#D0A15C", "danger": "#C97972",
            },
        ),
    },
    "ocean": {
        "name": "Ocean",
        "palette": _palette(
            {
                "canvas": "#F4F7FA", "surface": "#FBFDFE", "raised": "#FFFFFF",
                "line": "#DEE7EF", "line-strong": "#CBD8E2",
                "ink": "#1B2733", "ink-muted": "#64748B",
                "brand": "#3B82F6", "brand-ink": "#FFFFFF",
                "success": "#4C8C6C", "warning": "#C98A3D", "danger": "#C0564F",
            },
            {
                "canvas": "#0F1720", "surface": "#16202B", "raised": "#1B2733",
                "line": "#273443", "line-strong": "#33475A",
                "ink": "#E2E8F0", "ink-muted": "#8CA0B3",
                "brand": "#60A5FA", "brand-ink": "#0F1720",
                "success": "#6F9B7A", "warning": "#D0A15C", "danger": "#C97972",
            },
        ),
    },
    "forest": {
        "name": "Forest",
        "palette": _palette(
            {
                "canvas": "#F6F8F4", "surface": "#FBFCFA", "raised": "#FFFFFF",
                "line": "#E2E8DD", "line-strong": "#D0D8C8",
                "ink": "#24301F", "ink-muted": "#6C7864",
                "brand": "#5B8C5A", "brand-ink": "#FFFFFF",
                "success": "#6F9B7A", "warning": "#C98A3D", "danger": "#C0564F",
            },
            {
                "canvas": "#1C2419", "surface": "#242E20", "raised": "#2A3526",
                "line": "#3A4734", "line-strong": "#4A5943",
                "ink": "#E7EDE2", "ink-muted": "#9AA88F",
                "brand": "#7FB87B", "brand-ink": "#1C2419",
                "success": "#8BB98F", "warning": "#D0A15C", "danger": "#C97972",
            },
        ),
    },
    "midnight": {
        "name": "Midnight",
        "palette": _palette(
            {
                "canvas": "#F6F5FA", "surface": "#FBFAFD", "raised": "#FFFFFF",
                "line": "#E6E3F0", "line-strong": "#D5D0E5",
                "ink": "#262238", "ink-muted": "#6F6A85",
                "brand": "#7C6BE8", "brand-ink": "#FFFFFF",
                "success": "#768E64", "warning": "#D1A054", "danger": "#C6685B",
            },
            {
                "canvas": "#17151F", "surface": "#1E1B2B", "raised": "#232030",
                "line": "#352F4A", "line-strong": "#463E5E",
                "ink": "#E9E6F5", "ink-muted": "#9B94B5",
                "brand": "#A79BFF", "brand-ink": "#17151F",
                "success": "#6F9B7A", "warning": "#D0A15C", "danger": "#C97972",
            },
        ),
    },
    "mono": {
        "name": "Monochrome",
        "palette": _palette(
            {
                "canvas": "#F7F7F7", "surface": "#FCFCFC", "raised": "#FFFFFF",
                "line": "#E5E5E5", "line-strong": "#D4D4D4",
                "ink": "#1F1F1F", "ink-muted": "#737373",
                "brand": "#404040", "brand-ink": "#FFFFFF",
                "success": "#6B8A6B", "warning": "#B08A4A", "danger": "#B0605A",
            },
            {
                "canvas": "#171717", "surface": "#1F1F1F", "raised": "#242424",
                "line": "#333333", "line-strong": "#404040",
                "ink": "#EDEDED", "ink-muted": "#A3A3A3",
                "brand": "#E5E5E5", "brand-ink": "#171717",
                "success": "#7FA57F", "warning": "#C9A05C", "danger": "#C97972",
            },
        ),
    },
}


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #
def _load_data() -> dict:
    data = {"active": DEFAULT_THEME, "custom": {}}
    try:
        raw = json.loads(THEME_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return data

    # Accept the legacy ``{"theme": "..."}`` shape too.
    data["active"] = raw.get("active", raw.get("theme", DEFAULT_THEME))
    if isinstance(raw.get("custom"), dict):
        data["custom"] = raw["custom"]
    return data


def _save_data(data: dict) -> None:
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    THEME_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _all_themes() -> dict:
    themes = dict(BUILTIN_THEMES)
    data = _load_data()
    for name, spec in data["custom"].items():
        if isinstance(spec, dict) and spec.get("light") and spec.get("dark"):
            themes[name] = {
                "name": spec.get("name") or name,
                "palette": {"light": spec["light"], "dark": spec["dark"]},
            }
    return themes


# --------------------------------------------------------------------------- #
# Read API
# --------------------------------------------------------------------------- #
def available_themes() -> list[dict]:
    return [
        {"id": theme_id, "name": theme["name"],
         "light": theme["palette"]["light"], "dark": theme["palette"]["dark"]}
        for theme_id, theme in _all_themes().items()
    ]


def active_theme_id() -> str:
    theme = _load_data()["active"]
    return theme if theme in _all_themes() else DEFAULT_THEME


def get_active_theme() -> dict:
    return _all_themes()[active_theme_id()]["palette"]


def is_custom(name: str) -> bool:
    return name in _load_data()["custom"]


# --------------------------------------------------------------------------- #
# Write API
# --------------------------------------------------------------------------- #
def save_theme(name: str) -> bool:
    """Activate an existing (built-in or custom) theme."""
    if name not in _all_themes():
        return False
    data = _load_data()
    data["active"] = name
    _save_data(data)
    return True


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")


def _valid_color(value: str) -> bool:
    return bool(re.fullmatch(r"#[0-9a-fA-F]{6}", value or ""))


def create_theme(name: str, light: dict, dark: dict) -> tuple[bool, str | None]:
    slug = _slugify(name)
    if not slug:
        return False, "Please give the theme a name."
    if slug in BUILTIN_THEMES:
        return False, "That name is reserved for a built-in theme."

    for token in TOKENS:
        if not _valid_color(light.get(token)) or not _valid_color(dark.get(token)):
            return False, f"Invalid color for '{token}'."

    data = _load_data()
    data["custom"][slug] = {"name": name.strip(), "light": light, "dark": dark}
    data["active"] = slug
    _save_data(data)
    return True, None


def delete_theme(name: str) -> bool:
    data = _load_data()
    if name not in data["custom"]:
        return False
    del data["custom"][name]
    if data["active"] == name:
        data["active"] = DEFAULT_THEME
    _save_data(data)
    return True


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def theme_css() -> str:
    palette = get_active_theme()

    def block(variables: dict) -> str:
        return "\n".join(f"  --{key}: {value};" for key, value in variables.items())

    return f":root {{\n{block(palette['light'])}\n}}\n.dark {{\n{block(palette['dark'])}\n}}"


def chart_theme_json() -> str:
    """Inline light/dark theme JSON for the bundled chart elements."""
    palette = get_active_theme()

    def block(variables: dict) -> dict:
        return {
            "text-color": variables["ink"],
            "grid-color": variables["line"],
            "axis-color": variables["ink-muted"],
            "bar-color": variables["brand"],
            "line-color": variables["brand"],
            "point-color": variables["brand"],
        }

    return json.dumps({"light": block(palette["light"]), "dark": block(palette["dark"])})


def register_themes(app):
    @app.context_processor
    def _inject_themes():
        return {
            "theme_css": theme_css,
            "active_theme_id": active_theme_id(),
            "available_themes": available_themes(),
            "chart_theme_json": chart_theme_json,
            "theme_tokens": TOKENS,
        }
