from __future__ import annotations
from typing import TYPE_CHECKING
from agent.utils.logger import get_logger
from agent.utils.signature import build_signature, MATCH_EXACT, MATCH_LIKELY

if TYPE_CHECKING:
    from agent.core.executor import PhaseExecutor

log = get_logger(__name__)


async def run(executor: "PhaseExecutor") -> None:
    raw_crashes = executor.state.get("raw_crashes", [])
    if not raw_crashes:
        return
    classified = []
    for crash in raw_crashes:
        sig = build_signature(crash)
        match_type, memory_entry = executor.memory.check(sig)
        if match_type == MATCH_EXACT:
            status = "regression" if (memory_entry and memory_entry.pr_url and memory_entry.status == "merged") else "recurring"
            classified.append({"crash": crash, "signature": sig, "type": status, "memory_entry": memory_entry})
            executor.results["recurring"] += 1
        elif match_type == MATCH_LIKELY:
            classified.append({"crash": crash, "signature": sig, "type": "likely_recurring", "memory_entry": memory_entry})
            executor.results["recurring"] += 1
        else:
            classified.append({"crash": crash, "signature": sig, "type": "new", "memory_entry": None})
            executor.results["new"] += 1
    executor.state["classified_crashes"] = classified
    log.info("Memory check: %d new, %d recurring", executor.results["new"], executor.results["recurring"])
