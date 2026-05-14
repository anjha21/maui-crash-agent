from __future__ import annotations
import os
from pathlib import Path
from typing import TYPE_CHECKING
from agent.utils.logger import get_logger

if TYPE_CHECKING:
    from agent.core.executor import PhaseExecutor

log = get_logger(__name__)
REQUIRED_ENV = ["ANTHROPIC_API_KEY", "JIRA_API_TOKEN", "GITHUB_TOKEN"]
OPTIONAL_ENV = ["FIREBASE_PROJECT_ID", "FIREBASE_SERVICE_ACCOUNT"]


async def run(executor: "PhaseExecutor") -> None:
    errors, warnings = [], []
    for var in REQUIRED_ENV:
        if not os.environ.get(var):
            errors.append(f"Missing required env var: {var}")
    for var in OPTIONAL_ENV:
        if not os.environ.get(var):
            warnings.append(f"Missing optional env var: {var} — will use mock data")
    memory_path = executor.cfg.memory_file
    if not memory_path.exists():
        memory_path.parent.mkdir(parents=True, exist_ok=True)
    maui_found = False
    for sln in Path(".").glob("**/*.sln"):
        for csproj in sln.parent.glob("**/*.csproj"):
            content = csproj.read_text(errors="ignore")
            if "<UseMaui>true</UseMaui>" in content or "net9.0-android" in content:
                maui_found = True
                executor.state["project_root"] = sln.parent
                executor.state["sln_path"] = sln
                break
        if maui_found:
            break
    if not maui_found:
        warnings.append("No MAUI project found — running without codebase context")
    for w in warnings:
        log.warning(w)
    if errors:
        for e in errors:
            log.error(e)
        raise EnvironmentError(f"Phase 0 failed with {len(errors)} error(s).")
    executor.state["validation_passed"] = True
