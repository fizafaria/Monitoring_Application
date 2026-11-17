"""HTTP routes for the demo monitoring app."""

from datetime import datetime, timezone

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from app.auth import (
    is_authenticated,
    login_required,
    login_user,
    logout_user,
    verify_admin_credentials,
)
from app.inventory import InventoryError, ServerInventory
from app.metrics import collect_all_metrics, collect_server_metrics, filter_metrics, summarize_health

bp = Blueprint("main", __name__)


def _inventory() -> ServerInventory:
    return current_app.extensions["inventory"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


@bp.get("/")
@login_required
def index():
    """Overview dashboard with server cards and health summary."""
    servers = _inventory().list_servers()
    metrics = collect_all_metrics(servers)
    query = request.args.get("q", "")
    health = request.args.get("health", "all")
    filtered = filter_metrics(metrics, query=query, health=health)
    summary = summarize_health(metrics)
    return render_template(
        "dashboard.html",
        metrics=filtered,
        summary=summary,
        query=query,
        health_filter=health,
        last_refreshed=_utc_now_iso(),
        server_count=len(servers),
    )


@bp.get("/servers/manage")
@login_required
def manage_servers():
    """Add / remove servers (in-memory inventory)."""
    servers = _inventory().list_servers()
    return render_template("manage.html", servers=servers)


@bp.get("/servers/<server_id>")
@login_required
def server_detail(server_id: str):
    server = _inventory().get(server_id)
    if server is None:
        flash("Server not found.", "error")
        return redirect(url_for("main.index"))
    metrics = collect_server_metrics(server)
    return render_template(
        "detail.html",
        server=server,
        metrics=metrics,
        last_refreshed=_utc_now_iso(),
    )


@bp.get("/api/metrics")
@login_required
def api_metrics():
    """JSON metrics for auto/manual refresh (auth required)."""
    servers = _inventory().list_servers()
    collected = collect_all_metrics(servers)
    metrics = [m.to_dict() for m in collected]
    return jsonify(
        {
            "last_refreshed": _utc_now_iso(),
            "summary": summarize_health(collected),
            "metrics": metrics,
        }
    )


@bp.get("/api/metrics/<server_id>")
@login_required
def api_server_metrics(server_id: str):
    server = _inventory().get(server_id)
    if server is None:
        return jsonify({"error": "not found"}), 404
    metrics = collect_server_metrics(server)
    return jsonify(
        {"last_refreshed": _utc_now_iso(), "metrics": metrics.to_dict()}
    )


@bp.post("/servers")
@login_required
def add_server():
    """Register a Linux server in memory only — no remote changes."""
    try:
        _inventory().add(
            name=request.form.get("name"),
            host=request.form.get("host"),
            ssh_user=request.form.get("ssh_user"),
            ssh_port=request.form.get("ssh_port") or 22,
        )
        flash("Server added to inventory.", "info")
    except InventoryError as exc:
        flash(str(exc), "error")
    return redirect(request.referrer or url_for("main.manage_servers"))


@bp.post("/servers/<server_id>/delete")
@login_required
def delete_server(server_id: str):
    """Remove from in-memory inventory only — does not modify the remote host."""
    if _inventory().remove(server_id):
        flash("Server removed from inventory (remote host unchanged).", "info")
    else:
        flash("Server not found.", "error")
    return redirect(request.referrer or url_for("main.manage_servers"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if is_authenticated():
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if verify_admin_credentials(username, password):
            login_user()
            next_url = request.args.get("next") or url_for("main.index")
            if not next_url.startswith("/"):
                next_url = url_for("main.index")
            return redirect(next_url)
        flash("Invalid username or password.", "error")

    return render_template("login.html")


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Signed out.", "info")
    return redirect(url_for("main.login"))
