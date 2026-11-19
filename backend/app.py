"""Mini Task Manager - Flask application entry point (PostgreSQL)."""

import os
import secrets
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.middleware.proxy_fix import ProxyFix

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
INSTANCE_DIR = BASE_DIR / "instance"

load_dotenv(BASE_DIR / ".env")

from database import db, init_app as init_database, normalize_database_url  # noqa: E402
from models import Task, User  # noqa: E402,F401  (registers metadata for Alembic)
from routes.auth import auth_bp  # noqa: E402
from routes.tasks import tasks_bp  # noqa: E402

migrate = Migrate()


def env_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def load_secret_key():
    """Require SECRET_KEY in production; allow a local file for development."""
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key

    if os.environ.get("VERCEL"):
        raise RuntimeError(
            "SECRET_KEY is required on Vercel. Add it to the project environment variables."
        )

    key_file = INSTANCE_DIR / "secret_key"
    if key_file.exists():
        return key_file.read_text(encoding="utf-8").strip()

    key = secrets.token_hex(32)
    key_file.write_text(key, encoding="utf-8")
    return key


def cors_origins():
    configured = os.environ.get("FRONTEND_URL") or os.environ.get("CORS_ORIGINS")
    if configured:
        return [origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()]
    return ["http://localhost:5173", "http://127.0.0.1:5173"]


def create_app(test_config=None):
    is_vercel = bool(os.environ.get("VERCEL"))
    if not is_vercel:
        INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

    secure_cookies = True if is_vercel else env_flag("SESSION_COOKIE_SECURE")
    same_site_raw = os.environ.get("SESSION_COOKIE_SAMESITE") or (
        "None" if secure_cookies else "Lax"
    )
    same_site = {
        "none": "None",
        "lax": "Lax",
        "strict": "Strict",
    }.get(same_site_raw.lower(), same_site_raw)
    if same_site == "None":
        secure_cookies = True

    if is_vercel and not (
        os.environ.get("FRONTEND_URL") or os.environ.get("CORS_ORIGINS")
    ):
        raise RuntimeError(
            "FRONTEND_URL is required on Vercel. Set it to your deployed frontend origin."
        )

    app = Flask(
        __name__,
        instance_path=str(INSTANCE_DIR),
        instance_relative_config=True,
    )
    app.config.from_mapping(
        SECRET_KEY=load_secret_key(),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE=same_site,
        SESSION_COOKIE_SECURE=secure_cookies,
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
        JSON_SORT_KEYS=False,
        MAX_CONTENT_LENGTH=64 * 1024,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    database_url = app.config.get("SQLALCHEMY_DATABASE_URI") or os.environ.get(
        "DATABASE_URL"
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = normalize_database_url(database_url)

    init_database(app)
    migrate.init_app(app, db)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": cors_origins(),
                "supports_credentials": True,
            }
        },
    )

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)

    @app.get("/api/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            app.logger.exception("Database health check failed")
            db.session.rollback()
            return jsonify({"status": "error", "database": "unavailable"}), 503
        return jsonify({"status": "ok", "database": "ok"})

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error):
        app.logger.exception("Database error: %s", error)
        db.session.rollback()
        return jsonify({"error": "Database service is unavailable. Please try again."}), 503

    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found."}), 404
        return serve_frontend("")

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(413)
    def payload_too_large(_error):
        return jsonify({"error": "Request body is too large."}), 413

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error("Unhandled error: %s", error)
        return jsonify({"error": "Something went wrong on the server."}), 500

    # Serve the production frontend locally when a build exists.
    @app.get("/")
    @app.get("/<path:path>")
    def serve_frontend(path=""):
        if not (FRONTEND_DIST / "index.html").exists():
            return jsonify({
                "message": "Task Manager API is running.",
                "database": "postgresql",
                "api": "/api/tasks",
            })

        requested = FRONTEND_DIST / path
        if path and requested.is_file():
            return send_from_directory(FRONTEND_DIST, path)
        return send_from_directory(FRONTEND_DIST, "index.html")

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    app.run(host="127.0.0.1", port=port, debug=True)
