"""
Read-only SSH helper for Linux metric collection.

HARD RULE: This module must NEVER restart services, kill processes, change
configs, reboot hosts, write files, or otherwise modify remote systems.
Only fixed, allowlisted read commands are permitted.
"""

from __future__ import annotations

import os
from typing import Callable

import paramiko

# Exact allowlisted remote commands only (no user-supplied command strings).
ALLOWED_COMMANDS: frozenset[str] = frozenset(
    {
        "grep '^cpu ' /proc/stat",
        "grep -E '^(MemTotal|MemAvailable):' /proc/meminfo",
        "cat /proc/net/dev",
        "ss -lntuH",
    }
)

# Patterns that must never appear in a remote command string.
_DANGEROUS = (
    "rm ",
    "reboot",
    "shutdown",
    "systemctl",
    "kill",
    "mkfs",
    "dd ",
    ">",
    "chmod",
    "chown",
    "passwd",
    "useradd",
    "apt ",
    "yum ",
    "dnf ",
)


class SSHError(Exception):
    """Connection or remote read failure (safe to show to the user)."""


def assert_command_allowed(command: str) -> None:
    """Reject anything not on the allowlist or matching dangerous patterns."""
    if command not in ALLOWED_COMMANDS:
        raise SSHError("Command is not on the read-only allowlist.")
    lowered = command.lower()
    for token in _DANGEROUS:
        if token in lowered and command not in ALLOWED_COMMANDS:
            raise SSHError("Refusing potentially dangerous remote command.")


def _connect(
    host: str,
    username: str,
    port: int,
    timeout: float = 5.0,
) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key_path = os.environ.get("SSH_KEY_PATH", "").strip() or None
    password = os.environ.get("SSH_PASSWORD", "").strip() or None
    connect_kwargs: dict = {
        "hostname": host,
        "username": username,
        "port": port,
        "timeout": timeout,
        "banner_timeout": timeout,
        "auth_timeout": timeout,
        "allow_agent": True,
        "look_for_keys": True,
    }
    if key_path:
        connect_kwargs["key_filename"] = key_path
    if password:
        connect_kwargs["password"] = password
    try:
        client.connect(**connect_kwargs)
    except Exception as exc:  # noqa: BLE001 — surface as graceful SSHError
        client.close()
        raise SSHError(f"SSH unreachable: {exc}") from exc
    return client


def run_readonly(
    host: str,
    username: str,
    port: int,
    command: str,
    *,
    timeout: float = 5.0,
    connect_fn: Callable[..., paramiko.SSHClient] | None = None,
) -> str:
    """
    Run a single allowlisted read-only command over SSH and return stdout.

    Never executes mutate/write/reboot-style operations.
    """
    assert_command_allowed(command)
    connector = connect_fn or _connect
    client = connector(host, username, port, timeout=timeout)
    try:
        _stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        exit_status = stdout.channel.recv_exit_status()
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        if exit_status != 0:
            raise SSHError(err.strip() or f"Remote command failed ({exit_status}).")
        return out
    except SSHError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise SSHError(f"SSH read failed: {exc}") from exc
    finally:
        client.close()
