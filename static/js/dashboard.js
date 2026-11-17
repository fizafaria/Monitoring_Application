(() => {
  const grid = document.getElementById("card-grid");
  if (!grid) return;

  const api = grid.dataset.api;
  const refreshMs = Number(grid.dataset.refreshMs || 8000);
  const lastEl = document.getElementById("last-refreshed");
  const btn = document.getElementById("refresh-btn");
  const qInput = document.getElementById("filter-q");
  const healthSelect = document.getElementById("filter-health");

  function formatBytes(n) {
    if (n == null) return "—";
    if (n < 1024) return `${n} B`;
    if (n < 1048576) return `${(n / 1024).toFixed(1)} KB`;
    return `${(n / 1048576).toFixed(1)} MB`;
  }

  function applyClientFilter() {
    const q = (qInput?.value || "").trim().toLowerCase();
    const health = (healthSelect?.value || "all").toLowerCase();
    let visible = 0;
    grid.querySelectorAll(".server-card").forEach((card) => {
      const name = card.dataset.name || "";
      const host = card.dataset.host || "";
      const h = card.dataset.health || "";
      const matchQ = !q || name.includes(q) || host.includes(q);
      const matchH = health === "all" || h === health;
      const show = matchQ && matchH;
      card.hidden = !show;
      if (show) visible += 1;
    });
    let empty = document.getElementById("empty-state");
    if (!empty && visible === 0) {
      empty = document.createElement("div");
      empty.className = "empty-state";
      empty.id = "empty-state";
      empty.textContent = "No servers match this search/filter.";
      grid.appendChild(empty);
    } else if (empty && visible > 0) {
      empty.remove();
    } else if (empty && visible === 0) {
      empty.hidden = false;
    }
  }

  function updateCard(card, m) {
    card.dataset.health = m.health;
    card.className = `server-card health-${m.health}`;
    const badge = card.querySelector(".badge");
    if (badge) {
      badge.className = `badge badge-${m.health}`;
      badge.textContent = m.reachable ? m.health : "offline";
    }
    if (!m.reachable) {
      card.querySelectorAll(".metric-block, .card-net").forEach((el) => el.remove());
      let err = card.querySelector(".card-error");
      if (!err) {
        err = document.createElement("p");
        err.className = "card-error";
        card.appendChild(err);
      }
      err.textContent = m.error || "Unreachable";
      return;
    }
    const err = card.querySelector(".card-error");
    if (err) err.remove();
    const cpu = card.querySelector(".card-cpu");
    const mem = card.querySelector(".card-mem");
    const bars = card.querySelectorAll(".bar-fill");
    if (cpu) cpu.textContent = `${m.cpu_percent}%`;
    if (mem) mem.textContent = `${m.memory_percent}%`;
    if (bars[0]) {
      bars[0].style.width = `${m.cpu_percent}%`;
      bars[0].className = `bar-fill bar-${m.health}`;
    }
    if (bars[1]) {
      bars[1].style.width = `${m.memory_percent}%`;
      bars[1].className = `bar-fill bar-${m.health}`;
    }
    const net = card.querySelector(".card-net");
    if (net) {
      net.textContent = `Network: ${m.network_status} · RX ${formatBytes(m.network_rx_bytes)} / TX ${formatBytes(m.network_tx_bytes)}`;
    }
  }

  async function refresh() {
    try {
      const res = await fetch(api, { credentials: "same-origin" });
      if (!res.ok) return;
      const data = await res.json();
      if (lastEl) lastEl.textContent = `Last refreshed: ${data.last_refreshed}`;
      if (data.summary) {
        const map = {
          "sum-total": data.summary.total,
          "sum-healthy": data.summary.healthy,
          "sum-warning": data.summary.warning,
          "sum-critical": data.summary.critical,
        };
        Object.entries(map).forEach(([id, val]) => {
          const el = document.getElementById(id);
          if (el) el.textContent = val;
        });
      }
      const byId = Object.fromEntries((data.metrics || []).map((m) => [m.server_id, m]));
      grid.querySelectorAll(".server-card").forEach((card) => {
        const m = byId[card.dataset.id];
        if (m) updateCard(card, m);
      });
      applyClientFilter();
    } catch (_) {
      /* keep last good UI on transient errors */
    }
  }

  btn?.addEventListener("click", () => refresh());
  qInput?.addEventListener("input", applyClientFilter);
  healthSelect?.addEventListener("change", applyClientFilter);
  setInterval(refresh, refreshMs);
})();
