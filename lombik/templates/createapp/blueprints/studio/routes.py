from flask import render_template, request

from . import studio_bp
from lombik import studio


@studio_bp.get("/")
def canvas():
    context = {
        "selected": "canvas",
        "models": studio.list_models(),
        "column_types": studio.COLUMN_TYPES,
        "relationship_types": studio.RELATIONSHIP_TYPES,
        "lazy_options": studio.LAZY_OPTIONS,
    }
    return render_template("studio/canvas.html", **context)


@studio_bp.get("/models")
def models():
    context = {
        "selected": "models",
        "models": studio.list_models(),
        "column_types": studio.COLUMN_TYPES,
    }
    return render_template("studio/models.html", **context)


@studio_bp.get("/models/<module>")
def model_detail(module):
    info = studio.parse_model_file(studio.model_path(module))
    if not info:
        return render_template("studio/not_found.html", selected="models", name=module), 404

    context = {
        "selected": "models",
        "model": info,
        "models": studio.list_models(),
        "column_types": studio.COLUMN_TYPES,
        "relationship_types": studio.RELATIONSHIP_TYPES,
        "lazy_options": studio.LAZY_OPTIONS,
        "on_delete_actions": studio.ON_DELETE_ACTIONS,
    }
    return render_template("studio/model_detail.html", **context)


@studio_bp.get("/data")
def data():
    tables = studio.list_tables()
    selected_table = request.args.get("table") or (tables[0] if tables else None)

    context = {
        "selected": "data",
        "tables": tables,
        "selected_table": selected_table,
        "columns": [],
        "rows_data": None,
    }

    if selected_table:
        context["columns"] = studio.table_columns(selected_table)
        context["rows_data"] = studio.fetch_rows(
            selected_table,
            page=request.args.get("page", 1, type=int),
            per_page=request.args.get("per_page", 50, type=int),
        )

    return render_template("studio/data.html", **context)


@studio_bp.get("/sql")
def sql():
    context = {
        "selected": "sql",
        "tables": studio.list_tables(),
    }
    return render_template("studio/sql.html", **context)


@studio_bp.get("/migrations")
def migrations():
    context = {
        "selected": "migrations",
    }
    return render_template("studio/migrations.html", **context)
