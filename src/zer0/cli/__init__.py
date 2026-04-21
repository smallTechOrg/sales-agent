"""CLI entry point — operator interface for local dev, admin, and debugging.

Spec: spec/product/06-cli.md
"""

from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.table import Table

console = Console()


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------

@click.group()
@click.option("--json-log", is_flag=True, default=False, help="Emit JSON structured logs.")
@click.option("-v", "verbose", is_flag=True, default=False, help="Debug verbosity.")
@click.pass_context
def cli(ctx: click.Context, json_log: bool, verbose: bool) -> None:
    """Zer0 — autonomous sales agent platform operator CLI."""
    ctx.ensure_object(dict)
    ctx.obj["json_log"] = json_log
    ctx.obj["verbose"] = verbose


# ---------------------------------------------------------------------------
# zer0 version
# ---------------------------------------------------------------------------

@cli.command()
def version() -> None:
    """Print the installed Zer0 version."""
    from importlib.metadata import version as _ver

    try:
        v = _ver("zer0")
    except Exception:
        v = "unknown"
    click.echo(f"zer0 {v}")


# ---------------------------------------------------------------------------
# zer0 config show
# ---------------------------------------------------------------------------

@cli.command("config")
@click.argument("subcommand", default="show")
def config_cmd(subcommand: str) -> None:
    """Show current settings (secrets are masked)."""
    if subcommand != "show":
        click.echo(f"Unknown subcommand: {subcommand}", err=True)
        sys.exit(1)

    _secret_fields = {
        "gemini_api_key",
        "tavily_api_key",
        "credential_encryption_key",
        "jwt_secret",
        "google_client_id",
        "google_client_secret",
    }

    try:
        from zer0.config.settings import get_settings

        s = get_settings()
    except Exception as exc:
        console.print(f"[red]Configuration error:[/red] {exc}")
        sys.exit(3)

    table = Table(show_header=False, box=None)
    for field_name in s.model_fields:
        raw = getattr(s, field_name, "")
        value = "***" if field_name in _secret_fields else str(raw)
        table.add_row(f"ZER0_{field_name.upper()}:", value)
    console.print(table)


# ---------------------------------------------------------------------------
# zer0 health
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--tenant", "tenant_id", default=None, help="Check credentials for a specific tenant.")
def health(tenant_id: str | None) -> None:
    """Check configured services.

    Exit 0 = all ok, 1 = not found, 2 = one or more FAILED.
    """
    all_ok = True

    try:
        from zer0.config.settings import get_settings
        from zer0.db.session import create_db_session

        s = get_settings()

        # Database
        try:
            with create_db_session() as session:
                session.execute(__import__("sqlalchemy").text("SELECT 1"))
            console.print("  Database:       [green]ok[/green]")
        except Exception as exc:
            console.print(f"  Database:       [red]FAILED[/red] — {exc}")
            all_ok = False

        # LLM
        try:
            import google.generativeai as genai

            genai.configure(api_key=s.gemini_api_key)
            console.print(f"  LLM ({s.llm_provider}):   [green]ok[/green]")
        except Exception as exc:
            console.print(f"  LLM ({s.llm_provider}):   [red]FAILED[/red] — {exc}")
            all_ok = False

    except Exception as exc:
        console.print(f"[red]Config error:[/red] {exc}")
        sys.exit(3)

    if tenant_id:
        console.print(f"\nTenant: {tenant_id}")
        try:
            from zer0.db.models import TenantRow
            from zer0.db.session import create_db_session

            with create_db_session() as session:
                tenant = (
                    session.query(TenantRow)
                    .filter(TenantRow.id == tenant_id, TenantRow.deleted_at.is_(None))
                    .first()
                )
            if not tenant:
                console.print(f"  [red]Tenant {tenant_id!r} not found.[/red]")
                sys.exit(1)

            console.print(
                f"  Gmail:         {'[green]ok[/green]' if tenant.google_oauth_token_enc else '[yellow]not configured[/yellow]'}"
            )
            console.print(
                f"  WhatsApp:      {'[green]ok[/green]' if tenant.whatsapp_api_key_enc else '[yellow]not configured[/yellow]'}"
            )
            console.print(
                f"  Slack:         {'[green]ok[/green]' if tenant.slack_webhook_url_enc else '[yellow]not configured[/yellow]'}"
            )
        except Exception as exc:
            console.print(f"  [red]Error checking tenant:[/red] {exc}")
            all_ok = False

    sys.exit(0 if all_ok else 2)


# ---------------------------------------------------------------------------
# zer0 tenant
# ---------------------------------------------------------------------------

@cli.group()
def tenant() -> None:
    """Manage tenants."""


@tenant.command("list")
def tenant_list() -> None:
    """List all tenants."""
    try:
        from zer0.db.models import CampaignRow, TenantRow
        from zer0.db.session import create_db_session

        with create_db_session() as session:
            tenants = (
                session.query(TenantRow)
                .filter(TenantRow.deleted_at.is_(None))
                .order_by(TenantRow.name)
                .all()
            )
            campaign_counts = {
                row[0]: row[1]
                for row in session.query(CampaignRow.tenant_id, __import__("sqlalchemy").func.count())
                .filter(CampaignRow.deleted_at.is_(None))
                .group_by(CampaignRow.tenant_id)
                .all()
            }
    except Exception as exc:
        console.print(f"[red]DB error:[/red] {exc}")
        sys.exit(2)

    table = Table("ID", "NAME", "CAMPAIGNS")
    for t in tenants:
        table.add_row(t.id, t.name, str(campaign_counts.get(t.id, 0)))
    console.print(table)


@tenant.command("add")
@click.argument("tenant_id")
@click.option("--name", default=None, help="Display name (defaults to tenant_id).")
def tenant_add(tenant_id: str, name: str | None) -> None:
    """Insert a new tenant row."""
    import uuid

    from zer0.db.models import TenantRow
    from zer0.db.session import create_db_session

    display_name = name or tenant_id
    try:
        with create_db_session() as session:
            existing = session.query(TenantRow).filter(TenantRow.id == tenant_id).first()
            if existing:
                console.print(f"[red]Tenant {tenant_id!r} already exists.[/red]")
                sys.exit(1)
            session.add(TenantRow(id=tenant_id, name=display_name))
        console.print(f"[green]Created tenant {tenant_id!r} ({display_name}).[/green]")
    except SystemExit:
        raise
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(2)


@tenant.command("remove")
@click.argument("tenant_id")
@click.option("--force", is_flag=True, default=False, help="Skip confirmation prompt.")
def tenant_remove(tenant_id: str, force: bool) -> None:
    """Soft-delete a tenant and all its data."""
    from datetime import datetime, timezone

    from zer0.db.models import TenantRow
    from zer0.db.session import create_db_session

    if not force:
        click.confirm(
            f"Remove tenant {tenant_id!r} and ALL its data? This cannot be undone.",
            abort=True,
        )
    try:
        with create_db_session() as session:
            row = session.query(TenantRow).filter(TenantRow.id == tenant_id).first()
            if not row:
                console.print(f"[red]Tenant {tenant_id!r} not found.[/red]")
                sys.exit(1)
            row.deleted_at = datetime.now(tz=timezone.utc)
        console.print(f"[green]Tenant {tenant_id!r} removed.[/green]")
    except SystemExit:
        raise
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(2)


# ---------------------------------------------------------------------------
# zer0 campaign run
# ---------------------------------------------------------------------------

@cli.group()
def campaign() -> None:
    """Manage and trigger campaigns."""


@campaign.command("run")
@click.argument("campaign_id")
@click.option("--tenant", "tenant_id", required=True, help="Tenant ID owning the campaign.")
def campaign_run(campaign_id: str, tenant_id: str) -> None:
    """Trigger a campaign run synchronously.

    Exit 0 = completed, 1 = campaign not found, 2 = runtime error.
    """
    try:
        from zer0.graph.runner import run_campaign

        console.print(f"Running campaign [bold]{campaign_id}[/bold] for tenant [bold]{tenant_id}[/bold] …")
        final_state = run_campaign(campaign_id=campaign_id, tenant_id=tenant_id)
        console.print(
            f"[green]Done.[/green] "
            f"Leads discovered: {len(final_state.get('raw_leads', []))}  "
            f"qualified: {len(final_state.get('qualified_leads', []))}  "
            f"messages sent: {len(final_state.get('sent_messages', []))}"
        )
        if final_state.get("error"):
            console.print(f"[yellow]Run ended with error:[/yellow] {final_state['error']}")
            sys.exit(2)
    except Exception as exc:
        error_msg = str(exc)
        if "not found" in error_msg.lower():
            console.print(f"[red]Campaign not found:[/red] {error_msg}")
            sys.exit(1)
        console.print(f"[red]Runtime error:[/red] {error_msg}")
        sys.exit(2)


# ---------------------------------------------------------------------------
# zer0 events
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--tenant", "tenant_id", required=True, help="Tenant ID.")
@click.option("--limit", default=20, show_default=True, help="Number of events to show.")
def events(tenant_id: str, limit: int) -> None:
    """List recent events for a tenant.

    Exit 0 = success, 1 = tenant not found, 2 = DB error.
    """
    from datetime import datetime, timezone

    try:
        from zer0.db.models import EventRow, TenantRow
        from zer0.db.session import create_db_session

        with create_db_session() as session:
            tenant = session.query(TenantRow).filter(
                TenantRow.id == tenant_id, TenantRow.deleted_at.is_(None)
            ).first()
            if not tenant:
                console.print(f"[red]Tenant {tenant_id!r} not found.[/red]")
                sys.exit(1)

            rows = (
                session.query(EventRow)
                .filter(EventRow.tenant_id == tenant_id)
                .order_by(EventRow.created_at.desc())
                .limit(limit)
                .all()
            )

        now = datetime.now(tz=timezone.utc)
        table = Table("ID", "TIME", "TYPE", "CAMPAIGN", "LEAD")
        for ev in rows:
            age = now - ev.created_at if ev.created_at else None
            age_str = _human_age(age) if age else "-"
            table.add_row(
                ev.id[:8],
                age_str,
                ev.event_type,
                (ev.campaign_id or "-")[:8],
                (ev.lead_id or "-")[:8],
            )
        console.print(table)
    except SystemExit:
        raise
    except Exception as exc:
        console.print(f"[red]DB error:[/red] {exc}")
        sys.exit(2)


def _human_age(delta) -> str:  # type: ignore[no-untyped-def]
    total_seconds = int(delta.total_seconds())
    if total_seconds < 60:
        return f"{total_seconds}s ago"
    if total_seconds < 3600:
        return f"{total_seconds // 60}m ago"
    if total_seconds < 86400:
        return f"{total_seconds // 3600}h ago"
    return f"{total_seconds // 86400}d ago"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    cli(obj={})
