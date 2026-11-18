"""Task model: database queries and serialization."""

from datetime import datetime, timezone
from dataclasses import dataclass, asdict

from database import get_db

VALID_STATUSES = ("pending", "completed")


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class Task:
    id: int
    title: str
    description: str
    due_date: str | None
    status: str
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row):
        return cls(**dict(row))

    def to_dict(self):
        return asdict(self)

    # ------------------------------------------------------------------ queries
    @classmethod
    def list(cls, status=None, search=None):
        sql = "SELECT * FROM tasks"
        clauses, params = [], []

        if status in VALID_STATUSES:
            clauses.append("status = ?")
            params.append(status)

        if search:
            clauses.append("(title LIKE ? OR description LIKE ?)")
            term = f"%{search}%"
            params.extend([term, term])

        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        sql += " ORDER BY created_at DESC, id DESC"

        rows = get_db().execute(sql, params).fetchall()
        return [cls.from_row(row).to_dict() for row in rows]

    @classmethod
    def get(cls, task_id):
        row = get_db().execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return cls.from_row(row) if row else None

    @classmethod
    def create(cls, title, description="", due_date=None, status="pending"):
        now = utc_now()
        db = get_db()
        cursor = db.execute(
            """INSERT INTO tasks (title, description, due_date, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, description, due_date, status, now, now),
        )
        db.commit()
        return cls.get(cursor.lastrowid)

    def update(self, **fields):
        if not fields:
            return self

        fields["updated_at"] = utc_now()
        columns = ", ".join(f"{column} = ?" for column in fields)
        params = list(fields.values()) + [self.id]

        db = get_db()
        db.execute(f"UPDATE tasks SET {columns} WHERE id = ?", params)
        db.commit()
        return type(self).get(self.id)

    def delete(self):
        db = get_db()
        db.execute("DELETE FROM tasks WHERE id = ?", (self.id,))
        db.commit()

    @staticmethod
    def stats():
        row = get_db().execute(
            """SELECT
                   COUNT(*) AS total,
                   COALESCE(SUM(status = 'pending'), 0)   AS pending,
                   COALESCE(SUM(status = 'completed'), 0) AS completed
               FROM tasks"""
        ).fetchone()
        return dict(row)
