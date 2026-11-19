"""Vercel serverless entrypoint for the Flask API."""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

from app import app  # noqa: E402,F401
