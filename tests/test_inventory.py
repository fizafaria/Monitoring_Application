"""Unit tests for in-memory server inventory add/remove/validation."""

from tests.conftest import TEST_PASSWORD


def _login(client):
    return client.post(
        "/login",
        data={"username": "admin", "password": TEST_PASSWORD},
        follow_redirects=True,
    )


def test_add_server(client):
    _login(client)
    response = client.post(
        "/servers",
        data={
            "name": "web-01",
            "host": "10.0.0.10",
            "ssh_user": "monitor",
            "ssh_port": "22",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"web-01" in response.data
    assert b"10.0.0.10" in response.data
    assert b"Server added to inventory" in response.data


def test_reject_invalid_input(client):
    _login(client)
    response = client.post(
        "/servers",
        data={
            "name": "bad;rm",
            "host": "10.0.0.10",
            "ssh_user": "monitor",
            "ssh_port": "22",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"invalid characters" in response.data
    assert b"bad;rm" not in response.data

    response = client.post(
        "/servers",
        data={
            "name": "web-02",
            "host": "10.0.0.11",
            "ssh_user": "monitor",
            "ssh_port": "99999",
        },
        follow_redirects=True,
    )
    assert b"SSH port must be between" in response.data


def test_remove_server(client, app):
    _login(client)
    client.post(
        "/servers",
        data={
            "name": "db-01",
            "host": "10.0.0.20",
            "ssh_user": "ubuntu",
            "ssh_port": "22",
        },
    )
    servers = app.extensions["inventory"].list_servers()
    assert len(servers) == 1
    server_id = servers[0].id

    response = client.post(
        f"/servers/{server_id}/delete",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"db-01" not in response.data
    assert b"remote host unchanged" in response.data
    assert app.extensions["inventory"].list_servers() == []


def test_add_server_requires_login(client):
    response = client.post(
        "/servers",
        data={
            "name": "web-01",
            "host": "10.0.0.10",
            "ssh_user": "monitor",
            "ssh_port": "22",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
