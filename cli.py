#!/usr/bin/env python3
"""PRISM CLI — Code Quality Metrics Platform."""

import click
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import Config
from core.orchestrator import Orchestrator


@click.group()
def cli():
    """PRISM — Code Quality Metrics Platform."""
    pass


@cli.command()
@click.argument("path")
@click.option("--agents", "-a", multiple=True, help="Specific agents to run")
@click.option("--output", "-o", default=None, help="Output file path")
def analyze(path, agents, output):
    """Analyze a codebase or file."""
    config = Config()
    orchestrator = Orchestrator(config)

    if not os.path.exists(path):
        click.echo(f"Error: Path '{path}' not found", err=True)
        sys.exit(1)

    if os.path.isfile(path):
        with open(path, "r") as f:
            code = f.read()
    else:
        code = ""
        for root, dirs, files in os.walk(path):
            for fname in files:
                if fname.endswith((".py", ".js", ".ts", ".java", ".go", ".rs")):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r") as f:
                            code += f"\n--- {fpath} ---\n" + f.read()
                    except Exception:
                        pass

    click.echo(f"Analyzing: {path}")
    click.echo(f"Code size: {len(code):,} chars\n")

    agent_list = list(agents) if agents else None
    results = asyncio.run(orchestrator.analyze(code, {"path": path}, agent_list))

    for agent_name, report in results.items():
        findings = report.get("findings", [])
        metrics = report.get("metrics", {})
        tokens = report.get("tokens_used", 0)
        click.echo(f"  {agent_name}: {len(findings)} findings, {tokens:,} tokens")

    if output:
        with open(output, "w") as f:
            json.dump(results, f, indent=2)
        click.echo(f"\nResults saved to {output}")


@cli.command()
def agents():
    """List all available agents."""
    config = Config()
    orchestrator = Orchestrator(config)

    click.echo("PRISM Agents:")
    click.echo("=" * 60)
    for name, agent in orchestrator.agents.items():
        est = getattr(agent, "token_estimate", "N/A")
        doc = agent.__doc__ or "No description"
        click.echo(f"  {name}")
        click.echo(f"    Tokens: ~{est:,}/scan" if isinstance(est, int) else f"    Tokens: {est}")
        click.echo(f"    {doc.strip()[:80]}")
        click.echo()


@cli.command()
def stats():
    """Show token consumption statistics."""
    from core.token_tracker import TokenTracker

    tracker = TokenTracker()
    stats = tracker.get_daily_stats()

    click.echo("PRISM Daily Token Statistics:")
    click.echo("=" * 60)
    click.echo(f"  Total consumed: {stats.get('total_tokens', 0):,}")
    click.echo(f"  Total analyses: {stats.get('total_analyses', 0)}")
    click.echo(f"  Avg per analysis: {stats.get('avg_per_analysis', 0):,.0f}")


@cli.command()
@click.option("--port", "-p", default=8081, help="Port number")
def dashboard(port):
    """Start the web dashboard."""
    click.echo(f"Starting PRISM dashboard on port {port}...")
    os.environ["PRISM_PORT"] = str(port)
    from web.app import app
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    cli()
