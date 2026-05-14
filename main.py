"""
Entry point. Run the full crash-analysis pipeline or a specific phase.

Usage:
    python main.py                          # full pipeline
    python main.py --phase fetch            # only fetch crashes
    python main.py --phase analyze          # fetch + analyze (no fix/PR)
    python main.py --dry-run                # analyze only, skip Jira/GitHub writes
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

from agent.utils.logger import get_logger
from config import load_config

console = Console()
log = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="maui-crash-agent",
        description="Automated .NET MAUI crash analysis and remediation",
    )
    p.add_argument("--phase", choices=["fetch", "analyze", "ticket", "fix", "pr", "report", "full"], default="full")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--max-crashes", type=int, default=10, metavar="N")
    return p.parse_args()


async def run(args: argparse.Namespace) -> int:
    from agent.core.agent import CrashAgent
    try:
        cfg = load_config()
    except EnvironmentError as e:
        console.print(f"[bold red]Configuration error:[/] {e}")
        return 1

    cfg.firebase.max_crashes = args.max_crashes
    agent = CrashAgent(cfg, dry_run=args.dry_run)

    try:
        if args.phase == "full":
            await agent.run_full_pipeline()
        elif args.phase == "fetch":
            crashes = await agent.fetch_crashes()
            console.print(f"[green]Fetched {len(crashes)} crashes.[/]")
        elif args.phase == "analyze":
            crashes = await agent.fetch_crashes()
            await agent.analyze_crashes(crashes)
        elif args.phase == "report":
            await agent.generate_report_only()
        return 0
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/]")
        return 130
    except Exception as e:
        log.exception("Unhandled error in main pipeline")
        console.print(f"[bold red]Fatal error:[/] {e}")
        return 1


if __name__ == "__main__":
    args = parse_args()
    sys.exit(asyncio.run(run(args)))
