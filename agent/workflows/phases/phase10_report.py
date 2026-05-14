from __future__ import annotations
from datetime import date
from typing import TYPE_CHECKING
from agent.utils.logger import get_logger

if TYPE_CHECKING:
    from agent.core.executor import PhaseExecutor

log = get_logger(__name__)


async def run(executor: "PhaseExecutor") -> None:
    all_crashes = executor.memory.get_all()
    if not all_crashes:
        log.info("No crashes in memory — skipping report")
        return
    report_path = await executor.reporter.generate(all_crashes, date.today())
    executor.state["report_path"] = str(report_path)
    executor.results["report_path"] = str(report_path)
    log.info("Report ready: %s", report_path)
