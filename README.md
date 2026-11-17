# Demo Linux Infrastructure Monitoring

Local Flask demo for **read-only** Linux monitoring (CPU, memory, network, listening ports) over SSH. Built for internal L1/L2/L3 and infra/app teams. See [docs/requirements.md](docs/requirements.md) and [docs/TODO.md](docs/TODO.md).

## Login (local demo)

| Field | Value |
|--------|--------|
| **Username** | `admin` |
| **Password** | `admin` |

Change the password by setting `ADMIN_PASSWORD_HASH` (hash only — never commit plain-text passwords).

## Quick start

```bash
cd Monitoring_Application
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open **http://127.0.0.1:5020** or **http://\<host-ip\>:5020** (listens on `0.0.0.0:5020` by default).

Overrides: `HOST=127.0.0.1 PORT=5030 python run.py`

### Demo walkthrough

1. Sign in as `admin` / `admin`
2. **Manage servers** → add name, hostname/IP, SSH user, SSH port (default 22)
3. **Dashboard** → cards with health, CPU/memory bars, network status
4. Open a card for **detail** (CPU, memory, network, listening ports)
5. Use search/filter; metrics **auto-refresh ~8s** and via **Refresh**

Inventory is **in-memory** and resets when the app restarts. Removing a server from the app does **not** change the remote host.

## SSH access (read-only)

The app connects with Paramiko using hostname/IP, SSH user, and port from inventory.

Optional env (never commit secrets):

| Variable | Purpose |
|----------|---------|
| `SSH_KEY_PATH` | Path to private key (preferred) |
| `SSH_PASSWORD` | Password auth for lab demos only |
| `FLASK_SECRET_KEY` | Session signing |
| `ADMIN_PASSWORD_HASH` | Werkzeug password hash for `admin` |

Generate a password hash:

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('YOUR_PASSWORD'))"
```

### Read-only policy

- Only **allowlisted** remote commands run (see `app/ssh_client.py`)
- **No** restart, kill, config change, reboot, or write actions
- Timeouts on SSH; private keys must stay local (gitignored)

### Metrics shown

| Metric | Source / meaning |
|--------|------------------|
| CPU % | Busy estimate from one `/proc/stat` sample |
| Memory | Used/total from `MemTotal` / `MemAvailable` in `/proc/meminfo` |
| Network | RX/TX byte totals (non-`lo`) from `/proc/net/dev` + up/down status |
| Ports | `ss -lntuH` listening sockets |

### Health thresholds

| Level | Rule |
|-------|------|
| Healthy (green) | Reachable and CPU & memory &lt; 70% |
| Warning (amber) | Reachable and CPU or memory ≥ 70% and &lt; 90% |
| Critical (red) | Unreachable, or CPU or memory ≥ 90% |

## Tests

```bash
source .venv/bin/activate
pytest -q
```

CI (GitHub Actions) installs deps and runs the same unit tests on push/PR. **No real SSH keys or passwords** are used in CI — SSH is mocked.

## Security checklist (demo)

- [x] Password stored as hash only
- [x] Secrets via env / `.env` (gitignored)
- [x] Routes protected after login
- [x] SSH commands allowlisted; no remediation actions
- [x] Inventory holds no SSH private keys (key path via env only)

## Project layout

```
app/                 Flask app (auth, inventory, SSH, metrics)
templates/           Dashboard, detail, manage, login
static/css|js        UI + light refresh/filter JS
tests/               Unit tests (mocked SSH)
.github/workflows/   CI
docs/                PRD + TODO
run.py               Local entrypoint
```
