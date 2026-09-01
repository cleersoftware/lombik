"""
Database trigger management.

Lombik keeps referential behaviour at the database level so it works
end-to-end (ORM or raw SQL). Triggers are created idempotently, so they are
safe to run after every migration.

Triggers managed here:

  * `updated_at` auto-timestamp  -> every table with an `updated_at` column

Run manually with:  flask triggers create | drop
"""
from sqlalchemy import text

from db import db


def _dialect() -> str:
    return db.engine.dialect.name


def _pk_of(table) -> str:
    columns = list(table.primary_key.columns)
    return columns[0].name if columns else "id"


def _tables_with(column: str):
    return [t for t in db.metadata.sorted_tables if column in t.columns]


def _updated_at_specs():
    return [t.name for t in _tables_with("updated_at")]


def _build_create_statements(dialect: str) -> list[str]:
    statements = []

    if dialect == "postgresql" and _updated_at_specs():
        statements.append(
            "CREATE OR REPLACE FUNCTION lombik_set_updated_at() RETURNS TRIGGER AS $$ "
            "BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$ LANGUAGE plpgsql;"
        )

    for table in _updated_at_specs():
        pk = _pk_of(db.metadata.tables[table])
        if dialect == "sqlite":
            statements.append(
                f"CREATE TRIGGER IF NOT EXISTS trg_{table}_set_updated_at "
                f"AFTER UPDATE ON {table} FOR EACH ROW "
                f"WHEN OLD.updated_at IS NEW.updated_at "
                f"BEGIN UPDATE {table} SET updated_at = CURRENT_TIMESTAMP "
                f"WHERE {pk} = OLD.{pk}; END;"
            )
        elif dialect == "postgresql":
            statements.append(
                f"CREATE TRIGGER trg_{table}_set_updated_at BEFORE UPDATE ON {table} "
                "FOR EACH ROW EXECUTE FUNCTION lombik_set_updated_at();"
            )
        elif dialect == "mysql":
            statements.append(
                f"CREATE TRIGGER trg_{table}_set_updated_at BEFORE UPDATE ON {table} "
                "FOR EACH ROW SET NEW.updated_at = NOW();"
            )

    return statements


def _build_drop_statements(dialect: str) -> list[str]:
    statements = []
    pg_functions = set()

    for table in _updated_at_specs():
        if dialect == "sqlite":
            statements.append(f"DROP TRIGGER IF EXISTS trg_{table}_set_updated_at;")
        elif dialect == "postgresql":
            statements.append(f"DROP TRIGGER IF EXISTS trg_{table}_set_updated_at ON {table};")
            pg_functions.add("lombik_set_updated_at")
        elif dialect == "mysql":
            statements.append(f"DROP TRIGGER IF EXISTS trg_{table}_set_updated_at;")

    if dialect == "postgresql":
        statements.extend(f"DROP FUNCTION IF EXISTS {fn}();" for fn in sorted(pg_functions))

    return statements


def create_all_triggers():
    dialect = _dialect()
    statements = _build_create_statements(dialect)
    if not statements:
        return

    with db.engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def drop_all_triggers():
    dialect = _dialect()
    statements = _build_drop_statements(dialect)
    if not statements:
        return

    with db.engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))
