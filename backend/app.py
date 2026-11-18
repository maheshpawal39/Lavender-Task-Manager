"""Mini Task Manager - Flask application entry point."""

import os
import secrets
from datetime import timedelta
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from database import init_app as init_database
from routes.auth import auth_bp
from routes.tasks import tasks_bp

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
INSTANCE_DIR = BASE_DIR / "instance"


def load_secret_key(instance_path):
    """Use SECRET_KEY from the environment or a stable local key file."""
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key

    key_file = Path(instance_path) / "secret_key"
    if key_file.exists():
        return key_file.read_text(encoding="utf-8").strip()

    key = secrets.token_hex(32)
    key_file.write_text(key, encoding="utf-8")
    return key


def create_app(test_config=None):
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

    app = Flask(
        __name__,
        instance_path=str(INSTANCE_DIR),
        instance_relative_config=True,
    )
    app.config.from_mapping(
        DATABASE=os.environ.get(
            "TASKMATE_DATABASE", str(INSTANCE_DIR / "tasks.db")
        ),
        SECRET_KEY=load_secret_key(INSTANCE_DIR),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "").lower()
        in ("1", "true", "yes"),
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
        JSON_SORT_KEYS=False,
        MAX_CONTENT_LENGTH=64 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    cors_origins = [
        origin.strip()
        for origin in os.environ.get(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ]
    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins, "supports_credentials": True}},
    )
    init_database(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

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

    # Serve the production build when it exists; Vite handles this during dev.
    @app.get("/")
    @app.get("/<path:path>")
    def serve_frontend(path=""):
        if not (FRONTEND_DIST / "index.html").exists():
            return jsonify(
                {
                    "message": "Task Manager API is running.",
                    "hint": "Run the React dev server (npm run dev) or build the frontend.",
                    "api": "/api/tasks",
                }
            )
        requested = FRONTEND_DIST / path
        if path and requested.is_file():
            return send_from_directory(FRONTEND_DIST, path)
        return send_from_directory(FRONTEND_DIST, "index.html")

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    app.run(host="127.0.0.1", port=port, debug=True)
