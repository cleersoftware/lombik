"""
Simple file-level undo/redo + activity log for Lombik Studio.

Studio mutations are file-based (models, blueprints, templates), so we can
snapshot those directories before and after a mutation, record the differences,
and restore them on undo/redo.
"""
from __future__ import annotations

import json
import time
from functools import wraps
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HISTORY_FILE = PROJECT_ROOT / "studio_history.json"
SCAN_DIRS = ("models", "blueprints", "templates")


def _snapshot() -> dict[str, str | None]:
    snapshot: dict[str, str | None] = {}

    for dirname in SCAN_DIRS:
        base = PROJECT_ROOT / dirname
        if not base.exists():
            continue

        for path in base.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue

            try:
                snapshot[str(path.relative_to(PROJECT_ROOT))] = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

    return snapshot


def _load() -> dict:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"undo": [], "redo": []}


def _save(data: dict) -> None:
    HISTORY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _record(before: dict, after: dict) -> None:
    changes = []

    for path in sorted(set(before) | set(after)):
        old = before.get(path)
        new = after.get(path)
        if old != new:
            changes.append({"path": path, "before": old, "after": new})

    if not changes:
        return

    data = _load()
    data["undo"].append({
        "time": int(time.time()),
        "summary": [c["path"] for c in changes],
        "changes": changes,
    })
    data["redo"] = []
    _save(data)


def track(fn):
    """Decorator that records file changes made by a Studio mutation endpoint."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        before = _snapshot()
        response = fn(*args, **kwargs)
        after = _snapshot()
        _record(before, after)
        return response

    return wrapper


def _apply_changes(changes: list[dict], direction: str) -> None:
    for change in changes:
        path = PROJECT_ROOT / change["path"]
        content = change[direction]

        if content is None:
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")


def undo() -> dict:
    data = _load()
    if not data["undo"]:
        return {"ok": False, "error": "Nothing to undo."}

    entry = data["undo"].pop()
    data["redo"].append(entry)
    _save(data)
    _apply_changes(entry["changes"], "before")

    return {"ok": True, "changes": entry["summary"], "message": "Undo applied."}


def redo() -> dict:
    data = _load()
    if not data["redo"]:
        return {"ok": False, "error": "Nothing to redo."}

    entry = data["redo"].pop()
    data["undo"].append(entry)
    _save(data)
    _apply_changes(entry["changes"], "after")

    return {"ok": True, "changes": entry["summary"], "message": "Redo applied."}


def log() -> dict:
    data = _load()
    return {
        "ok": True,
        "undo": data["undo"],
        "redo": data["redo"],
    }
