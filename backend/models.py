"""User and Task models: database queries and serialization."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db

VALID_STATUSES = ("pending", "completed")


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class User:
    id: int
    full_name: str
    email: str
    password_hash: str
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row):
        return cls(**dict(row))

    def to_public_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "created_at": self.created_at,
        }

    @classmethod
    def get_by_id(cls, user_id):
        if not user_id:
            return None
        row = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return cls.from_row(row) if row else None

    @classmethod
    def get_by_email(cls, email):
        normalized = email.strip().lower()
        row = get_db().execute("SELECT * FROM users WHERE email = ?", (normalized,)).fetchone()
        return cls.from_row(row) if row else None

    @classmethod
    def create(cls, full_name, email, password):
        now = utc_now()
        db = get_db()
        cursor = db.execute(
            """INSERT INTO users (full_name, email, password_hash, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                full_name.strip(),
                email.strip().lower(),
                generate_password_hash(password),
                now,
                now,
            ),
        )
        db.commit()
        return cls.get_by_id(cursor.lastrowid)

    @classmethod
    def count(cls):
        return get_db().execute("SELECT COUNT(*) FROM users").fetchone()[0]

    @classmethod
    def authenticate(cls, email, password):
        user = cls.get_by_email(email)
        if user and check_password_hash(user.password_hash, password):
            return user
        return None


@dataclass
class Task:
    id: int
    user_id: int | None
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
        data = asdict(self)
        data.pop("user_id", None)
        return data

    # ------------------------------------------------------------------ queries
    @classmethod
    def list(cls, user_id, status=None, search=None):
        sql = "SELECT * FROM tasks WHERE user_id = ?"
        params = [user_id]

        if status in VALID_STATUSES:
            sql += " AND status = ?"
            params.append(status)

        if search:
            sql += " AND (title LIKE ? OR description LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term])

        sql += " ORDER BY created_at DESC, id DESC"

        rows = get_db().execute(sql, params).fetchall()
        return [cls.from_row(row).to_dict() for row in rows]

    @classmethod
    def get(cls, task_id, user_id):
        row = get_db().execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)
        ).fetchone()
        return cls.from_row(row) if row else None

    @classmethod
    def create(cls, user_id, title, description="", due_date=None, status="pending"):
        now = utc_now()
        db = get_db()
        cursor = db.execute(
            """INSERT INTO tasks
                   (user_id, title, description, due_date, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, title, description, due_date, status, now, now),
        )
        db.commit()
        return cls.get(cursor.lastrowid, user_id)

    def update(self, **fields):
        if not fields:
            return self

        fields["updated_at"] = utc_now()
        columns = ", ".join(f"{column} = ?" for column in fields)
        params = list(fields.values()) + [self.id, self.user_id]

        db = get_db()
        db.execute(
            f"UPDATE tasks SET {columns} WHERE id = ? AND user_id = ?",
            params,
        )
        db.commit()
        return type(self).get(self.id, self.user_id)

    def delete(self):
        db = get_db()
        db.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?", (self.id, self.user_id)
        )
        db.commit()

    @staticmethod
    def stats(user_id):
        row = get_db().execute(
            """SELECT
                   COUNT(*) AS total,
                   COALESCE(SUM(status = 'pending'), 0)   AS pending,
                   COALESCE(SUM(status = 'completed'), 0) AS completed
               FROM tasks
               WHERE user_id = ?""",
            (user_id,),
        ).fetchone()
        return dict(row)

    @staticmethod
    def claim_unowned(user_id):
        """Give pre-authentication tasks to the first registered account."""
        db = get_db()
        cursor = db.execute(
            "UPDATE tasks SET user_id = ? WHERE user_id IS NULL", (user_id,)
        )
        db.commit()
        return cursor.rowcount
