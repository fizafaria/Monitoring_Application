"""Unit tests for metric parsing, health, filter, and mocked SSH collection."""

from app.inventory import Server
from app.metrics import (
    classify_health,
    collect_server_metrics,
    filter_metrics,
    parse_cpu,
    parse_memory,
    parse_network,
    parse_ports,
    summarize_health,
    ServerMetrics,
)


SAMPLE_CPU = "cpu  1000 0 1000 8000 0 0 0 0 0 0"
SAMPLE_MEM = "MemTotal:       2048000 kB\nMemAvailable:   1024000 kB\n"
SAMPLE_NET = """Inter-|   Receive                                                Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo: 100 0 0 0 0 0 0 0 100 0 0 0 0 0 0 0
  eth0: 5000 1 0 0 0 0 0 0 9000 1 0 0 0 0 0 0
"""
SAMPLE_PORTS = "tcp   LISTEN 0 128 0.0.0.0:22 0.0.0.0:*\nudp   UNCONN 0 0 0.0.0.0:68 0.0.0.0:*\n"


def test_parse_cpu():
    pct = parse_cpu(SAMPLE_CPU)
    assert 0 <= pct <= 100
    assert pct == round((2000) * 100.0 / 10000, 1)  # busy without idle+iowait


def test_parse_memory():
    used, total, pct = parse_memory(SAMPLE_MEM)
    assert total == round(2048000 / 1024.0, 1)
    assert used == round(1024000 / 1024.0, 1)
    assert pct == 50.0


def test_parse_network():
    rx, tx, status = parse_network(SAMPLE_NET)
    assert rx == 5000
    assert tx == 9000
    assert status == "up"


def test_parse_ports():
    ports = parse_ports(SAMPLE_PORTS)
    assert len(ports) == 2
    assert ports[0]["protocol"] == "tcp"
    assert "22" in ports[0]["local_address"]


def test_classify_health():
    assert classify_health(False, 10, 10) == "critical"
    assert classify_health(True, 50, 50) == "healthy"
    assert classify_health(True, 75, 50) == "warning"
    assert classify_health(True, 95, 50) == "critical"


def test_filter_and_summary():
    items = [
        ServerMetrics("1", "web", "10.0.0.1", True, "healthy"),
        ServerMetrics("2", "db", "10.0.0.2", False, "critical", error="down"),
    ]
    assert summarize_health(items) == {
        "total": 2,
        "healthy": 1,
        "warning": 0,
        "critical": 1,
    }
    assert len(filter_metrics(items, query="web")) == 1
    assert len(filter_metrics(items, health="critical")) == 1


def test_collect_server_metrics_mocked_success():
    server = Server("abc", "web-01", "10.0.0.10", "monitor", 22)

    def runner(cmd, **_kw):
        return {
            "grep '^cpu ' /proc/stat": SAMPLE_CPU,
            "grep -E '^(MemTotal|MemAvailable):' /proc/meminfo": SAMPLE_MEM,
            "cat /proc/net/dev": SAMPLE_NET,
            "ss -lntuH": SAMPLE_PORTS,
        }[cmd]

    m = collect_server_metrics(server, runner=runner)
    assert m.reachable is True
    assert m.cpu_percent is not None
    assert m.memory_percent == 50.0
    assert m.network_status == "up"
    assert len(m.listening_ports) == 2
    assert m.health in ("healthy", "warning", "critical")


def test_collect_server_metrics_mocked_failure():
    server = Server("abc", "web-01", "10.0.0.10", "monitor", 22)

    def runner(_cmd, **_kw):
        raise ConnectionError("timed out")

    m = collect_server_metrics(server, runner=runner)
    assert m.reachable is False
    assert m.health == "critical"
    assert m.error
