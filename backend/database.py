"""SQLite connection handling and schema setup."""

import sqlite3
from pathlib import Path

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    due_date    TEXT,
    status      TEXT    NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'completed')),
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks (due_date);
"""


def get_db():
    """Return the request-scoped SQLite connection."""
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the database file and tables if they do not exist."""
    database_path = Path(current_app.config["DATABASE"])
    database_path.parent.mkdir(parents=True, exist_ok=True)

    db = get_db()
    db.executescript(SCHEMA)
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
