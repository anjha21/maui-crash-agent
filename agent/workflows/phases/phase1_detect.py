from __future__ import annotations
import re
from pathlib import Path
from typing import TYPE_CHECKING
from agent.utils.logger import get_logger

if TYPE_CHECKING:
    from agent.core.executor import PhaseExecutor

log = get_logger(__name__)


async def run(executor: "PhaseExecutor") -> None:
    project_root = executor.state.get("project_root", Path("."))
    project_map = {"viewmodels": {}, "views": {}, "services": {}, "di_registrations": [], "maui_program": None, "app_shell": None}
    cs_files = list(project_root.rglob("*.cs"))
    for f in cs_files:
        name, rel = f.stem, str(f.relative_to(project_root))
        if "ViewModel" in name:
            project_map["viewmodels"][name] = rel
        elif "Page" in name or "View" in name:
            project_map["views"][name] = rel
        elif "Service" in name or "Repository" in name:
            project_map["services"][name] = rel
        if "MauiProgram" in name:
            project_map["maui_program"] = rel
            pattern = re.compile(r"builder\.Services\.(AddTransient|AddSingleton|AddScoped)(?:<([^>]+)>)?", re.MULTILINE)
            try:
                project_map["di_registrations"] = [m.group(0) for m in pattern.finditer(f.read_text(encoding="utf-8", errors="ignore"))]
            except Exception:
                pass
        if "AppShell" in name:
            project_map["app_shell"] = rel
    log.info("Project map: %d ViewModels, %d Services, %d DI registrations", len(project_map["viewmodels"]), len(project_map["services"]), len(project_map["di_registrations"]))
    executor.state["project_map"] = project_map
