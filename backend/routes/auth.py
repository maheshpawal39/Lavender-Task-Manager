"""Authentication API: register, login, logout and session lookup."""

import re
import sqlite3
from functools import wraps

from flask import Blueprint, g, jsonify, request, session

from models import Task, User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
FULL_NAME_MIN = 2
FULL_NAME_MAX = 80
EMAIL_MAX = 254
PASSWORD_MIN = 8
PASSWORD_MAX = 128


def api_error(message, status=400, fields=None):
    payload = {"error": message}
    if fields:
        payload["fields"] = fields
    return jsonify(payload), status


def login_required(view):
    """Reject requests without a valid session and expose the user via `g.user`."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = User.get_by_id(session.get("user_id"))
        if user is None:
            session.clear()
            return api_error("Authentication required.", 401)
        g.user = user
        return view(*args, **kwargs)

    return wrapped


def validate_registration(data):
    fields = {}
    errors = {}

    full_name = data.get("full_name")
    if not isinstance(full_name, str) or len(full_name.strip()) < FULL_NAME_MIN:
        errors["full_name"] = "Please enter your full name."
    elif len(full_name.strip()) > FULL_NAME_MAX:
        errors["full_name"] = f"Name must be {FULL_NAME_MAX} characters or fewer."
    else:
        fields["full_name"] = full_name.strip()

    email = data.get("email")
    if not isinstance(email, str) or not email.strip():
        errors["email"] = "Email address is required."
    elif len(email.strip()) > EMAIL_MAX or not EMAIL_RE.match(email.strip()):
        errors["email"] = "Please enter a valid email address."
    else:
        fields["email"] = email.strip().lower()

    password = data.get("password")
    if not isinstance(password, str) or len(password) < PASSWORD_MIN:
        errors["password"] = f"Password must be at least {PASSWORD_MIN} characters."
    elif len(password) > PASSWORD_MAX:
        errors["password"] = f"Password must be {PASSWORD_MAX} characters or fewer."
    else:
        fields["password"] = password

    return fields, errors


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return api_error("Request body must be a JSON object.")

    fields, errors = validate_registration(data)
    if errors:
        return api_error("Please check the highlighted fields.", 422, errors)

    if User.get_by_email(fields["email"]):
        return api_error(
            "An account with this email already exists.",
            409,
            {"email": "This email is already registered."},
        )

    first_account = User.count() == 0

    try:
        user = User.create(
            full_name=fields["full_name"],
            email=fields["email"],
            password=fields["password"],
        )
    except sqlite3.IntegrityError:
        return api_error(
            "An account with this email already exists.",
            409,
            {"email": "This email is already registered."},
        )

    # Tasks created before authentication existed have no owner yet.
    # The first account inherits them so no saved work is lost.
    if first_account:
        Task.claim_unowned(user.id)

    session.clear()
    session["user_id"] = user.id
    session.permanent = False
    return jsonify({"user": user.to_public_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return api_error("Request body must be a JSON object.")

    email = data.get("email")
    password = data.get("password")
    remember = bool(data.get("remember_me", False))

    if not isinstance(email, str) or not email.strip():
        return api_error("Email address is required.", 422, {"email": "Email address is required."})
    if not isinstance(password, str) or not password:
        return api_error("Password is required.", 422, {"password": "Password is required."})

    user = User.authenticate(email, password)
    if user is None:
        return api_error("Incorrect email or password.", 401)

    session.clear()
    session["user_id"] = user.id
    session.permanent = remember
    return jsonify({"user": user.to_public_dict()})


@auth_bp.post("/logout")
def logout():
    session.clear()
    return "", 204


@auth_bp.get("/me")
@login_required
def me():
    return jsonify({"user": g.user.to_public_dict()})
