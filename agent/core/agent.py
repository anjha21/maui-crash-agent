from __future__ import annotations
import asyncio
from datetime import date
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from agent.core.executor import PhaseExecutor
from agent.core.planner import Planner
from agent.integrations.firebase import FirebaseClient
from agent.integrations.github import GitHubClient
from agent.integrations.jira import JiraClient
from agent.services.crash_analyzer import CrashAnalyzer
from agent.services.memory_service import MemoryService
from agent.services.report_service import ReportService
from agent.utils.logger import get_logger

console = Console()
log = get_logger(__name__)


class CrashAgent:
    def __init__(self, cfg, *, dry_run: bool = False) -> None:
        self.cfg = cfg
        self.dry_run = dry_run
        self.firebase = FirebaseClient(cfg.firebase)
        self.jira = JiraClient(cfg.jira)
        self.github = GitHubClient(cfg.github)
        self.memory = MemoryService(cfg.memory_file)
        self.analyzer = CrashAnalyzer(cfg.claude)
        self.reporter = ReportService(cfg.reports_dir)
        self.planner = Planner(cfg)
        self.executor = PhaseExecutor(cfg=cfg, firebase=self.firebase, jira=self.jira, github=self.github, memory=self.memory, analyzer=self.analyzer, reporter=self.reporter, dry_run=dry_run)

    async def run_full_pipeline(self) -> None:
        console.rule("[bold cyan].NET MAUI Crash Agent[/]")
        phases = self.planner.full_pipeline_phases()
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            for phase in phases:
                task = progress.add_task(f"Phase {phase.number}: {phase.name} …", total=None)
                try:
                    await self.executor.run_phase(phase)
                    progress.update(task, description=f"[green]✓[/] Phase {phase.number}: {phase.name}")
                except Exception as e:
                    progress.update(task, description=f"[red]✗[/] Phase {phase.number}: {phase.name} — {e}")
                    if phase.required:
                        raise
                finally:
                    progress.remove_task(task)
        console.rule("[bold green]Pipeline complete[/]")

    async def fetch_crashes(self) -> list:
        return await self.firebase.get_top_crashes(lookback_days=self.cfg.firebase.lookback_days, limit=self.cfg.firebase.max_crashes)

    async def analyze_crashes(self, crashes: list) -> list:
        sem = asyncio.Semaphore(self.cfg.claude.max_concurrent_analyses)
        async def _one(crash):
            async with sem:
                return await self.analyzer.analyze(crash)
        return await asyncio.gather(*[_one(c) for c in crashes])

    async def generate_report_only(self) -> None:
        await self.reporter.generate(self.memory.get_all(), date.today())
