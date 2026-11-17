"""Pytest fixtures for the Flask demo app."""

import pytest
from werkzeug.security import generate_password_hash

from app import create_app

TEST_PASSWORD = "test-password-not-for-production"


@pytest.fixture()
def app():
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "ADMIN_PASSWORD_HASH": generate_password_hash(TEST_PASSWORD),
        }
    )
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()
