"""Task API blueprint."""

import re
from datetime import date

from flask import Blueprint, g, jsonify, request

from models import VALID_STATUSES, Task
from routes.auth import login_required

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api")

TITLE_MAX = 120
DESCRIPTION_MAX = 500


class ApiError(Exception):
    def __init__(self, message, status=400, fields=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.fields = fields or {}


def validate_payload(data, partial=False):
    """Validate and normalize a JSON task payload."""
    if not isinstance(data, dict):
        raise ApiError("Request body must be a JSON object.")

    fields = {}
    errors = {}

    if not partial or "title" in data:
        raw_title = data.get("title")
        if not isinstance(raw_title, str) or not raw_title.strip():
            errors["title"] = "Title is required."
        elif len(raw_title.strip()) > TITLE_MAX:
            errors["title"] = f"Title must be {TITLE_MAX} characters or fewer."
        else:
            fields["title"] = raw_title.strip()

    if not partial or "description" in data:
        raw_description = data.get("description", "")
        if raw_description is None:
            raw_description = ""
        if not isinstance(raw_description, str):
            errors["description"] = "Description must be text."
        elif len(raw_description.strip()) > DESCRIPTION_MAX:
            errors["description"] = f"Description must be {DESCRIPTION_MAX} characters or fewer."
        else:
            fields["description"] = raw_description.strip()

    if not partial or "due_date" in data:
        raw_due_date = data.get("due_date")
        if raw_due_date in (None, ""):
            fields["due_date"] = None
        elif not isinstance(raw_due_date, str):
            errors["due_date"] = "Due date must be in YYYY-MM-DD format."
        elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_due_date):
            errors["due_date"] = "Due date must be a valid date in YYYY-MM-DD format."
        else:
            try:
                parsed = date.fromisoformat(raw_due_date)
            except ValueError:
                errors["due_date"] = "Due date must be a valid date in YYYY-MM-DD format."
            else:
                if not 1900 <= parsed.year <= 2100:
                    errors["due_date"] = "Due date must be between 1900 and 2100."
                else:
                    fields["due_date"] = parsed.isoformat()

    if not partial or "status" in data:
        raw_status = data.get("status", "pending")
        if raw_status not in VALID_STATUSES:
            errors["status"] = "Status must be 'pending' or 'completed'."
        else:
            fields["status"] = raw_status

    if errors:
        raise ApiError("Please check the highlighted fields.", 422, errors)
    if partial and not fields:
        raise ApiError("No valid fields were provided to update.")

    return fields


def get_task_or_404(task_id):
    task = Task.get(task_id, g.user.id)
    if task is None:
        raise ApiError("Task not found.", 404)
    return task


@tasks_bp.errorhandler(ApiError)
def handle_api_error(error):
    payload = {"error": error.message}
    if error.fields:
        payload["fields"] = error.fields
    return jsonify(payload), error.status


@tasks_bp.get("/tasks")
@login_required
def list_tasks():
    status = request.args.get("status", "all").lower()
    search = request.args.get("search", "").strip()

    if status not in ("all", *VALID_STATUSES):
        raise ApiError("Status filter must be 'all', 'pending' or 'completed'.")

    tasks = Task.list(
        user_id=g.user.id,
        status=None if status == "all" else status,
        search=search or None,
    )
    return jsonify({"tasks": tasks, "count": len(tasks)})


@tasks_bp.get("/tasks/<int:task_id>")
@login_required
def get_task(task_id):
    return jsonify({"task": get_task_or_404(task_id).to_dict()})


@tasks_bp.post("/tasks")
@login_required
def create_task():
    payload = validate_payload(request.get_json(silent=True))
    task = Task.create(user_id=g.user.id, **payload)
    return jsonify({"task": task.to_dict()}), 201


@tasks_bp.route("/tasks/<int:task_id>", methods=["PUT", "PATCH"])
@login_required
def update_task(task_id):
    task = get_task_or_404(task_id)
    payload = validate_payload(request.get_json(silent=True), partial=request.method == "PATCH")
    updated = task.update(**payload)
    return jsonify({"task": updated.to_dict()})


@tasks_bp.delete("/tasks/<int:task_id>")
@login_required
def delete_task(task_id):
    task = get_task_or_404(task_id)
    task.delete()
    return "", 204


@tasks_bp.get("/stats")
@login_required
def get_stats():
    return jsonify(Task.stats(g.user.id))
