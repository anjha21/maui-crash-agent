from __future__ import annotations
from datetime import date
from typing import TYPE_CHECKING
from agent.utils.logger import get_logger

if TYPE_CHECKING:
    from agent.core.executor import PhaseExecutor

log = get_logger(__name__)


async def run(executor: "PhaseExecutor") -> None:
    analyses = executor.state.get("analyses", [])
    if not analyses:
        return
    today = date.today().isoformat()
    for item in analyses:
        crash, analysis, memory_entry = item["crash"], item.get("analysis"), item.get("memory_entry")
        crash_id = memory_entry.id if memory_entry else executor.memory.next_id()
        sig_parts = item["signature"].split("::")
        status = "regression" if item.get("type") == "regression" else ("pr_raised" if item.get("pr_url") else ("fix_applied" if item.get("fixed_files") else ("ticket_created" if item.get("jira_ticket") else "analyzed")))
        executor.memory.upsert({"id": crash_id, "signature": item["signature"], "exceptionType": crash.exception_type, "crashClass": sig_parts[1].split(".")[0] if len(sig_parts) > 1 else "", "crashMethod": sig_parts[1].split(".", 1)[1] if len(sig_parts) > 1 and "." in sig_parts[1] else "", "crashLine": int(sig_parts[2]) if len(sig_parts) > 2 and sig_parts[2].isdigit() else 0, "platform": crash.platform, "pattern": getattr(analysis, "pattern", memory_entry.pattern if memory_entry else "") if analysis else (memory_entry.pattern if memory_entry else ""), "firstSeen": memory_entry.first_seen if memory_entry else today, "lastSeen": today, "occurrenceCount": crash.occurrence_count, "recurrenceCount": (memory_entry.recurrence_count + 1) if memory_entry else 1, "status": status, "severityScore": getattr(analysis, "severity_score", memory_entry.severity_score if memory_entry else 0) if analysis else (memory_entry.severity_score if memory_entry else 0), "priority": getattr(analysis, "priority", memory_entry.priority if memory_entry else "P3") if analysis else (memory_entry.priority if memory_entry else "P3"), "rootCause": getattr(analysis, "root_cause", memory_entry.root_cause if memory_entry else "") if analysis else (memory_entry.root_cause if memory_entry else ""), "fix": getattr(analysis, "fix_summary", memory_entry.fix if memory_entry else "") if analysis else (memory_entry.fix if memory_entry else ""), "filesChanged": item.get("fixed_files", []), "jiraTicket": item.get("jira_ticket", ""), "jiraUrl": item.get("jira_url", ""), "prUrl": item.get("pr_url", ""), "prBranch": item.get("pr_branch", ""), "crashName": item.get("crash_name", ""), "appVersion": crash.app_version, "individualReport": item.get("individual_report", ""), "assignedDeveloper": getattr(analysis, "assigned_developer", "") if analysis else "", "commitHash": ""})
    log.info("Memory updated: %d entries", len(analyses))
