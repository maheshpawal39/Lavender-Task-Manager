"""SQLite connection handling and schema setup."""

import sqlite3
from pathlib import Path

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL,
    updated_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES users (id) ON DELETE CASCADE,
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

# Columns added after the first release. Existing databases receive them in place,
# so previously saved tasks are never dropped or recreated.
TASK_MIGRATIONS = {
    "user_id": "INTEGER REFERENCES users (id) ON DELETE CASCADE",
}


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


def migrate_db(db):
    """Apply additive schema changes to an existing tasks table."""
    columns = {row["name"] for row in db.execute("PRAGMA table_info(tasks)")}

    for name, definition in TASK_MIGRATIONS.items():
        if name not in columns:
            db.execute(f"ALTER TABLE tasks ADD COLUMN {name} {definition}")

    # Created here because old tasks tables do not have user_id at schema time.
    db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks (user_id)")


def init_db():
    """Create the database and apply pending additive migrations."""
    database_path = Path(current_app.config["DATABASE"])
    database_path.parent.mkdir(parents=True, exist_ok=True)

    db = get_db()
    db.executescript(SCHEMA)
    migrate_db(db)
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
