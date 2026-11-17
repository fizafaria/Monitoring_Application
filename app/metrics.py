"""Collect and parse read-only Linux metrics over SSH."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from app.inventory import Server
from app.ssh_client import SSHError, run_readonly

# Thresholds (documented in README)
CPU_WARN = 70.0
CPU_CRIT = 90.0
MEM_WARN = 70.0
MEM_CRIT = 90.0

CMD_CPU = "grep '^cpu ' /proc/stat"
CMD_MEM = "grep -E '^(MemTotal|MemAvailable):' /proc/meminfo"
CMD_NET = "cat /proc/net/dev"
CMD_PORTS = "ss -lntuH"


@dataclass
class ServerMetrics:
    server_id: str
    name: str
    host: str
    reachable: bool
    health: str  # healthy | warning | critical
    error: str | None = None
    cpu_percent: float | None = None
    memory_used_mb: float | None = None
    memory_total_mb: float | None = None
    memory_percent: float | None = None
    network_rx_bytes: int | None = None
    network_tx_bytes: int | None = None
    network_status: str = "unknown"
    listening_ports: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_health(
    reachable: bool,
    cpu_percent: float | None,
    memory_percent: float | None,
) -> str:
    """Green / amber / red classification for dashboard badges."""
    if not reachable:
        return "critical"
    cpu = cpu_percent if cpu_percent is not None else 0.0
    mem = memory_percent if memory_percent is not None else 0.0
    if cpu >= CPU_CRIT or mem >= MEM_CRIT:
        return "critical"
    if cpu >= CPU_WARN or mem >= MEM_WARN:
        return "warning"
    return "healthy"


def parse_cpu(stat_line: str) -> float:
    """
    Approximate CPU busy % from a single /proc/stat sample.
    busy = (total - idle - iowait) / total * 100
    """
    parts = stat_line.strip().split()
    if len(parts) < 5 or parts[0] != "cpu":
        raise ValueError("Unexpected /proc/stat format")
    values = [int(x) for x in parts[1:]]
    total = sum(values)
    idle = values[3] + (values[4] if len(values) > 4 else 0)
    if total <= 0:
        return 0.0
    busy = max(0.0, min(100.0, (total - idle) * 100.0 / total))
    return round(busy, 1)


def parse_memory(meminfo: str) -> tuple[float, float, float]:
    """Return used_mb, total_mb, percent from MemTotal/MemAvailable."""
    total_kb = None
    avail_kb = None
    for line in meminfo.splitlines():
        if line.startswith("MemTotal:"):
            total_kb = int(line.split()[1])
        elif line.startswith("MemAvailable:"):
            avail_kb = int(line.split()[1])
    if total_kb is None or avail_kb is None or total_kb <= 0:
        raise ValueError("Unexpected /proc/meminfo format")
    used_kb = max(0, total_kb - avail_kb)
    total_mb = round(total_kb / 1024.0, 1)
    used_mb = round(used_kb / 1024.0, 1)
    percent = round(used_kb * 100.0 / total_kb, 1)
    return used_mb, total_mb, percent


def parse_network(netdev: str) -> tuple[int, int, str]:
    """Sum RX/TX bytes across non-lo interfaces."""
    rx_total = 0
    tx_total = 0
    for line in netdev.splitlines():
        if ":" not in line:
            continue
        name, rest = line.split(":", 1)
        iface = name.strip()
        if iface == "lo":
            continue
        cols = rest.split()
        if len(cols) < 9:
            continue
        rx_total += int(cols[0])
        tx_total += int(cols[8])
    status = "up" if (rx_total > 0 or tx_total > 0 or "eth" in netdev or "ens" in netdev) else "down"
    if ":" in netdev and any(
        n.strip() and n.strip() != "lo"
        for n in (ln.split(":", 1)[0] for ln in netdev.splitlines() if ":" in ln)
    ):
        status = "up"
    return rx_total, tx_total, status


def parse_ports(ss_out: str) -> list[dict[str, str]]:
    """Parse `ss -lntuH` into protocol/address rows."""
    ports: list[dict[str, str]] = []
    for line in ss_out.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        proto = parts[0]
        local = parts[4]
        ports.append({"protocol": proto, "local_address": local})
    return ports


Runner = Callable[..., str]


def collect_server_metrics(
    server: Server,
    *,
    runner: Runner | None = None,
) -> ServerMetrics:
    """Fetch CPU, memory, network, and listening ports via allowlisted SSH reads."""
    run = runner or (
        lambda cmd, **_kw: run_readonly(
            server.host, server.ssh_user, server.ssh_port, cmd
        )
    )
    try:
        cpu_raw = run(CMD_CPU)
        mem_raw = run(CMD_MEM)
        net_raw = run(CMD_NET)
        ports_raw = run(CMD_PORTS)

        cpu = parse_cpu(cpu_raw.splitlines()[0] if cpu_raw.strip() else "")
        used_mb, total_mb, mem_pct = parse_memory(mem_raw)
        rx, tx, net_status = parse_network(net_raw)
        ports = parse_ports(ports_raw)
        health = classify_health(True, cpu, mem_pct)
        return ServerMetrics(
            server_id=server.id,
            name=server.name,
            host=server.host,
            reachable=True,
            health=health,
            cpu_percent=cpu,
            memory_used_mb=used_mb,
            memory_total_mb=total_mb,
            memory_percent=mem_pct,
            network_rx_bytes=rx,
            network_tx_bytes=tx,
            network_status=net_status,
            listening_ports=ports,
        )
    except (SSHError, ValueError, IndexError, OSError) as exc:
        return ServerMetrics(
            server_id=server.id,
            name=server.name,
            host=server.host,
            reachable=False,
            health="critical",
            error=str(exc),
            network_status="down",
        )


def collect_all_metrics(
    servers: list[Server],
    *,
    runner_factory: Callable[[Server], Runner] | None = None,
) -> list[ServerMetrics]:
    results: list[ServerMetrics] = []
    for server in servers:
        if runner_factory:
            results.append(collect_server_metrics(server, runner=runner_factory(server)))
        else:
            results.append(collect_server_metrics(server))
    return results


def summarize_health(metrics: list[ServerMetrics]) -> dict[str, int]:
    summary = {"total": len(metrics), "healthy": 0, "warning": 0, "critical": 0}
    for m in metrics:
        summary[m.health] = summary.get(m.health, 0) + 1
    return summary


def filter_metrics(
    metrics: list[ServerMetrics],
    *,
    query: str = "",
    health: str = "",
) -> list[ServerMetrics]:
    q = (query or "").strip().lower()
    h = (health or "").strip().lower()
    out: list[ServerMetrics] = []
    for m in metrics:
        if h and h != "all" and m.health != h:
            continue
        if q and q not in m.name.lower() and q not in m.host.lower():
            continue
        out.append(m)
    return out
