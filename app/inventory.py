"""In-memory Linux server inventory (demo — resets on process restart)."""

from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass
from typing import Any

# Reject shell metacharacters / control content in host-related fields.
_UNSAFE = re.compile(r"[;\|&`$<>\n\r\0]")
_HOST_OK = re.compile(r"^[A-Za-z0-9._:-]+$")
_NAME_OK = re.compile(r"^[A-Za-z0-9 ._-]+$")
_USER_OK = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass(frozen=True)
class Server:
    id: str
    name: str
    host: str
    ssh_user: str
    ssh_port: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class InventoryError(ValueError):
    """Validation or inventory error with a user-facing message."""


def _clean(value: str | None, field: str) -> str:
    text = (value or "").strip()
    if not text:
        raise InventoryError(f"{field} is required.")
    if _UNSAFE.search(text):
        raise InventoryError(f"{field} contains invalid characters.")
    return text


def validate_server_input(
    name: str | None,
    host: str | None,
    ssh_user: str | None,
    ssh_port: str | int | None,
) -> tuple[str, str, str, int]:
    """Validate and sanitize add-server fields. Never treats input as a shell command."""
    clean_name = _clean(name, "Server name")
    clean_host = _clean(host, "Hostname / IP")
    clean_user = _clean(ssh_user, "SSH username")

    if not _NAME_OK.match(clean_name):
        raise InventoryError("Server name has invalid characters.")
    if not _HOST_OK.match(clean_host):
        raise InventoryError("Hostname / IP has invalid characters.")
    if not _USER_OK.match(clean_user):
        raise InventoryError("SSH username has invalid characters.")

    if ssh_port is None or str(ssh_port).strip() == "":
        port = 22
    else:
        try:
            port = int(str(ssh_port).strip())
        except (TypeError, ValueError) as exc:
            raise InventoryError("SSH port must be a number.") from exc
    if port < 1 or port > 65535:
        raise InventoryError("SSH port must be between 1 and 65535.")

    return clean_name, clean_host, clean_user, port


class ServerInventory:
    """Process-memory store for registered servers. No SSH credentials are stored beyond user/port."""

    def __init__(self) -> None:
        self._servers: dict[str, Server] = {}

    def list_servers(self) -> list[Server]:
        return sorted(self._servers.values(), key=lambda s: s.name.lower())

    def get(self, server_id: str) -> Server | None:
        return self._servers.get(server_id)

    def add(
        self,
        name: str | None,
        host: str | None,
        ssh_user: str | None,
        ssh_port: str | int | None = 22,
    ) -> Server:
        clean_name, clean_host, clean_user, port = validate_server_input(
            name, host, ssh_user, ssh_port
        )
        server = Server(
            id=uuid.uuid4().hex,
            name=clean_name,
            host=clean_host,
            ssh_user=clean_user,
            ssh_port=port,
        )
        self._servers[server.id] = server
        return server

    def remove(self, server_id: str) -> bool:
        """Remove from local inventory only — does not change the remote host."""
        if server_id not in self._servers:
            return False
        del self._servers[server_id]
        return True

    def clear(self) -> None:
        self._servers.clear()
