"""PostgreSQL connection setup with SQLAlchemy and connection pooling."""

import os

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

POSTGRES_SCHEMES = ("postgresql://", "postgresql+psycopg://", "postgres://")


def normalize_database_url(url):
    """Validate DATABASE_URL and select the psycopg 3 driver."""
    if not url or not url.strip():
        raise RuntimeError(
            "DATABASE_URL is required. Set it to a PostgreSQL connection string, "
            "for example: postgresql://user:password@host:5432/database"
        )

    url = url.strip()
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    if url.startswith("postgresql+psycopg://"):
        return url

    raise RuntimeError(
        "Only PostgreSQL databases are supported. "
        "DATABASE_URL must start with postgresql:// or postgres://. "
        "SQLite is not a supported production fallback."
    )


def engine_options():
    """Pooling settings suitable for serverless PostgreSQL deployments."""
    connect_args = {
        "connect_timeout": int(os.environ.get("DB_CONNECT_TIMEOUT", "5")),
    }
    if os.environ.get("DB_DISABLE_PREPARED_STATEMENTS", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        # Needed for transaction-mode poolers such as PgBouncer.
        connect_args["prepare_threshold"] = None

    return {
        "pool_pre_ping": True,
        "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE", "280")),
        "pool_size": int(os.environ.get("DB_POOL_SIZE", "2")),
        "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", "3")),
        "pool_timeout": int(os.environ.get("DB_POOL_TIMEOUT", "10")),
        "connect_args": connect_args,
    }


def init_app(app):
    """Attach SQLAlchemy to the Flask app; schema changes run through Alembic."""
    if not app.config.get("SQLALCHEMY_ENGINE_OPTIONS"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options()
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    db.init_app(app)
