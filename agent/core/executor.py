from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING, Any
from agent.utils.logger import get_logger

if TYPE_CHECKING:
    from config import AgentConfig
    from agent.core.planner import Phase
    from agent.integrations.firebase import FirebaseClient
    from agent.integrations.jira import JiraClient
    from agent.integrations.github import GitHubClient
    from agent.services.crash_analyzer import CrashAnalyzer
    from agent.services.memory_service import MemoryService
    from agent.services.report_service import ReportService

log = get_logger(__name__)


class PhaseExecutor:
    def __init__(self, cfg, firebase, jira, github, memory, analyzer, reporter, dry_run=False):
        self.cfg = cfg
        self.firebase = firebase
        self.jira = jira
        self.github = github
        self.memory = memory
        self.analyzer = analyzer
        self.reporter = reporter
        self.dry_run = dry_run
        self.state: dict[str, Any] = {}
        self.results: dict[str, Any] = {"analyzed": 0, "new": 0, "recurring": 0, "tickets_created": 0, "prs_raised": 0, "report_path": None}

    async def run_phase(self, phase: "Phase") -> None:
        handler = getattr(self, phase.handler, None)
        if handler is None:
            raise NotImplementedError(f"No handler for phase: {phase.handler}")
        await handler()

    async def phase0_validate(self): from agent.workflows.phases.phase0_validate import run; await run(self)
    async def phase1_detect_project(self): from agent.workflows.phases.phase1_detect import run; await run(self)
    async def phase2_fetch_crashes(self): from agent.workflows.phases.phase2_fetch import run; await run(self)
    async def phase3_memory_check(self): from agent.workflows.phases.phase3_memory import run; await run(self)
    async def phase4_analyze(self): from agent.workflows.phases.phase4_analyze import run; await run(self)
    async def phase5_create_tickets(self):
        if self.dry_run: return
        from agent.workflows.phases.phase5_ticket import run; await run(self)
    async def phase6_fix_code(self):
        if self.dry_run: return
        from agent.workflows.phases.phase6_fix import run; await run(self)
    async def phase7_self_review(self): from agent.workflows.phases.phase7_review import run; await run(self)
    async def phase8_raise_prs(self):
        if self.dry_run: return
        from agent.workflows.phases.phase8_pr import run; await run(self)
    async def phase9_update_memory(self): from agent.workflows.phases.phase9_memory import run; await run(self)
    async def phase10_generate_report(self): from agent.workflows.phases.phase10_report import run; await run(self)
