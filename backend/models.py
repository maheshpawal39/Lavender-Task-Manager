"""SQLAlchemy models for users and tasks."""

from datetime import date, datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from database import db

VALID_STATUSES = ("pending", "completed")


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0)


def to_iso(value):
    """Serialize a datetime in the same format the existing API returns."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def to_date(value):
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def commit():
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (
        db.UniqueConstraint("email", name="uq_users_email"),
    )

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(254), nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    tasks = db.relationship(
        "Task",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def to_public_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "created_at": to_iso(self.created_at),
        }

    @classmethod
    def get_by_id(cls, user_id):
        if not user_id:
            return None
        return db.session.get(cls, user_id)

    @classmethod
    def get_by_email(cls, email):
        normalized = email.strip().lower()
        return db.session.scalar(db.select(cls).where(cls.email == normalized))

    @classmethod
    def create(cls, full_name, email, password):
        user = cls(
            full_name=full_name.strip(),
            email=email.strip().lower(),
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        commit()
        return user

    @classmethod
    def count(cls):
        return db.session.scalar(db.select(db.func.count()).select_from(cls)) or 0

    @classmethod
    def authenticate(cls, email, password):
        user = cls.get_by_email(email)
        if user and check_password_hash(user.password_hash, password):
            return user
        return None


class Task(db.Model):
    __tablename__ = "tasks"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('pending', 'completed')",
            name="ck_tasks_status_valid",
        ),
        db.Index("ix_tasks_user_id", "user_id"),
        db.Index("ix_tasks_status", "status"),
        db.Index("ix_tasks_due_date", "due_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, server_default="")
    due_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, server_default="pending")
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    owner = db.relationship("User", back_populates="tasks")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status,
            "created_at": to_iso(self.created_at),
            "updated_at": to_iso(self.updated_at),
        }

    # ------------------------------------------------------------------ queries
    @classmethod
    def list(cls, user_id, status=None, search=None):
        stmt = db.select(cls).where(cls.user_id == user_id)

        if status in VALID_STATUSES:
            stmt = stmt.where(cls.status == status)

        if search:
            term = f"%{search}%"
            stmt = stmt.where(
                db.or_(cls.title.ilike(term), cls.description.ilike(term))
            )

        stmt = stmt.order_by(cls.created_at.desc(), cls.id.desc())
        return [task.to_dict() for task in db.session.scalars(stmt).all()]

    @classmethod
    def get(cls, task_id, user_id):
        return db.session.scalar(
            db.select(cls).where(cls.id == task_id, cls.user_id == user_id)
        )

    @classmethod
    def create(cls, user_id, title, description="", due_date=None, status="pending"):
        task = cls(
            user_id=user_id,
            title=title,
            description=description,
            due_date=to_date(due_date),
            status=status,
        )
        db.session.add(task)
        commit()
        return task

    def update(self, **fields):
        if not fields:
            return self

        if "due_date" in fields:
            fields["due_date"] = to_date(fields["due_date"])
        fields["updated_at"] = utc_now()

        for key, value in fields.items():
            setattr(self, key, value)

        commit()
        db.session.refresh(self)
        return self

    def delete(self):
        db.session.delete(self)
        commit()

    @staticmethod
    def stats(user_id):
        pending_count = db.func.coalesce(
            db.func.sum(
                db.case((Task.status == "pending", 1), else_=0)
            ),
            0,
        )
        completed_count = db.func.coalesce(
            db.func.sum(
                db.case((Task.status == "completed", 1), else_=0)
            ),
            0,
        )
        row = db.session.execute(
            db.select(
                db.func.count(Task.id),
                pending_count,
                completed_count,
            ).where(Task.user_id == user_id)
        ).one()
        return {
            "total": int(row[0]),
            "pending": int(row[1]),
            "completed": int(row[2]),
        }

    @staticmethod
    def claim_unowned(user_id):
        """Give pre-authentication tasks to the first registered account."""
        result = db.session.execute(
            db.update(Task)
            .where(Task.user_id.is_(None))
            .values(user_id=user_id)
        )
        commit()
        return result.rowcount or 0
