from flask import current_app, render_template, request

from . import studio_bp
from lombik import studio


def _network_graph(models):
    """Build nodes/edges for the interactive vis-network relationship graph."""
    nodes = {}
    edge_map = {}

    for model in models:
        nodes[model["class_name"]] = {
            "id": model["class_name"],
            "label": model["class_name"],
            "title": model["table_name"],
            "module": model["module"],
        }

        for rel in model["relationships"]:
            target = rel.get("target")
            if not target:
                continue

            source = model["class_name"]
            key = tuple(sorted((source, target)))
            edge_map.setdefault(key, []).append({
                "name": rel["name"],
                "cardinality": "many" if rel["uselist"] else "one",
                "module": model["module"],
                "source": source,
                "target": target,
            })

    edges = []
    for key in sorted(edge_map):
        items = sorted(edge_map[key], key=lambda r: r["name"])
        label = " / ".join(f"{r['name']} ({r['cardinality']})" for r in items)
        edges.append({
            "id": f"{key[0]}__{key[1]}",
            "from": key[0],
            "to": key[1],
            "label": label,
            "relations": sorted(edge_map[key], key=lambda r: r["name"]),
        })

    return list(nodes.values()), edges


@studio_bp.get("/")
def canvas():
    models = studio.list_models()
    graph_nodes, graph_edges = _network_graph(models)
    context = {
        "selected": "canvas",
        "models": models,
        "column_types": studio.COLUMN_TYPES,
        "relationship_types": studio.RELATIONSHIP_TYPES,
        "lazy_options": studio.LAZY_OPTIONS,
        "graph_nodes": graph_nodes,
        "graph_edges": graph_edges,
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


@studio_bp.get("/routes")
def routes():
    rules = []

    for rule in current_app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue

        methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
        rules.append({
            "endpoint": rule.endpoint,
            "methods": methods,
            "rule": rule.rule,
            "linkable": "GET" in methods and "<" not in rule.rule,
        })

    rules.sort(key=lambda r: (r["endpoint"], r["rule"]))

    context = {
        "selected": "routes",
        "rules": rules,
    }
    return render_template("studio/routes.html", **context)
