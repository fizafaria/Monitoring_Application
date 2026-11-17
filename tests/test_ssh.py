"""Unit tests for read-only SSH helper (mocked — no real network)."""

from unittest.mock import MagicMock, patch

import pytest

from app.ssh_client import ALLOWED_COMMANDS, SSHError, assert_command_allowed, run_readonly


def test_allowlist_accepts_known_commands():
    for cmd in ALLOWED_COMMANDS:
        assert_command_allowed(cmd)


def test_allowlist_rejects_unknown_and_dangerous():
    with pytest.raises(SSHError):
        assert_command_allowed("reboot")
    with pytest.raises(SSHError):
        assert_command_allowed("cat /etc/shadow")
    with pytest.raises(SSHError):
        assert_command_allowed("rm -rf /")


def test_run_readonly_success():
    mock_client = MagicMock()
    stdout = MagicMock()
    stdout.channel.recv_exit_status.return_value = 0
    stdout.read.return_value = b"cpu  1 2 3 4 5\n"
    stderr = MagicMock()
    stderr.read.return_value = b""
    mock_client.exec_command.return_value = (MagicMock(), stdout, stderr)

    def fake_connect(*_a, **_k):
        return mock_client

    out = run_readonly(
        "10.0.0.1",
        "monitor",
        22,
        "grep '^cpu ' /proc/stat",
        connect_fn=fake_connect,
    )
    assert "cpu" in out
    mock_client.close.assert_called()


def test_run_readonly_unreachable():
    def boom(*_a, **_k):
        raise SSHError("SSH unreachable: timed out")

    with pytest.raises(SSHError, match="unreachable"):
        run_readonly(
            "10.0.0.1",
            "monitor",
            22,
            "grep '^cpu ' /proc/stat",
            connect_fn=boom,
        )


def test_run_readonly_rejects_non_allowlisted_before_connect():
    with patch("app.ssh_client._connect") as connect:
        with pytest.raises(SSHError, match="allowlist"):
            run_readonly("h", "u", 22, "reboot now")
        connect.assert_not_called()
