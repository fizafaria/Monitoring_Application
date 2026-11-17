# Implementation TODO
## Demo Linux Infrastructure Monitoring Application

Work in **very small increments**. Each item should be completable and reviewable on its own. Prefer the simplest approach that satisfies [requirements.md](requirements.md). Local demo only—no database, cloud, or production HA.

Legend: `[ ]` todo · `[x]` done

---

## Phase 0 — Project foundation

### 0.1 Project initialization and basic UI
- [x] Create project layout (`app/`, `templates/`, `static/`, `tests/`, `docs/`)
- [x] Add `requirements.txt` with minimal deps (Flask, and later Paramiko/SSH only when needed)
- [x] Add `.gitignore` (venv, `__pycache__`, `.env`, secrets)
- [x] Create minimal Flask app entrypoint that serves a home/placeholder page
- [x] Add basic HTML base template + clean CSS (responsive layout shell, no heavy frameworks)
- [x] **Security:** do not commit secrets; document that secrets stay in env/local config
- [x] **Docs:** short `README.md` with what the app is and how to create a venv + run Flask locally

### 0.2 Local run checklist
- [x] Document one-command (or few-step) local start in `README.md`
- [x] Verify app opens in browser on localhost

---

## Phase 1 — Sign-in and tests

### 1.1 Authentication (single admin)
- [x] Add login page (username + password)
- [x] Implement single default `admin` user with **hashed** password verification
- [x] Protect routes so unauthenticated users are redirected to login
- [x] Add logout
- [x] **Security:** store password hash only (never plain text); use Flask secret key from env; secure session cookie flags appropriate for local demo
- [x] **Docs:** document default username and how to set/generate the password hash locally (no real passwords in repo)

### 1.2 Unit tests for auth
- [x] Add pytest (or Flask test client) setup
- [x] Test: login success with correct credentials
- [x] Test: login failure with wrong password
- [x] Test: protected page redirects when logged out
- [x] Test: logout clears session
- [x] **Docs:** note how to run tests in `README.md`

---

## Phase 2 — Server inventory (in-memory)

### 2.1 In-memory server store
- [x] Add simple in-memory structure for registered servers
- [x] Fields: server name, hostname/IP, SSH user, SSH port
- [x] **Security:** do not log SSH credentials; keep inventory in process memory only
- [x] **Docs:** note that inventory resets on app restart (demo behavior)

### 2.2 Add / remove servers (UI + routes)
- [x] Form to add a Linux server (name, hostname/IP, SSH user, SSH port; default port 22)
- [x] List registered servers on a basic page
- [x] Remove server from in-memory inventory only (no remote changes)
- [x] Basic validation (required fields, sensible port)
- [x] **Security:** require login for add/remove; validate/sanitize inputs; never execute user input as shell on the app host
- [x] Unit tests: add server, reject invalid input, remove server
- [x] **Docs:** document add-server fields and demo limits

---

## Phase 3 — SSH collection (read-only foundation)

### 3.1 SSH helper (read-only)
- [x] Add minimal SSH client helper (e.g. Paramiko) used only for read commands
- [x] Connection using hostname/IP, user, port (+ key path from env/config if needed)
- [x] Hard rule in code/comments: **no** restart, kill, config change, reboot, or write actions
- [x] Graceful error when host unreachable
- [x] **Security:** prefer key-based auth via local config; never commit private keys; timeouts on SSH; disallow dangerous command patterns
- [x] Unit tests: mock SSH success/failure paths
- [x] **Docs:** document required SSH access for demo hosts and read-only policy

---

## Phase 4 — Metrics (incremental)

### 4.1 CPU metrics
- [x] Collect CPU usage over SSH (read-only)
- [x] Return structured data to the app
- [x] Show CPU on a simple per-server view
- [x] Unit tests with mocked SSH for CPU parsing
- [x] **Security:** use fixed, allowlisted remote commands only
- [x] **Docs:** brief note on which CPU signal is shown

### 4.2 Memory metrics
- [x] Collect memory used/total (and %) over SSH
- [x] Display alongside CPU
- [x] Unit tests with mocked SSH for memory parsing
- [x] **Security:** allowlisted commands only
- [x] **Docs:** brief note on memory fields shown

### 4.3 Network metrics
- [x] Collect network usage/status over SSH
- [x] Display on server view
- [x] Unit tests with mocked SSH for network parsing
- [x] **Security:** allowlisted commands only
- [x] **Docs:** brief note on network fields shown

### 4.4 Listening ports
- [x] Collect listening port details over SSH
- [x] Display on server detail view
- [x] Unit tests with mocked SSH for port parsing
- [x] **Security:** allowlisted commands only; do not expose unrelated host files
- [x] **Docs:** brief note on how ports are listed

---

## Phase 5 — Modern interactive dashboard (PRD UI)

### 5.1 Overview dashboard with server cards
- [x] Build overview page of all servers as clean cards
- [x] Each card: name, IP/hostname, availability, CPU, memory, network status
- [x] Responsive, professional layout (CSS only + light JS)
- [x] **Docs:** screenshot or short UI description in README (optional for demo)

### 5.2 Health status visuals
- [x] Green / amber / red health indicators
- [x] Define simple thresholds for healthy / warning / critical (and unreachable = critical/red)
- [x] CPU and memory progress bars or gauges
- [x] Unit tests for health classification helpers
- [x] **Docs:** document threshold rules

### 5.3 Server detail view
- [x] Click/select card → detail page for one server
- [x] Detail shows CPU, memory, network, listening ports
- [x] Clear error state when unreachable
- [x] **Docs:** describe navigation overview → detail

### 5.4 Search and filter
- [x] Search by server name or IP/hostname
- [x] Filter by health status (healthy / warning / critical)
- [x] Keep interaction simple (no heavy libraries)
- [x] Unit/UI-logic tests for filter helpers where practical
- [x] **Docs:** note search/filter behavior

### 5.5 Auto refresh, manual refresh, last refreshed
- [x] Auto-refresh metrics at a reasonable interval (e.g. 5–10s)
- [x] Manual Refresh button
- [x] Show last refreshed time
- [x] **Security:** refresh endpoints require auth; rate-limit lightly if easy (optional for demo)
- [x] **Docs:** document refresh interval and manual refresh

### 5.6 Dashboard polish (small UI enhancements)
- [x] Online/offline badges
- [x] Summary cards: total servers, healthy / warning / critical counts
- [x] Hover effects on cards
- [x] Empty state when no servers registered
- [x] Error/unreachable state messaging
- [x] Keep UI clean—no unnecessary widgets
- [x] **Docs:** update README with final demo walkthrough

---

## Phase 6 — CI/CD (GitHub Actions, minimal)

### 6.1 GitHub Actions workflow
- [x] Add `.github/workflows/ci.yml`
- [x] On push/PR: install deps, run unit tests, (optional) lint if already configured
- [x] No deploy jobs, no cloud targets, no containers required unless already trivial
- [x] **Security:** do not inject real SSH keys or passwords into CI; use mocks/fakes in tests
- [x] **Docs:** document what CI runs and how to check status

---

## Phase 7 — Final demo readiness

### 7.1 End-to-end local demo pass
- [x] Fresh venv → install → run → login → add server → overview → detail → search/filter → auto + manual refresh
- [x] Confirm read-only behavior (no mutate commands in SSH helper)
- [x] Confirm inventory is in-memory and resets on restart
- [x] **Security:** quick checklist (hash auth, no secrets in git, protected routes, allowlisted SSH commands)
- [x] **Docs:** finalize `README.md` + ensure PRD/TODO links are clear

### 7.2 Acceptance criteria checklist (from PRD)
- [x] Unauthenticated access blocked
- [x] `admin` + hashed password login works
- [x] Add server with name, hostname/IP, SSH user, SSH port
- [x] In-memory inventory
- [x] Cards show name, IP/hostname, status, CPU, memory, network
- [x] Green/amber/red + progress bars/gauges
- [x] Detail view: CPU, memory, network, ports
- [x] Auto + manual refresh + last refreshed time
- [x] Search/filter by name/IP and health
- [x] Summary counts + badges + empty/error states
- [x] SSH collection from Flask
- [x] No modifications to monitored servers
- [x] Runs locally where Cursor is running

---

## Explicit non-goals (do not implement)

- Windows monitoring
- Historical storage / complex graphs
- Alerts, email/SMS
- RBAC / multi-user
- HTTPS / production hardening beyond basic demo hygiene
- Databases, cloud deploy, HA
- Server remediation actions
- Extra frameworks or infrastructure not required by the PRD
