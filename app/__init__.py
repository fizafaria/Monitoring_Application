"""Demo Linux Infrastructure Monitoring — Flask application factory."""

import os

from flask import Flask

from app.auth import load_admin_password_hash_from_env
from app.inventory import ServerInventory


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.config.update(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me"),
        ADMIN_PASSWORD_HASH=load_admin_password_hash_from_env(),
        # Session cookies — appropriate for local HTTP demo
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
    )

    if test_config:
        app.config.update(test_config)

    # In-memory inventory (demo): lost on process restart.
    app.extensions["inventory"] = ServerInventory()

    from app.routes import bp

    app.register_blueprint(bp)
    return app
