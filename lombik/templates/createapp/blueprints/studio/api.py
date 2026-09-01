"""JSON API for Lombik Studio.

Every endpoint in this module is reached through the ``studio_bp`` blueprint,
whose ``before_request`` hook restricts access to superusers. The functions
here are thin HTTP adapters over the service layer in ``lombik.studio``.
"""
from flask import jsonify, request

from . import studio_bp
from lombik import studio


def _payload() -> dict:
    """Return the request body as a dict (JSON preferred, form fallback)."""
    data = request.get_json(silent=True)
    if data is None:
        data = request.form.to_dict()
    return data or {}


def _json(result, status: int = 200):
    """Serialize a service-layer result and pick an appropriate status."""
    if isinstance(result, dict) and result.get("ok") is False:
        return jsonify(result), 400
    return jsonify(result), status


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
@studio_bp.get("/api/models")
def api_list_models():
    return jsonify(studio.list_models())


@studio_bp.post("/api/models")
def api_create_model():
    data = _payload()
    columns = data.get("columns") or []

    # Tolerate form-encoded submissions where ``columns`` arrives as a string.
    if isinstance(columns, str):
        import json

        columns = json.loads(columns) if columns else []

    result = studio.create_model(data.get("name", ""), columns)
    return _json(result, 201 if result.get("ok") else 400)


@studio_bp.get("/api/models/<module>")
def api_get_model(module):
    info = studio.parse_model_file(studio.model_path(module))
    if not info:
        return jsonify({"ok": False, "error": "Model not found."}), 404
    return jsonify(info)


@studio_bp.delete("/api/models/<module>")
def api_delete_model(module):
    return _json(studio.delete_model(module))


@studio_bp.post("/api/models/<module>/columns")
def api_add_column(module):
    return _json(studio.add_column(module, _payload()))


@studio_bp.delete("/api/models/<module>/columns/<name>")
def api_remove_column(module, name):
    return _json(studio.remove_column(module, name))


@studio_bp.post("/api/models/<module>/relationships")
def api_add_relationship(module):
    return _json(studio.add_relationship_line(module, _payload()))


@studio_bp.delete("/api/models/<module>/relationships/<name>")
def api_remove_relationship(module, name):
    return _json(studio.remove_relationship(module, name))


@studio_bp.post("/api/relationships")
def api_create_relationship():
    data = _payload()
    return _json(
        studio.create_relationship(
            parent=data.get("parent", ""),
            child=data.get("child", ""),
            rel_type=data.get("rel_type", "one-to-many"),
            fk_field=data.get("fk_field") or None,
            lazy=data.get("lazy", "select"),
        )
    )


# --------------------------------------------------------------------------- #
# Data browser
# --------------------------------------------------------------------------- #
@studio_bp.get("/api/tables")
def api_list_tables():
    return jsonify(studio.list_tables())


@studio_bp.get("/api/tables/<table>/columns")
def api_table_columns(table):
    return jsonify(studio.table_columns(table))


@studio_bp.get("/api/tables/<table>/rows")
def api_table_rows(table):
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    return jsonify(studio.fetch_rows(table, page, per_page))


@studio_bp.post("/api/tables/<table>/rows")
def api_insert_row(table):
    return _json(studio.insert_row(table, _payload()), 201)


@studio_bp.patch("/api/tables/<table>/rows")
def api_update_row(table):
    data = _payload()
    pk = data.pop("_pk", None) or {}
    return _json(studio.update_row(table, pk, data))


@studio_bp.delete("/api/tables/<table>/rows")
def api_delete_row(table):
    data = _payload()
    pk = data.pop("_pk", None) or {}
    return _json(studio.delete_row(table, pk))


# --------------------------------------------------------------------------- #
# SQL console
# --------------------------------------------------------------------------- #
@studio_bp.post("/api/sql")
def api_run_sql():
    data = _payload()
    return _json(
        studio.run_sql(
            data.get("sql", ""),
            write=bool(data.get("write")),
        )
    )


# --------------------------------------------------------------------------- #
# Migrations
# --------------------------------------------------------------------------- #
@studio_bp.post("/api/migrations")
def api_run_migration():
    data = _payload()
    return _json(studio.run_migration(data.get("message", "studio migration")))
