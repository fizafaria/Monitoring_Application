"""Single-admin authentication helpers (hashed password only)."""

from __future__ import annotations

import functools
import os
from typing import Callable, TypeVar

from flask import current_app, redirect, request, session, url_for
from werkzeug.security import check_password_hash

F = TypeVar("F", bound=Callable)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")


def get_admin_password_hash() -> str:
    """Return the configured password hash (never a plain-text password)."""
    return current_app.config["ADMIN_PASSWORD_HASH"]


def verify_admin_credentials(username: str, password: str) -> bool:
    if username != ADMIN_USERNAME:
        return False
    return check_password_hash(get_admin_password_hash(), password)


def login_user() -> None:
    session.clear()
    session["authenticated"] = True
    session["username"] = ADMIN_USERNAME


def logout_user() -> None:
    session.clear()


def is_authenticated() -> bool:
    return bool(session.get("authenticated"))


def login_required(view: F) -> F:
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for("main.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped  # type: ignore[return-value]


def load_admin_password_hash_from_env() -> str:
    """
    Resolve ADMIN_PASSWORD_HASH from the environment.

    A built-in demo hash is used only when unset so `python run.py` works locally.
    Generate your own: see README (never commit production passwords).
    """
    configured = os.environ.get("ADMIN_PASSWORD_HASH", "").strip()
    if configured:
        return configured
    # Hash of the local-demo password documented in README (not for production).
    return (
        "scrypt:32768:8:1$GHzlmxOuweNtBk9G$"
        "d02f3422fb006a23d0a975511e7555c9bdd6700a73b1ed5138d7e832ccc4fb61"
        "97f81ddf6478c1f550ced7b1e8ca5adb535dd02fd2957e8dc88fc5b94dce3e51"
    )
