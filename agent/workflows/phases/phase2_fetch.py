from __future__ import annotations
from typing import TYPE_CHECKING
from agent.utils.logger import get_logger

if TYPE_CHECKING:
    from agent.core.executor import PhaseExecutor

log = get_logger(__name__)


async def run(executor: "PhaseExecutor") -> None:
    cfg = executor.cfg.firebase
    try:
        crashes = await executor.firebase.get_top_crashes(lookback_days=cfg.lookback_days, limit=cfg.max_crashes)
    except Exception as e:
        log.error("Firebase fetch failed: %s", e)
        executor.state["raw_crashes"] = []
        return
    if not crashes:
        log.info("No fatal crashes in the last %d days", cfg.lookback_days)
        executor.state["raw_crashes"] = []
        return
    log.info("Fetched %d crashes", len(crashes))
    executor.state["raw_crashes"] = crashes
    executor.results["analyzed"] = len(crashes)
