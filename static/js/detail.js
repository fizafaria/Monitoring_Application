(() => {
  const root = document.getElementById("detail-root");
  if (!root) return;
  const api = root.dataset.api;
  const refreshMs = Number(root.dataset.refreshMs || 8000);
  const lastEl = document.getElementById("last-refreshed");
  const btn = document.getElementById("refresh-btn");

  function renderPorts(ports) {
    const el = document.getElementById("d-ports");
    if (!el) return;
    if (!ports || !ports.length) {
      el.innerHTML = '<p class="empty-state">No listening ports reported.</p>';
      return;
    }
    const rows = ports
      .map((p) => `<tr><td>${p.protocol}</td><td><code>${p.local_address}</code></td></tr>`)
      .join("");
    el.innerHTML = `<table class="ports-table"><thead><tr><th>Protocol</th><th>Local address</th></tr></thead><tbody>${rows}</tbody></table>`;
  }

  async function refresh() {
    try {
      const res = await fetch(api, { credentials: "same-origin" });
      if (!res.ok) return;
      const data = await res.json();
      const m = data.metrics;
      if (lastEl) lastEl.textContent = `Last refreshed: ${data.last_refreshed}`;
      if (!m.reachable) {
        root.innerHTML = `<div class="empty-state error-state"><strong>Unreachable</strong><p>${m.error || "Could not collect metrics over SSH."}</p></div>`;
        return;
      }
      const cpu = document.getElementById("d-cpu");
      const mem = document.getElementById("d-mem");
      const cpuBar = document.getElementById("d-cpu-bar");
      const memBar = document.getElementById("d-mem-bar");
      const memText = document.getElementById("d-mem-text");
      const netStatus = document.getElementById("d-net-status");
      const netBytes = document.getElementById("d-net-bytes");
      if (cpu) cpu.textContent = `${m.cpu_percent}%`;
      if (mem) mem.textContent = `${m.memory_percent}%`;
      if (cpuBar) {
        cpuBar.style.width = `${m.cpu_percent}%`;
        cpuBar.className = `bar-fill bar-${m.health}`;
      }
      if (memBar) {
        memBar.style.width = `${m.memory_percent}%`;
        memBar.className = `bar-fill bar-${m.health}`;
      }
      if (memText) memText.textContent = `${m.memory_used_mb} / ${m.memory_total_mb} MB used`;
      if (netStatus) netStatus.textContent = m.network_status;
      if (netBytes) {
        netBytes.textContent = `RX ${m.network_rx_bytes} bytes · TX ${m.network_tx_bytes} bytes (totals since boot, non-lo)`;
      }
      renderPorts(m.listening_ports);
    } catch (_) {
      /* ignore transient */
    }
  }

  btn?.addEventListener("click", () => refresh());
  setInterval(refresh, refreshMs);
})();
