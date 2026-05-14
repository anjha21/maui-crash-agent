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
    for item in executor.state.get("analyses", []):
        if not item.get("fixed_files"):
            continue
        analysis = item.get("analysis")
        results = {"build_passed": item.get("build_passed", False), "root_cause_addressed": analysis is not None and bool(analysis.root_cause), "di_updated": True}
        for f in item.get("fixed_files", []):
            fp = project_root / f
            if fp.exists():
                content = fp.read_text(encoding="utf-8", errors="replace")
                results["no_null_forgiving"] = not bool(re.compile(r'\w+![\s;,\)\.]').search(content))
                ios = content.count("#if IOS") + content.count("#if __IOS__")
                android = content.count("#if ANDROID") + content.count("#if __ANDROID__")
                results["platform_safe"] = content.count("#endif") >= ios + android
        if analysis and "di" in (analysis.pattern or ""):
            results["di_updated"] = any("MauiProgram" in f for f in item.get("fixed_files", []))
        failed = [desc for key, desc in [("root_cause_addressed", "Fix addresses root cause"), ("no_null_forgiving", "No unjustified ! operators"), ("platform_safe", "Platform-safe (#if guards balanced)"), ("di_updated", "MauiProgram.cs updated for DI"), ("build_passed", "dotnet build passes")] if not results.get(key, True)]
        item["review_results"] = results
        item["review_failed"] = failed
        if failed:
            log.warning("⚠️  Review flagged %d issue(s): %s", len(failed), ", ".join(failed))
        else:
            log.info("✅ Review passed for %s", item["signature"])
