"""One-time migration of legacy SQLite data into PostgreSQL.

Usage (after `flask db upgrade`):

    python backend/scripts/migrate_sqlite_to_postgres.py
    python backend/scripts/migrate_sqlite_to_postgres.py --source path/to/tasks.db

The source SQLite database is opened read-only and is never modified. The script
is idempotent: existing users (by id or email) and tasks (by id) are skipped.
"""

import argparse
import sqlite3
import sys
from datetime import date, datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import text  # noqa: E402

from app import create_app  # noqa: E402
from database import db  # noqa: E402
from models import VALID_STATUSES, Task, User  # noqa: E402

DEFAULT_SOURCE = BASE_DIR / "instance" / "tasks.db"


def parse_datetime(value):
    if not value:
        return datetime.now(timezone.utc).replace(microsecond=0)
    if isinstance(value, datetime):
        return value
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def parse_date(value):
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def read_sqlite(source):
    connection = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }

    if "users" not in tables or "tasks" not in tables:
        connection.close()
        raise RuntimeError(
            f"{source} does not contain the expected users/tasks tables."
        )

    users = [dict(row) for row in connection.execute("SELECT * FROM users ORDER BY id")]
    task_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(tasks)")
    }
    tasks = [
        dict(row) for row in connection.execute("SELECT * FROM tasks ORDER BY id")
    ]
    connection.close()
    return users, tasks, task_columns


def sync_sequence(table):
    max_id = db.session.execute(
        text(f"SELECT COALESCE(MAX(id), 0) FROM {table}")
    ).scalar_one()
    db.session.execute(
        text("SELECT setval(pg_get_serial_sequence(:table, 'id'), :value, :called)"),
        {"table": table, "value": max(max_id, 1), "called": max_id > 0},
    )


def migrate(source):
    users, tasks, task_columns = read_sqlite(source)

    app = create_app()
    with app.app_context():
        existing_tables = set(db.inspect(db.engine).get_table_names())
        if not {"users", "tasks"}.issubset(existing_tables):
            raise RuntimeError(
                "PostgreSQL schema is missing. Run `flask db upgrade` first."
            )

        user_map = {}
        users_added = users_skipped = 0

        for row in users:
            source_id = int(row["id"])
            existing = db.session.get(User, source_id)
            if existing:
                user_map[source_id] = existing.id
                users_skipped += 1
                continue

            by_email = User.get_by_email(row["email"])
            if by_email:
                user_map[source_id] = by_email.id
                users_skipped += 1
                continue

            user = User(
                id=source_id,
                full_name=row["full_name"],
                email=str(row["email"]).strip().lower(),
                password_hash=row["password_hash"],
                created_at=parse_datetime(row.get("created_at")),
                updated_at=parse_datetime(row.get("updated_at")),
            )
            db.session.add(user)
            user_map[source_id] = source_id
            users_added += 1

        db.session.commit()

        tasks_added = tasks_skipped = 0
        for row in tasks:
            source_id = int(row["id"])
            if db.session.get(Task, source_id):
                tasks_skipped += 1
                continue

            status = row.get("status") or "pending"
            if status not in VALID_STATUSES:
                raise RuntimeError(
                    f"Task {source_id} has invalid status {status!r}; aborting."
                )

            source_user_id = row.get("user_id") if "user_id" in task_columns else None
            task = Task(
                id=source_id,
                user_id=user_map.get(source_user_id) if source_user_id else None,
                title=row["title"],
                description=row.get("description") or "",
                due_date=parse_date(row.get("due_date")),
                status=status,
                created_at=parse_datetime(row.get("created_at")),
                updated_at=parse_datetime(row.get("updated_at")),
            )
            db.session.add(task)
            tasks_added += 1

        db.session.commit()

        sync_sequence("users")
        sync_sequence("tasks")
        db.session.commit()

        print("SQLite -> PostgreSQL migration complete")
        print(f"  users: {users_added} added, {users_skipped} skipped")
        print(f"  tasks: {tasks_added} added, {tasks_skipped} skipped")
        print(f"  source: {source} (unchanged)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Legacy SQLite database (default: {DEFAULT_SOURCE})",
    )
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"SQLite source not found: {args.source}")

    migrate(args.source.resolve())


if __name__ == "__main__":
    main()
