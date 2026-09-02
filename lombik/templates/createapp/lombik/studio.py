"""
Lombik Studio — browser-based data modelling & data workspace.

This module is the service layer used by the ``studio`` blueprint. It is only
reachable by superusers (enforced in the blueprint itself).

It is intentionally split from ``cli.py`` because it runs *inside* a generated
app (where ``db`` and ``models`` are importable), whereas the CLI runs from the
developer's shell against the project directory.
"""
from __future__ import annotations

import importlib
import keyword
import math
import re
import subprocess
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path

from sqlalchemy import (
    MetaData,
    Table,
    and_,
    delete,
    func,
    inspect,
    insert,
    select,
    text,
    update,
)

from db import db
from lombik.strings import plural, singularize, to_camel, to_snake


# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"


# --------------------------------------------------------------------------- #
# Naming helpers now live in lombik.strings so the CLI and Studio share them.
# --------------------------------------------------------------------------- #
PYTHON_KEYWORDS = set(keyword.kwlist)

# Names we refuse to let a model/table use.
RESERVED_NAMES = {
    "studio", "core", "auth", "db", "models", "blueprints", "lombik",
    "static", "templates", "tests", "user",
}

COLUMN_TYPES = {
    "String":     {"sqlalchemy": "db.String", "label": "String"},
    "Text":       {"sqlalchemy": "db.Text", "label": "Text"},
    "Integer":    {"sqlalchemy": "db.Integer", "label": "Integer"},
    "BigInteger": {"sqlalchemy": "db.BigInteger", "label": "Big Integer"},
    "Float":      {"sqlalchemy": "db.Float", "label": "Float"},
    "Numeric":    {"sqlalchemy": "db.Numeric", "label": "Numeric"},
    "Boolean":    {"sqlalchemy": "db.Boolean", "label": "Boolean"},
    "DateTime":   {"sqlalchemy": "db.DateTime", "label": "Date + Time"},
    "Date":       {"sqlalchemy": "db.Date", "label": "Date"},
    "Time":       {"sqlalchemy": "db.Time", "label": "Time"},
    "JSON":       {"sqlalchemy": "db.JSON", "label": "JSON"},
}

RELATIONSHIP_TYPES = ("one-to-many", "many-to-one", "one-to-one", "many-to-many")
LAZY_OPTIONS = ("select", "joined", "subquery", "dynamic", "noload", "raise")
ON_DELETE_ACTIONS = ("CASCADE", "SET NULL", "RESTRICT", "NO ACTION", "SET DEFAULT")


def sanitize_identifier(value: str) -> str:
    name = to_snake(value or "")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
        raise ValueError("Identifiers must be snake_case and start with a letter.")
    if name in PYTHON_KEYWORDS:
        raise ValueError("That name is a reserved Python keyword.")
    return name


def validate_model_name(name: str) -> str:
    snake = sanitize_identifier(name)
    table = plural(snake)
    if snake in RESERVED_NAMES or singularize(snake) in RESERVED_NAMES or table in RESERVED_NAMES:
        raise ValueError("That name is reserved.")
    return table


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


# --------------------------------------------------------------------------- #
# Code generation
# --------------------------------------------------------------------------- #
def _escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _build_default(spec: dict) -> str | None:
    kind = spec.get("default_kind")
    value = spec.get("default_value")
    if not kind or kind == "none":
        return None
    if kind == "utc_now":
        return "default=utc_now"
    if kind == "uuid4":
        return "default=lambda: str(uuid.uuid4())"
    if kind == "literal":
        return f"default={value}"
    if kind == "string":
        return f'default="{_escape(value or "")}"'
    if kind == "server_default":
        return f'server_default="{_escape(value or "")}"'
    return None


def build_column_line(spec: dict) -> str:
    name = sanitize_identifier(spec.get("name", ""))
    ctype = spec.get("type", "String")
    if ctype not in COLUMN_TYPES:
        raise ValueError(f"Unknown column type: {ctype}")

    args = []
    if ctype == "String":
        args.append(str(int(spec.get("length") or 255)))
    elif ctype == "Numeric":
        args.append(str(int(spec.get("precision") or 10)))
        args.append(str(int(spec.get("scale") or 2)))
    type_str = f"db.{ctype}" + (f"({', '.join(args)})" if args else "")

    parts = [type_str]

    fk = spec.get("fk") or {}
    if fk.get("table"):
        ref = f'db.ForeignKey("{fk["table"]}.{fk.get("column", "id")}"'
        if fk.get("ondelete"):
            ref += f', ondelete="{fk["ondelete"]}"'
        if fk.get("onupdate"):
            ref += f', onupdate="{fk["onupdate"]}"'
        ref += ")"
        parts.append(ref)

    if spec.get("primary_key"):
        parts.append("primary_key=True")
    if spec.get("nullable") is False:
        parts.append("nullable=False")
    if spec.get("unique"):
        parts.append("unique=True")
    if spec.get("index"):
        parts.append("index=True")

    default = _build_default(spec)
    if default:
        parts.append(default)

    return f"    {name} = db.Column({', '.join(parts)})\n"


def build_relationship_line(spec: dict) -> str:
    name = sanitize_identifier(spec.get("name", ""))
    target = spec.get("target")
    if not target:
        raise ValueError("Relationship target is required.")

    options = []
    if spec.get("uselist") is False:
        options.append("uselist=False")
    options.append(f"lazy='{spec.get('lazy', 'select')}'")
    if spec.get("secondary"):
        options.insert(0, f'secondary="{spec["secondary"]}"')

    return (
        f'    {name} = db.relationship("{target}", '
        f'back_populates="{spec.get("back_populates") or ""}", {", ".join(options)})\n'
    )


def generate_model_source(class_name: str, table_name: str, columns: list[dict]) -> str:
    lines = [
        "from lombik.utils import utc_now",
        "from db import db",
        "import uuid",
        "",
        "",
        f"class {class_name}(db.Model):",
        f'    __tablename__ = "{table_name}"',
        "",
        "    id = db.Column(",
        "        db.String(36),",
        "        primary_key=True,",
        "        default=lambda: str(uuid.uuid4())",
        "    )",
        "",
        "    # <LOMBIK:COLUMNS>",
    ]
    for col in columns:
        lines.append(build_column_line(col).rstrip("\n"))
    lines += [
        "    # </LOMBIK:COLUMNS>",
        "",
        "    created_at = db.Column(",
        "        db.DateTime(timezone=True),",
        "        default=utc_now",
        "    )",
        "",
        "    updated_at = db.Column(",
        "        db.DateTime(timezone=True),",
        "        default=utc_now",
        "    )",
        "",
        "    # <LOMBIK:RELATIONSHIPS>",
        "    # </LOMBIK:RELATIONSHIPS>",
    ]
    return "\n".join(lines) + "\n"


def _insert_line(path: Path, marker: str, name: str, line: str) -> bool:
    content = path.read_text(encoding="utf-8")
    if f"{name} =" in content:
        return False
    if marker not in content:
        raise RuntimeError(f"Missing {marker} marker in {path.name}")
    content = content.replace(marker, marker + "\n" + line.rstrip("\n"))
    path.write_text(content, encoding="utf-8")
    return True


def _remove_assignment(path: Path, name: str, func: str) -> bool:
    content = path.read_text(encoding="utf-8")
    for a in _find_assignments(content, func):
        if a["name"] != name:
            continue
        end = a["end"]
        if end < len(content) and content[end] == "\n":
            end += 1
        content = content[:a["start"]] + content[end:]
        path.write_text(content, encoding="utf-8")
        return True
    return False


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


# --------------------------------------------------------------------------- #
# Model CRUD (file-level)
# --------------------------------------------------------------------------- #
def create_model(name: str, columns: list[dict]) -> dict:
    try:
        validate_model_name(name)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    table_name = plural(to_snake(name))
    class_name = to_camel(singularize(to_snake(name)))
    module = table_name
    path = model_path(module)
    if path.exists():
        return {"ok": False, "error": "A model with that name already exists."}

    try:
        source = generate_model_source(class_name, table_name, columns)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    path.write_text(source, encoding="utf-8")
    sync_models_init()

    try:
        importlib.import_module(f"models.{module}")
    except Exception:
        pass

    return {"ok": True, "module": module, "class_name": class_name, "table_name": table_name}


def delete_model(module: str) -> dict:
    path = model_path(module)
    if not path.exists():
        return {"ok": False, "error": "Model not found."}
    path.unlink()
    sync_models_init()
    return {"ok": True}


def add_column(module: str, spec: dict) -> dict:
    path = model_path(module)
    if not path.exists():
        return {"ok": False, "error": "Model not found."}
    try:
        line = build_column_line(spec)
        _insert_line(path, "# <LOMBIK:COLUMNS>", sanitize_identifier(spec["name"]), line)
        return {"ok": True}
    except (ValueError, RuntimeError) as exc:
        return {"ok": False, "error": str(exc)}


def remove_column(module: str, name: str) -> dict:
    path = model_path(module)
    if not path.exists():
        return {"ok": False, "error": "Model not found."}
    if _remove_assignment(path, name, "db.Column"):
        return {"ok": True}
    return {"ok": False, "error": "Column not found."}


def add_relationship_line(module: str, spec: dict) -> dict:
    path = model_path(module)
    if not path.exists():
        return {"ok": False, "error": "Model not found."}
    try:
        line = build_relationship_line(spec)
        _insert_line(path, "# <LOMBIK:RELATIONSHIPS>", sanitize_identifier(spec["name"]), line)
        return {"ok": True}
    except (ValueError, RuntimeError) as exc:
        return {"ok": False, "error": str(exc)}


def remove_relationship(module: str, name: str) -> dict:
    path = model_path(module)
    if not path.exists():
        return {"ok": False, "error": "Model not found."}
    if _remove_assignment(path, name, "db.relationship"):
        return {"ok": True}
    return {"ok": False, "error": "Relationship not found."}


def create_association_table(table_name: str, left_table: str, right_table: str, left_fk: str, right_fk: str) -> None:
    path = model_path(table_name)
    if path.exists():
        return
    content = (
        "from db import db\n\n\n"
        f"class {to_camel(table_name)}(db.Model):\n"
        f'    __tablename__ = "{table_name}"\n\n'
        "    # Composite primary key\n"
        f'    {left_fk} = db.Column(db.String(36), db.ForeignKey("{left_table}.id"), primary_key=True)\n'
        f'    {right_fk} = db.Column(db.String(36), db.ForeignKey("{right_table}.id"), primary_key=True)\n\n'
        "    # <LOMBIK:COLUMNS>\n"
        "    # </LOMBIK:COLUMNS>\n\n"
        "    # <LOMBIK:RELATIONSHIPS>\n"
        "    # </LOMBIK:RELATIONSHIPS>\n"
    )
    path.write_text(content, encoding="utf-8")


def create_relationship(parent: str, child: str, rel_type: str = "one-to-many", fk_field: str | None = None, lazy: str = "select") -> dict:
    if rel_type not in RELATIONSHIP_TYPES:
        return {"ok": False, "error": "Unknown relationship type."}

    parent_file = resolve_model_file(parent)
    child_file = resolve_model_file(child)
    if not parent_file or not child_file:
        return {"ok": False, "error": "One or both models do not exist."}

    p = parse_model_file(parent_file)
    c = parse_model_file(child_file)
    if not p or not c:
        return {"ok": False, "error": "Could not parse models."}

    if rel_type == "many-to-one":
        parent_file, child_file = child_file, parent_file
        p, c = c, p

    if fk_field is None:
        fk_field = f"{to_snake(p['class_name'])}_id"

    try:
        if rel_type in ("one-to-many", "many-to-one"):
            _insert_line(
                child_file, "# <LOMBIK:COLUMNS>", fk_field,
                build_column_line({
                    "name": fk_field, "type": "String", "length": 36,
                    "fk": {"table": p["table_name"], "column": "id"}, "index": True,
                }),
            )
            parent_rel = plural(to_snake(c["class_name"]))
            child_rel = to_snake(p["class_name"])
            _insert_line(
                child_file, "# <LOMBIK:RELATIONSHIPS>", child_rel,
                build_relationship_line({"name": child_rel, "target": p["class_name"], "back_populates": parent_rel, "uselist": False, "lazy": lazy}),
            )
            _insert_line(
                parent_file, "# <LOMBIK:RELATIONSHIPS>", parent_rel,
                build_relationship_line({"name": parent_rel, "target": c["class_name"], "back_populates": child_rel, "uselist": True, "lazy": lazy}),
            )

        elif rel_type == "one-to-one":
            _insert_line(
                child_file, "# <LOMBIK:COLUMNS>", fk_field,
                build_column_line({
                    "name": fk_field, "type": "String", "length": 36,
                    "fk": {"table": p["table_name"], "column": "id"}, "unique": True, "index": True,
                }),
            )
            parent_rel = to_snake(c["class_name"])
            child_rel = to_snake(p["class_name"])
            _insert_line(
                child_file, "# <LOMBIK:RELATIONSHIPS>", child_rel,
                build_relationship_line({"name": child_rel, "target": p["class_name"], "back_populates": parent_rel, "uselist": False, "lazy": lazy}),
            )
            _insert_line(
                parent_file, "# <LOMBIK:RELATIONSHIPS>", parent_rel,
                build_relationship_line({"name": parent_rel, "target": c["class_name"], "back_populates": child_rel, "uselist": False, "lazy": lazy}),
            )

        elif rel_type == "many-to-many":
            assoc_table = f"{p['table_name']}_{c['table_name']}"
            left_fk = f"{to_snake(p['class_name'])}_id"
            right_fk = f"{to_snake(c['class_name'])}_id"
            create_association_table(assoc_table, p["table_name"], c["table_name"], left_fk, right_fk)
            sync_models_init()

            parent_rel = plural(to_snake(c["class_name"]))
            child_rel = plural(to_snake(p["class_name"]))
            _insert_line(
                parent_file, "# <LOMBIK:RELATIONSHIPS>", parent_rel,
                build_relationship_line({"name": parent_rel, "target": c["class_name"], "back_populates": child_rel, "uselist": True, "lazy": lazy, "secondary": assoc_table}),
            )
            _insert_line(
                child_file, "# <LOMBIK:RELATIONSHIPS>", child_rel,
                build_relationship_line({"name": child_rel, "target": p["class_name"], "back_populates": parent_rel, "uselist": True, "lazy": lazy, "secondary": assoc_table}),
            )

        return {"ok": True}
    except (ValueError, RuntimeError) as exc:
        return {"ok": False, "error": str(exc)}


# --------------------------------------------------------------------------- #
# Live database helpers (Data Browser + SQL Console)
# --------------------------------------------------------------------------- #
def _table(name: str):
    if name in db.metadata.tables:
        return db.metadata.tables[name]
    return Table(name, MetaData(), autoload_with=db.engine)


def list_tables() -> list[str]:
    insp = inspect(db.engine)
    return sorted(t for t in insp.get_table_names() if t != "alembic_version")


def table_columns(table: str) -> list[dict]:
    t = _table(table)
    pk = {c.name for c in t.primary_key.columns}
    fks = {fk.parent.name: f"{fk.column.table.name}.{fk.column.name}" for fk in t.foreign_keys}
    cols = []
    for c in t.columns:
        cols.append({
            "name": c.name,
            "type": str(c.type),
            "nullable": c.nullable,
            "primary_key": c.name in pk,
            "foreign_key": fks.get(c.name),
        })
    return cols


def _jsonable(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value)
    return str(value)


def fetch_rows(table: str, page: int = 1, per_page: int = 50) -> dict:
    t = _table(table)
    per_page = max(1, min(per_page, 500))
    page = max(1, page)
    offset = (page - 1) * per_page
    total = db.session.execute(select(func.count()).select_from(t)).scalar() or 0
    result = db.session.execute(select(t).limit(per_page).offset(offset))
    columns = [c.name for c in t.columns]
    rows = [[_jsonable(v) for v in row] for row in result.fetchall()]
    pages = max(1, math.ceil(total / per_page)) if total else 1
    return {"columns": columns, "rows": rows, "total": total, "page": page, "per_page": per_page, "pages": pages}


def _coerce(column, value):
    if value is None or value == "":
        return None
    py_type = getattr(column.type, "python_type", None)
    if py_type is bool and not isinstance(value, bool):
        return str(value).lower() in ("1", "true", "yes", "on")
    if py_type is int and not isinstance(value, int):
        try:
            return int(value)
        except (TypeError, ValueError):
            return value
    if py_type is float and not isinstance(value, float):
        try:
            return float(value)
        except (TypeError, ValueError):
            return value
    return value


def _pk_where(t, pk: dict):
    pk_cols = [c.name for c in t.primary_key.columns]
    if not pk_cols:
        raise ValueError("Table has no primary key.")
    return pk_cols, and_(*(t.c[pk_c] == _coerce(t.c[pk_c], pk.get(pk_c)) for pk_c in pk_cols))


def insert_row(table: str, data: dict) -> dict:
    t = _table(table)
    values = {c.name: _coerce(c, data[c.name]) for c in t.columns if c.name in data}
    try:
        db.session.execute(insert(t).values(**values))
        db.session.commit()
        return {"ok": True}
    except Exception as exc:
        db.session.rollback()
        return {"ok": False, "error": str(exc)}


def update_row(table: str, pk: dict, data: dict) -> dict:
    t = _table(table)
    try:
        pk_cols, where = _pk_where(t, pk)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    values = {c.name: _coerce(c, data[c.name]) for c in t.columns if c.name in data and c.name not in pk_cols}
    try:
        db.session.execute(update(t).where(where).values(**values))
        db.session.commit()
        return {"ok": True}
    except Exception as exc:
        db.session.rollback()
        return {"ok": False, "error": str(exc)}


def delete_row(table: str, pk: dict) -> dict:
    t = _table(table)
    try:
        _, where = _pk_where(t, pk)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    try:
        db.session.execute(delete(t).where(where))
        db.session.commit()
        return {"ok": True}
    except Exception as exc:
        db.session.rollback()
        return {"ok": False, "error": str(exc)}


_READ_PREFIXES = ("SELECT", "WITH", "SHOW", "PRAGMA", "EXPLAIN", "DESCRIBE")


def run_sql(sql: str, write: bool = False) -> dict:
    statement = (sql or "").strip()
    if not statement:
        return {"ok": False, "error": "Empty query."}

    upper = statement.lstrip().upper()
    is_read = upper.startswith(_READ_PREFIXES)

    if write and not is_read:
        try:
            result = db.session.execute(text(statement))
            db.session.commit()
            return {"ok": True, "rowcount": getattr(result, "rowcount", 0), "columns": [], "rows": []}
        except Exception as exc:
            db.session.rollback()
            return {"ok": False, "error": str(exc)}

    if not is_read:
        return {"ok": False, "error": "Only read statements are allowed unless write mode is enabled."}

    try:
        result = db.session.execute(text(statement))
        rows = result.fetchall()
        columns = list(result.keys())
        data = [[_jsonable(v) for v in row] for row in rows]
        return {"ok": True, "columns": columns, "rows": data, "rowcount": len(rows)}
    except Exception as exc:
        db.session.rollback()
        return {"ok": False, "error": str(exc)}


# --------------------------------------------------------------------------- #
# Migrations
# --------------------------------------------------------------------------- #
def run_migration(message: str = "studio migration") -> dict:
    commands = []
    if not (PROJECT_ROOT / "migrations" / "alembic.ini").exists():
        commands.append(["flask", "db", "init"])
    commands += [
        ["flask", "db", "migrate", "-m", message or "studio migration"],
        ["flask", "db", "upgrade"],
        ["flask", "triggers", "create"],
    ]
    output = []
    for cmd in commands:
        output.append("$ " + " ".join(cmd))
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
                timeout=600,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "output": "\n".join(output), "error": "Command timed out."}
        except OSError as exc:
            return {"ok": False, "output": "\n".join(output), "error": str(exc)}

        output.append(result.stdout or "")
        output.append(result.stderr or "")
        if result.returncode != 0:
            return {"ok": False, "output": "\n".join(output), "error": f"Command failed with exit code {result.returncode}."}

    return {"ok": True, "output": "\n".join(output)}
