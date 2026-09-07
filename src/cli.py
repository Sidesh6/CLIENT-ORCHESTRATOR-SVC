"""
CLI Interface for Client Orchestrator Service.
"""

import sys
import time
import click
import uvicorn
from src.config.settings import settings
from src.database.session import SessionLocal, check_db_connection, init_db
from src.schemas.workflow import PipelineRunRequest
from src.services.service_registry import GLOBAL_REGISTRY
from src.workflows.pipeline_runner import PipelineRunner


@click.group()
def cli() -> None:
    """Client Orchestrator Service CLI."""
    pass


@cli.command("init-db")
def cmd_init_db() -> None:
    """Initialize database tables."""
    click.secho("[+] Initializing Orchestrator database...", fg="cyan")
    init_db()
    if check_db_connection():
        click.secho("[OK] Database initialized successfully!", fg="green")
    else:
        click.secho("[ERROR] Failed to connect to database.", fg="red", err=True)
        sys.exit(1)


@cli.command("run-server")
@click.option("--host", default=None, help="Host to bind.")
@click.option("--port", default=None, type=int, help="Port to bind.")
@click.option("--reload", is_flag=True, default=False, help="Auto-reload.")
def cmd_run_server(host: str | None, port: int | None, reload: bool) -> None:
    """Start Client Orchestrator REST API."""
    bind_host = host or settings.app_host
    bind_port = port or settings.app_port
    click.secho(f"[*] Starting Client Orchestrator Service on http://{bind_host}:{bind_port}", fg="green")
    click.secho(f"[*] Swagger Docs: http://{bind_host}:{bind_port}/docs", fg="cyan")
    uvicorn.run("src.api.main:app", host=bind_host, port=bind_port, reload=reload)


@cli.command("check-services")
def cmd_check_services() -> None:
    """Check health and latency of all 5 platform services."""
    click.secho("[*] Checking status of all 5 platform services...", fg="cyan")
    topology = GLOBAL_REGISTRY.get_topology()

    click.secho(f"\n--- Platform Topology: {topology.online_count}/{topology.total_services} Online ---\n", fg="cyan", bold=True)
    for s in topology.services:
        color = "green" if s.status == "online" else ("yellow" if s.status == "degraded" else "red")
        lat_str = f"({s.latency_ms} ms)" if s.latency_ms is not None else ""
        click.secho(f"* [{s.status.upper()}] {s.name:26} {lat_str:>10} -> {s.url}", fg=color)
    click.echo()


@cli.command("run-pipeline")
@click.option("--min-score", default=75.0, type=float, help="Min score to qualify.")
@click.option("--limit", default=20, type=int, help="Max leads to fetch from finder.")
def cmd_run_pipeline(min_score: float, limit: int) -> None:
    """Run full end-to-end multi-service pipeline."""
    click.secho(f"[*] Triggering orchestrated pipeline (min_score={min_score}, limit={limit})...", fg="cyan")
    req = PipelineRunRequest(min_qualification_score=min_score, limit=limit)
    with SessionLocal() as session:
        runner = PipelineRunner(session)
        result = runner.run_pipeline(req)

    status_color = "green" if result.status == "completed" else "yellow"
    click.secho(f"\n[+] Pipeline Run [{result.status.upper()}]:", fg=status_color, bold=True)
    click.secho(f"  • Run ID: {result.id}")
    click.secho(f"  • Discovered: {result.leads_discovered_count}")
    click.secho(f"  • Enriched: {result.leads_enriched_count}")
    click.secho(f"  • Saved to CRM: {result.leads_saved_count}")
    click.secho(f"  • Proposals Staged in Queue: {result.proposals_staged_count}")
    if result.errors:
        click.secho(f"  • Errors ({len(result.errors)}):", fg="red")
        for err in result.errors[:3]:
            click.secho(f"    * {err}", fg="red")
    click.echo()


@cli.command("daemon")
@click.option("--interval", default=15, type=int, help="Interval in minutes between runs.")
@click.option("--min-score", default=75.0, type=float, help="Min score to qualify.")
def cmd_daemon(interval: int, min_score: float) -> None:
    """Run pipeline continuously in background daemon mode."""
    click.secho(f"[*] Starting Orchestrator daemon (every {interval} min, min_score={min_score})...", fg="green")
    while True:
        try:
            req = PipelineRunRequest(min_qualification_score=min_score, limit=25)
            with SessionLocal() as session:
                runner = PipelineRunner(session)
                res = runner.run_pipeline(req)
                click.secho(f"[{time.strftime('%X')}] Ran pipeline: {res.leads_discovered_count} discovered, {res.proposals_staged_count} proposals staged.", fg="bright_black")
        except Exception as e:
            click.secho(f"[!] Daemon error: {str(e)}", fg="red")

        time.sleep(interval * 60)


if __name__ == "__main__":
    cli()
