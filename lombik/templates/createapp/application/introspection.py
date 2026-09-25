"""
Model-file introspection helpers.

These functions read the generated ``models/*.py`` files back into structured
data and are used by the ``flask crud`` command to build CRUD blueprints. They
run *inside* a generated app (where ``db`` and ``models`` are importable), which
is why they live here instead of in the Lombik CLI package.
"""
from __future__ import annotations

import re
from pathlib import Path

from application.strings import plural, singularize, to_camel, to_snake


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"


def model_path(module: str) -> Path:
    return MODELS_DIR / f"{module}.py"


# --------------------------------------------------------------------------- #
# Parsing (read .py model files back into structured data)
# --------------------------------------------------------------------------- #
def _match_paren(text: str, open_idx: int) -> int | None:
    depth = 0
    quote = None
    i = open_idx
    n = len(text)
    while i < n:
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ('"', "'"):
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def _find_assignments(content: str, func: str) -> list[dict]:
    pattern = re.compile(r"(?m)^(\s*)(\w+)\s*=\s*" + re.escape(func) + r"\(")
    results = []
    for m in pattern.finditer(content):
        open_idx = m.end() - 1
        close_idx = _match_paren(content, open_idx)
        if close_idx is None:
            continue
        results.append({
            "name": m.group(2),
            "block": content[m.start():close_idx + 1],
            "start": m.start(),
            "end": close_idx + 1,
        })
    return results


def _parse_default(block: str) -> str | None:
    m = re.search(r"default=([^,\n)]+)", block)
    return m.group(1).strip() if m else None


def _parse_column(name: str, block: str) -> dict:
    m = re.search(r"db\.Column\(\s*(db\.\w+(?:\([^)]*\))?)", block)
    type_display = m.group(1).replace("db.", "") if m else "String(255)"

    fk = None
    fkm = re.search(r'db\.ForeignKey\(\s*"([^"]+)"', block)
    if fkm:
        ref = fkm.group(1)
        table, _, col = ref.partition(".")
        fk = {"table": table, "column": col or "id"}
        od = re.search(r'ondelete="([^"]+)"', block)
        if od:
            fk["ondelete"] = od.group(1)
        ou = re.search(r'onupdate="([^"]+)"', block)
        if ou:
            fk["onupdate"] = ou.group(1)

    return {
        "name": name,
        "type": type_display.split("(")[0],
        "type_display": type_display,
        "primary_key": "primary_key=True" in block,
        "nullable": "nullable=False" not in block,
        "unique": "unique=True" in block,
        "index": "index=True" in block,
        "default": _parse_default(block),
        "fk": fk,
    }


def _parse_relationship(name: str, block: str) -> dict:
    target = ""
    m = re.search(r'db\.relationship\(\s*"([^"]+)"', block)
    if m:
        target = m.group(1)
    bp = re.search(r'back_populates="([^"]+)"', block)
    sec = re.search(r'secondary="([^"]+)"', block)
    lazy = re.search(r"lazy='([^']+)'", block)
    return {
        "name": name,
        "target": target,
        "back_populates": bp.group(1) if bp else "",
        "uselist": "uselist=False" not in block,
        "lazy": lazy.group(1) if lazy else "select",
        "secondary": sec.group(1) if sec else None,
    }


def parse_model_file(path: Path) -> dict | None:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    class_m = re.search(r"class\s+(\w+)\s*\(db\.Model\)", content)
    table_m = re.search(r'__tablename__\s*=\s*"([^"]+)"', content)
    if not class_m:
        return None

    return {
        "module": path.stem,
        "class_name": class_m.group(1),
        "table_name": table_m.group(1) if table_m else path.stem,
        "columns": [_parse_column(a["name"], a["block"]) for a in _find_assignments(content, "db.Column")],
        "relationships": [_parse_relationship(a["name"], a["block"]) for a in _find_assignments(content, "db.relationship")],
    }


def list_models() -> list[dict]:
    if not MODELS_DIR.exists():
        return []
    models = []
    for path in sorted(MODELS_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        info = parse_model_file(path)
        if info:
            models.append(info)
    return models


def resolve_model_file(name: str) -> Path | None:
    snake = to_snake(name)
    candidates = []
    for candidate in (snake, plural(snake), singularize(snake), plural(singularize(snake))):
        candidate = to_snake(candidate)
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    for candidate in candidates:
        path = model_path(candidate)
        if path.exists():
            return path

    target_class = to_camel(name)
    for path in sorted(MODELS_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        info = parse_model_file(path)
        if info and (info["class_name"] == target_class or info["table_name"] in (snake, plural(snake))):
            return path
    return None


def sync_models_init() -> None:
    MODELS_DIR.mkdir(exist_ok=True)
    entries = []
    for path in sorted(MODELS_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        info = parse_model_file(path)
        if info and info["class_name"]:
            entries.append((path.stem, info["class_name"]))

    imports = "\n".join(f"from .{module} import {cls}" for module, cls in entries)
    class_list = ", ".join(cls for _, cls in entries)
    all_list = ", ".join(f'"{cls}"' for _, cls in entries)

    content = (
        f"{imports}\n\n\n"
        f"def register_models():\n"
        f'    """\n'
        f"    Import all models in here to be supplied in app.py\n"
        f'    """\n'
        f"    return [{class_list}]\n\n\n"
        f"__all__ = [{all_list}]\n"
    )
    (MODELS_DIR / "__init__.py").write_text(content, encoding="utf-8")
