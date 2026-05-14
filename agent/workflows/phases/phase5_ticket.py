from __future__ import annotations
from typing import TYPE_CHECKING
from agent.utils.logger import get_logger

if TYPE_CHECKING:
    from agent.core.executor import PhaseExecutor

log = get_logger(__name__)
PRIORITY_MAP = {"P0": "Critical", "P1": "High", "P2": "Medium", "P3": "Low"}


async def run(executor: "PhaseExecutor") -> None:
    for item in executor.state.get("analyses", []):
        crash, analysis, memory_entry, crash_type = item["crash"], item.get("analysis"), item.get("memory_entry"), item["type"]
        try:
            if crash_type == "new" and analysis:
                result = await executor.jira.create_ticket(summary=f"[CRASH][{analysis.priority}] {crash.exception_type} — {crash.platform}", description=f"**Root Cause:** {analysis.root_cause}\n\n**Fix:** {analysis.fix_summary}\n\n**Occurrences:** {crash.occurrence_count} | **Users:** {crash.affected_users}", priority=PRIORITY_MAP.get(analysis.priority, "Medium"), labels=["crash", "auto-detected", "maui", crash.platform], assignee_email=analysis.assigned_developer_email or None)
                item["jira_ticket"] = result["key"]
                item["jira_url"] = result["url"]
                executor.results["tickets_created"] += 1
                log.info("Created ticket: %s", result["key"])
            elif crash_type == "regression":
                parent = memory_entry.jira_ticket if memory_entry else None
                result = await executor.jira.create_ticket(summary=f"[REGRESSION] {crash.exception_type} — previously fixed in {parent or 'unknown'}", description=f"Regression of {parent}. Fix was merged but crash reappeared.", priority="Critical", labels=["crash", "regression", "maui"], parent_ticket=parent)
                item["jira_ticket"] = result["key"]
                item["jira_url"] = result["url"]
                executor.results["tickets_created"] += 1
            elif crash_type in ("recurring", "likely_recurring") and memory_entry and memory_entry.jira_ticket:
                await executor.jira.add_comment(memory_entry.jira_ticket, f"Still occurring — {crash.occurrence_count} events, {crash.affected_users} users as of {crash.last_seen}.")
                item["jira_ticket"] = memory_entry.jira_ticket
                item["jira_url"] = memory_entry.jira_url
        except Exception as e:
            log.error("Jira failed for %s: %s", item["signature"], e)
