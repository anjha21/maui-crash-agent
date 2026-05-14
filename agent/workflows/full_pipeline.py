from __future__ import annotations
from typing import TYPE_CHECKING
from agent.core.planner import Planner

if TYPE_CHECKING:
    from agent.core.executor import PhaseExecutor
    from config import AgentConfig


async def run_full_pipeline(executor: "PhaseExecutor", cfg: "AgentConfig") -> dict:
    planner = Planner(cfg)
    for phase in planner.full_pipeline_phases():
        try:
            await executor.run_phase(phase)
        except Exception as e:
            if phase.required:
                raise RuntimeError(f"Required phase {phase.number} ({phase.name}) failed: {e}") from e
    return executor.results
