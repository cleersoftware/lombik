"""
CRUD generator used by both the ``flask crud`` command and Lombik Studio.

This module lives inside a generated app so Studio can preview and generate
CRUD blueprints without shelling out to the Lombik CLI.
"""
from __future__ import annotations

import re
from pathlib import Path

from lombik import studio
from lombik.strings import plural, singularize, to_camel, to_snake

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CRUD_SKIP_COLUMNS = {
    "id", "created_at", "updated_at", "deactivated_at", "delete_at",
}
CRUD_SENSITIVE_COLUMNS = {
    "password", "password_hash", "reset_token", "reset_token_hash",
    "reset_token_expires_at", "failed_login_attempts", "locked_until",
    "last_seen",
}
CRUD_LABEL_FIELDS = ("name", "title", "username", "email", "label", "slug")

# Column names that should become a SelectField with these Lombik constants.
ENUM_COLUMNS = {
    "role": ("USER_ROLES", False),
    "status": ("USER_STATUSES", False),
    "timezone": ("TIMEZONES", True),
    "country": ("COUNTRIES", False),
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _label(name: str) -> str:
    return name.replace("_", " ").title()


def _required(col: dict) -> bool:
    return (not col.get("nullable")) and not col.get("default")


def _editable_columns(columns: list[dict]) -> list[dict]:
    return [
        c for c in columns
        if c["name"] not in CRUD_SKIP_COLUMNS
        and c["name"] not in CRUD_SENSITIVE_COLUMNS
        and not c.get("primary_key")
    ]


def _display_columns(columns: list[dict]) -> list[dict]:
    return [
        c for c in columns
        if c["name"] not in CRUD_SENSITIVE_COLUMNS
        and c["name"] not in {"updated_at", "deactivated_at", "delete_at"}
    ]


def _column_length(col: dict) -> int | None:
    match = re.search(r"\((\d+)", col.get("type_display") or "")
    return int(match.group(1)) if match else None


def _model_index() -> dict[str, str]:
    return {m["table_name"]: m["class_name"] for m in studio.list_models()}


def _class_for_table(table: str, model_index: dict[str, str]) -> str:
    return model_index.get(table) or to_camel(singularize(to_snake(table)))


def _label_attr(class_name: str) -> str:
    path = studio.resolve_model_file(class_name)
    if path:
        info = studio.parse_model_file(path)
        if info:
            for name in CRUD_LABEL_FIELDS:
                if any(c["name"] == name for c in info["columns"]):
                    return name
            for c in info["columns"]:
                if c["type"] == "String" and c["name"] not in CRUD_SKIP_COLUMNS:
                    return c["name"]
    return "id"


# --------------------------------------------------------------------------- #
# Code generation
# --------------------------------------------------------------------------- #
def _form_field_code(
    col: dict,
    fk_meta: dict[str, tuple[str, str]],
    used_constants: set[str],
) -> str:
    name = col["name"]
    label = _label(name)
    required = _required(col)
    ctype = col.get("type")

    if col.get("fk") and name in fk_meta:
        related_class, label_attr = fk_meta[name]
        return (
            f'    fields.append(SelectField(\n'
            f'        name="{name}",\n'
            f'        label="{label}",\n'
            f'        required={required},\n'
            f'        options=_related_options({related_class}, label_attrs=["{label_attr}"]),\n'
            f'        value=_val(item, "{name}", ""),\n'
            f'    ))'
        )

    if name in ENUM_COLUMNS and ctype in ("String", "Text"):
        const, sort_needed = ENUM_COLUMNS[name]
        used_constants.add(const)
        option_expr = f"sorted({const})" if sort_needed else const
        return (
            f'    fields.append(SelectField(\n'
            f'        name="{name}",\n'
            f'        label="{label}",\n'
            f'        required={required},\n'
            f'        options=[(v, v) for v in {option_expr}],\n'
            f'        value=_val(item, "{name}", ""),\n'
            f'    ))'
        )

    if ctype == "Boolean":
        return (
            f'    fields.append(CheckboxField(\n'
            f'        name="{name}",\n'
            f'        label="{label}",\n'
            f'        required={required},\n'
            f'        value=bool(_val(item, "{name}", False)),\n'
            f'    ))'
        )

    if ctype in ("Text", "JSON"):
        return (
            f'    fields.append(TextareaField(\n'
            f'        name="{name}",\n'
            f'        label="{label}",\n'
            f'        required={required},\n'
            f'        value=_val(item, "{name}", ""),\n'
            f'    ))'
        )

    field_type = "text"
    extra = ""
    if ctype in ("Integer", "BigInteger"):
        field_type = "number"
    elif ctype in ("Float", "Numeric"):
        field_type = "number"
        extra = ', step="any"'
    elif ctype == "DateTime":
        field_type = "datetime-local"
    elif ctype == "Date":
        field_type = "date"
    elif ctype == "Time":
        field_type = "time"

    max_length = _column_length(col) if ctype == "String" else None
    max_length_kw = f", max_length={max_length}" if max_length else ""

    return (
        f'    fields.append(InputField(\n'
        f'        name="{name}",\n'
        f'        label="{label}",\n'
        f'        field_type="{field_type}"{extra},\n'
        f'        required={required}{max_length_kw},\n'
        f'        value=_val(item, "{name}", ""),\n'
        f'    ))'
    )


_INIT_TEMPLATE = '''from flask import Blueprint

__BP__ = Blueprint(
    "__BP__",
    __name__,
    template_folder="templates",
    static_folder="static",
)
'''

_QUERIES_TEMPLATE = '''from datetime import date, datetime, time
import json

from models import __CLASS__
from db import db
from lombik.responses import Result


COLUMNS = [
__COLUMNS__
]

FIELDS = {
__FIELDS__
}

RELATIONSHIPS = [
__RELATIONSHIPS__
]


def _coerce(value, type_):
    if value is None or value == "":
        return None
    if type_ == "Boolean":
        return str(value).lower() in ("1", "true", "yes", "on")
    if type_ in ("Integer", "BigInteger"):
        try:
            return int(value)
        except (TypeError, ValueError):
            return value
    if type_ in ("Float", "Numeric"):
        try:
            return float(value)
        except (TypeError, ValueError):
            return value
    if type_ == "JSON":
        if isinstance(value, str):
            return json.loads(value)
        return value
    if type_ == "DateTime":
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return value
    if type_ == "Date":
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            return value
    if type_ == "Time":
        try:
            return time.fromisoformat(value)
        except (TypeError, ValueError):
            return value
    return value


def _apply(instance, data):
    for name, meta in FIELDS.items():
        if name in data:
            setattr(instance, name, _coerce(data.get(name), meta["type"]))
    return instance


def _related_options(model, label_attrs=("name",)):
    options = []
    for row in model.query.all():
        label = None
        for attr in label_attrs:
            value = getattr(row, attr, None)
            if value not in (None, ""):
                label = value
                break
        options.append((str(getattr(row, "id")), str(label if label is not None else getattr(row, "id"))))
    return options


def get_all___MODULE__():
    return __CLASS__.query.order_by(__CLASS__.created_at.desc()).all()


def get___MODEL_VAR__(item_id):
    return __CLASS__.query.filter_by(id=item_id).first()


def create___MODEL_VAR__(data):
    item = __CLASS__()
    _apply(item, data)
    try:
        db.session.add(item)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return Result(success=False, message="__CLASS__ could not be created.")
    return Result(success=True, data={"id": item.id}, message="__CLASS__ created.")


def update___MODEL_VAR__(item, data):
    _apply(item, data)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return Result(success=False, message="__CLASS__ could not be updated.")
    return Result(success=True, data={"id": item.id}, message="__CLASS__ updated.")


def delete___MODEL_VAR__(item):
    try:
        db.session.delete(item)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return Result(success=False, message="__CLASS__ could not be deleted.")
    return Result(success=True, data={}, message="__CLASS__ deleted.")
'''

_FORMS_TEMPLATE = '''from lombik.forms import Form, InputField, SelectField, CheckboxField, TextareaField
from .queries import _related_options
__RELATED_IMPORTS__
__ENUM_IMPORTS__


def _val(item, name, default=""):
    return getattr(item, name, default) if item else default


def get___MODEL_VAR___form(item=None):
    fields = []

__FORM_FIELDS__

    return Form(fields)
'''

_ROUTES_TEMPLATE = '''from flask import render_template, abort

from . import __BP__
from .queries import COLUMNS, RELATIONSHIPS, get_all___MODULE__, get___MODEL_VAR__
from .forms import get___MODEL_VAR___form


@__BP__.get("/")
def index():
    items = get_all___MODULE__()
    return render_template("__MODULE__/index.html", selected="__MODULE__", items=items, columns=COLUMNS)


@__BP__.get("/new")
def new():
    form = get___MODEL_VAR___form()
    return render_template("__MODULE__/form.html", form=form, item=None, mode="new", columns=COLUMNS)


@__BP__.get("/<item_id>")
def detail(item_id):
    item = get___MODEL_VAR__(item_id)
    if not item:
        abort(404)
    return render_template(
        "__MODULE__/detail.html",
        item=item,
        columns=COLUMNS,
        relationships=RELATIONSHIPS,
    )


@__BP__.get("/<item_id>/edit")
def edit(item_id):
    item = get___MODEL_VAR__(item_id)
    if not item:
        abort(404)
    form = get___MODEL_VAR___form(item)
    return render_template("__MODULE__/form.html", form=form, item=item, mode="edit", columns=COLUMNS)
'''

_ACTIONS_TEMPLATE = '''from flask import render_template, request, redirect, url_for, abort

from . import __BP__
from .forms import get___MODEL_VAR___form
from .queries import get___MODEL_VAR__, create___MODEL_VAR__, update___MODEL_VAR__, delete___MODEL_VAR__
from lombik.flash import Flash


@__BP__.post("/new")
def create():
    form = get___MODEL_VAR___form()
    for field in form.fields:
        if field.type == "checkbox":
            field.value = request.form.get(field.name) in ("1", "true", "on", "yes")
        else:
            field.value = request.form.get(field.name, field.value)

    if not form.validate():
        Flash.error("Please fix the errors below.")
        return render_template("__MODULE__/form.html", form=form, item=None, mode="new"), 400

    res = create___MODEL_VAR__(form.data)
    if not res.success:
        Flash.error(res.message)
        return render_template("__MODULE__/form.html", form=form, item=None, mode="new"), 400

    Flash.ok(res.message)
    return redirect(url_for("__BP__.detail", item_id=res.data["id"]))


@__BP__.post("/<item_id>/edit")
def update(item_id):
    item = get___MODEL_VAR__(item_id)
    if not item:
        abort(404)

    form = get___MODEL_VAR___form(item)
    for field in form.fields:
        if field.type == "checkbox":
            field.value = request.form.get(field.name) in ("1", "true", "on", "yes")
        else:
            field.value = request.form.get(field.name, field.value)

    if not form.validate():
        Flash.error("Please fix the errors below.")
        return render_template("__MODULE__/form.html", form=form, item=item, mode="edit"), 400

    res = update___MODEL_VAR__(item, form.data)
    if not res.success:
        Flash.error(res.message)
        return render_template("__MODULE__/form.html", form=form, item=item, mode="edit"), 400

    Flash.ok(res.message)
    return redirect(url_for("__BP__.detail", item_id=item.id))


@__BP__.post("/<item_id>/delete")
def delete(item_id):
    item = get___MODEL_VAR__(item_id)
    if not item:
        abort(404)

    res = delete___MODEL_VAR__(item)
    if not res.success:
        Flash.error(res.message)
        return redirect(url_for("__BP__.detail", item_id=item.id))

    Flash.ok(res.message)
    return redirect(url_for("__BP__.index"))
'''

_INDEX_TEMPLATE = '''{% extends 'base/base.html' %}

{% block title %}__CLASS__ list{% endblock %}

{% block content %}
<section class="w-full h-full px-8 py-8">
    <div class="max-w-6xl mx-auto">
        <div class="flex items-center justify-between mb-8">
            <div>
                <h1 class="text-2xl font-bold text-zinc-800 dark:text-zinc-100">__CLASS__</h1>
                <p class="text-sm text-zinc-500 dark:text-zinc-400 mt-1">__TABLE__</p>
            </div>
            <a href="{{ url_for('__BP__.new') }}"
               class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-white text-sm font-medium hover:opacity-90 transition">
                <ion-icon name="add-outline"></ion-icon> New __CLASS__
            </a>
        </div>

        <div class="rounded-3xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-neutral-800 overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="text-left text-xs uppercase tracking-wide text-zinc-400 dark:text-zinc-500 border-b border-zinc-100 dark:border-zinc-700/60">
                            {% for col in columns %}
                            <th class="px-4 py-3 font-medium">{{ col.label }}</th>
                            {% endfor %}
                            <th class="px-4 py-3 font-medium text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-zinc-100 dark:divide-zinc-700/60">
                        {% for item in items %}
                        <tr class="hover:bg-zinc-50 dark:hover:bg-zinc-700/30 transition">
                            {% for col in columns %}
                            <td class="px-4 py-3 text-zinc-600 dark:text-zinc-300 truncate">{{ item[col.name] }}</td>
                            {% endfor %}
                            <td class="px-4 py-3">
                                <div class="flex items-center justify-end gap-1">
                                    <a href="{{ url_for('__BP__.detail', item_id=item.id) }}" class="text-zinc-400 hover:text-primary transition" title="View">
                                        <ion-icon name="eye-outline" class="text-lg"></ion-icon>
                                    </a>
                                    <a href="{{ url_for('__BP__.edit', item_id=item.id) }}" class="text-zinc-400 hover:text-primary transition" title="Edit">
                                        <ion-icon name="create-outline" class="text-lg"></ion-icon>
                                    </a>
                                    <form method="POST" action="{{ url_for('__BP__.delete', item_id=item.id) }}"
                                          onsubmit="return confirm('Delete this item?');" class="m-0">
                                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                                        <button type="submit" class="text-zinc-400 hover:text-red-500 transition" title="Delete">
                                            <ion-icon name="trash-outline" class="text-lg"></ion-icon>
                                        </button>
                                    </form>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</section>
{% endblock %}
'''

_DETAIL_TEMPLATE = '''{% extends 'base/base.html' %}

{% block title %}__CLASS__ detail{% endblock %}

{% block content %}
<section class="w-full h-full px-8 py-8">
    <div class="max-w-4xl mx-auto">
        <div class="flex items-start justify-between mb-8">
            <div>
                <a href="{{ url_for('__BP__.index') }}" class="inline-flex items-center gap-1.5 text-sm text-zinc-500 dark:text-zinc-400 hover:text-primary transition mb-3">
                    <ion-icon name="arrow-back-outline"></ion-icon> __CLASS__
                </a>
                <h1 class="text-2xl font-bold text-zinc-800 dark:text-zinc-100">__CLASS__ detail</h1>
            </div>
            <div class="flex items-center gap-2">
                <a href="{{ url_for('__BP__.edit', item_id=item.id) }}"
                   class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-zinc-200 dark:border-zinc-700 text-sm font-medium hover:bg-zinc-100 dark:hover:bg-zinc-700/60 transition">
                    <ion-icon name="create-outline"></ion-icon> Edit
                </a>
                <form method="POST" action="{{ url_for('__BP__.delete', item_id=item.id) }}"
                      onsubmit="return confirm('Delete this item?');" class="m-0">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    <button type="submit"
                            class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-red-200 dark:border-red-500/30 text-red-600 dark:text-red-400 text-sm font-medium hover:bg-red-50 dark:hover:bg-red-500/10 transition">
                        <ion-icon name="trash-outline"></ion-icon> Delete
                    </button>
                </form>
            </div>
        </div>

        <dl class="rounded-3xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-neutral-800 overflow-hidden mb-8">
            {% for col in columns %}
            <div class="grid grid-cols-3 gap-4 px-6 py-4 border-b border-zinc-100 dark:border-zinc-700/60">
                <dt class="text-sm font-medium text-zinc-500 dark:text-zinc-400">{{ col.label }}</dt>
                <dd class="col-span-2 text-sm text-zinc-800 dark:text-zinc-100">{{ item[col.name] }}</dd>
            </div>
            {% endfor %}
        </dl>

        {% if relationships %}
        <h2 class="text-base font-semibold text-zinc-800 dark:text-zinc-100 mb-4">Related records</h2>
        <div class="space-y-4">
            {% for rel in relationships %}
            <div class="rounded-3xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-neutral-800 p-6">
                <h3 class="text-sm font-semibold text-zinc-800 dark:text-zinc-100 mb-3">{{ rel.label }}</h3>
                {% set related = item[rel.name] %}
                {% if rel.uselist %}
                    {% if related %}
                    <ul class="space-y-1">
                        {% for obj in related %}
                        <li class="text-sm text-zinc-600 dark:text-zinc-300">{{ obj[rel.target_label] }}</li>
                        {% endfor %}
                    </ul>
                    {% else %}
                    <p class="text-sm text-zinc-400 dark:text-zinc-500">No records.</p>
                    {% endif %}
                {% else %}
                    <p class="text-sm text-zinc-600 dark:text-zinc-300">{{ related[rel.target_label] if related else "" }}</p>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</section>
{% endblock %}
'''

_FORM_TEMPLATE = '''{% extends 'base/base.html' %}

{% block title %}__CLASS__ form{% endblock %}

{% block content %}
<section class="w-full h-full px-8 py-8">
    <div class="max-w-2xl mx-auto">
        <div class="mb-8">
            <a href="{{ url_for('__BP__.index') }}" class="inline-flex items-center gap-1.5 text-sm text-zinc-500 dark:text-zinc-400 hover:text-primary transition mb-3">
                <ion-icon name="arrow-back-outline"></ion-icon> __CLASS__
            </a>
            <h1 class="text-2xl font-bold text-zinc-800 dark:text-zinc-100">{% if mode == 'new' %}New __CLASS__{% else %}Edit __CLASS__{% endif %}</h1>
        </div>

        <form method="POST"
              action="{% if mode == 'new' %}{{ url_for('__BP__.create') }}{% else %}{{ url_for('__BP__.update', item_id=item.id) }}{% endif %}"
              class="rounded-3xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-neutral-800 p-6 space-y-4">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

            {% for field in form.fields %}
                {% include "components/form_field.html" %}
            {% endfor %}

            <div class="flex justify-end gap-3 pt-4">
                <a href="{{ url_for('__BP__.index') }}"
                   class="px-4 py-2.5 rounded-xl border border-stone-300 dark:border-zinc-600 text-sm text-zinc-600 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-700/60 transition">
                    Cancel
                </a>
                <button type="submit"
                        class="px-4 py-2.5 rounded-xl bg-primary text-white text-sm font-medium hover:opacity-90 transition">
                    Save
                </button>
            </div>
        </form>
    </div>
</section>
{% endblock %}
'''


def _replace_all(template: str, **values: str) -> str:
    for key, value in values.items():
        template = template.replace(key, value)
    return template


def _build_files(info: dict) -> dict:
    """Return {module, files: {relative_path: content}} for a parsed model."""
    class_name = info["class_name"]
    table_name = info["table_name"]
    module = to_snake(plural(singularize(to_snake(info["module"]))))
    bp_name = f"{module}_bp"
    model_var = to_snake(class_name)

    editable = _editable_columns(info["columns"])
    display = _display_columns(info["columns"])

    model_index = _model_index()
    fk_meta: dict[str, tuple[str, str]] = {}
    for col in editable:
        if col.get("fk"):
            related_class = _class_for_table(col["fk"]["table"], model_index)
            fk_meta[col["name"]] = (related_class, _label_attr(related_class))

    used_constants: set[str] = set()
    form_fields = []
    for col in editable:
        form_fields.append(_form_field_code(col, fk_meta, used_constants))

    related_classes = sorted({cls for cls, _ in fk_meta.values() if cls != class_name})
    related_imports = "\n".join(f"from models import {cls}" for cls in related_classes)
    enum_imports = ""
    if used_constants:
        enum_imports = "from lombik.constants import " + ", ".join(sorted(used_constants))

    # Columns / fields / relationships snippets.
    column_lines = "\n".join(
        f'    {{"name": "{c["name"]}", "label": "{_label(c["name"])}", "type": "{c["type"]}"}},'
        for c in display
    )
    field_lines = "\n".join(
        f'    "{c["name"]}": {{"type": "{c["type"]}"}},'
        for c in editable
    )

    relationships = []
    for rel in info["relationships"]:
        target_label = _label_attr(rel["target"])
        relationships.append(
            f'    {{"name": "{rel["name"]}", "label": "{_label(rel["name"])}", '
            f'"uselist": {rel["uselist"]}, "target": "{rel["target"]}", '
            f'"target_label": "{target_label}"}},'
        )
    relationship_lines = "\n".join(relationships)

    if not column_lines:
        column_lines = "    # no display columns"
    if not field_lines:
        field_lines = "    # no editable fields"
    if not relationship_lines:
        relationship_lines = "    # no relationships"

    common = {
        "__BP__": bp_name,
        "__CLASS__": class_name,
        "__TABLE__": table_name,
        "__MODULE__": module,
        "__MODEL_VAR__": model_var,
    }

    files = {
        f"blueprints/{module}/__init__.py": _replace_all(_INIT_TEMPLATE, **common),
        f"blueprints/{module}/queries.py": _replace_all(
            _QUERIES_TEMPLATE,
            __COLUMNS__=column_lines,
            __FIELDS__=field_lines,
            __RELATIONSHIPS__=relationship_lines,
            **common,
        ),
        f"blueprints/{module}/forms.py": _replace_all(
            _FORMS_TEMPLATE,
            __RELATED_IMPORTS__=related_imports,
            __ENUM_IMPORTS__=enum_imports,
            __FORM_FIELDS__="\n\n".join(form_fields) if form_fields else "    pass",
            **common,
        ),
        f"blueprints/{module}/routes.py": _replace_all(_ROUTES_TEMPLATE, **common),
        f"blueprints/{module}/actions.py": _replace_all(_ACTIONS_TEMPLATE, **common),
        f"templates/{module}/index.html": _replace_all(_INDEX_TEMPLATE, **common),
        f"templates/{module}/detail.html": _replace_all(_DETAIL_TEMPLATE, **common),
        f"templates/{module}/form.html": _replace_all(_FORM_TEMPLATE, **common),
    }

    return {"module": module, "class_name": class_name, "files": files}


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def resolve_model(name: str):
    path = studio.resolve_model_file(name)
    if not path:
        return None
    return studio.parse_model_file(path)


def preview_crud(name: str) -> dict:
    info = resolve_model(name)
    if not info:
        return {"ok": False, "error": f"Model '{name}' not found or unparsable."}

    built = _build_files(info)
    module = built["module"]
    exists = (PROJECT_ROOT / "blueprints" / module).exists()

    return {
        "ok": True,
        "module": module,
        "class_name": built["class_name"],
        "files": built["files"],
        "exists": exists,
    }


def generate_crud(name: str) -> dict:
    preview = preview_crud(name)
    if not preview.get("ok"):
        return preview

    module = preview["module"]
    if preview.get("exists"):
        return {"ok": False, "error": f"Module '{module}' already exists. Remove it first."}

    # Make sure `from models import <Class>` will work in generated code.
    studio.sync_models_init()

    for rel_path, content in preview["files"].items():
        path = PROJECT_ROOT / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    return {
        "ok": True,
        "module": module,
        "class_name": preview["class_name"],
        "files": preview["files"],
        "message": f"Created CRUD module: {module}",
    }
