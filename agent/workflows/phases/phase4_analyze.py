from __future__ import annotations
import asyncio
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING
from agent.utils.logger import get_logger

if TYPE_CHECKING:
    from agent.core.executor import PhaseExecutor

log = get_logger(__name__)


async def run(executor: "PhaseExecutor") -> None:
    classified = executor.state.get("classified_crashes", [])
    if not classified:
        return
    reports_dir = executor.cfg.reports_dir
    reports_dir.mkdir(exist_ok=True)
    sem = asyncio.Semaphore(executor.cfg.claude.max_concurrent_analyses)
    analyses = []

    async def analyze_one(item: dict) -> dict:
        async with sem:
            crash = item["crash"]
            memory_entry = item.get("memory_entry")
            if item["type"] == "recurring" and memory_entry and memory_entry.fix:
                log.info("↻ RECURRING: loaded from memory")
                return {**item, "analysis": None, "from_memory": True, "crash_name": f"{memory_entry.pattern} - {memory_entry.crash_class}"}
            try:
                analysis = await executor.analyzer.analyze(crash, memory_entry.to_dict() if memory_entry else None)
                exc = crash.exception_type.split(".")[-1]
                version = ".".join(crash.app_version.split(".")[:3]) if crash.app_version else "?"
                crash_name = f"{exc} - v{version}"
                return {**item, "analysis": analysis, "from_memory": False, "crash_name": crash_name}
            except Exception as e:
                log.error("Analysis failed for %s: %s", item["signature"], e)
                return {**item, "analysis": None, "from_memory": False, "analysis_error": str(e), "crash_name": crash.exception_type.split(".")[-1]}

    for i in range(0, len(classified), executor.cfg.batch_size):
        batch = classified[i:i + executor.cfg.batch_size]
        results = await asyncio.gather(*[analyze_one(item) for item in batch])
        analyses.extend(results)
        if i + executor.cfg.batch_size < len(classified):
            await asyncio.sleep(executor.cfg.batch_delay_seconds)

    executor.state["analyses"] = analyses
    log.info("Analysis complete: %d/%d succeeded", sum(1 for a in analyses if a.get("analysis")), len(analyses))
