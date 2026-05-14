from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from agent.utils.logger import get_logger
from agent.utils.signature import signatures_match, MATCH_EXACT, MATCH_LIKELY

log = get_logger(__name__)


class MemoryEntry:
    def __init__(self, data: dict) -> None:
        self.id = data["id"]
        self.signature = data["signature"]
        self.exception_type = data.get("exceptionType", "")
        self.crash_class = data.get("crashClass", "")
        self.crash_method = data.get("crashMethod", "")
        self.crash_line = data.get("crashLine", 0)
        self.platform = data.get("platform", "")
        self.pattern = data.get("pattern", "")
        self.first_seen = data.get("firstSeen", "")
        self.last_seen = data.get("lastSeen", "")
        self.occurrence_count = data.get("occurrenceCount", 0)
        self.recurrence_count = data.get("recurrenceCount", 1)
        self.status = data.get("status", "new")
        self.severity_score = data.get("severityScore", 0)
        self.priority = data.get("priority", "P3")
        self.root_cause = data.get("rootCause", "")
        self.fix = data.get("fix", "")
        self.files_changed = data.get("filesChanged", [])
        self.jira_ticket = data.get("jiraTicket", "")
        self.jira_url = data.get("jiraUrl", "")
        self.pr_url = data.get("prUrl", "")
        self.pr_branch = data.get("prBranch", "")
        self.assigned_developer = data.get("assignedDeveloper", "")
        self.crash_name = data.get("crashName", "")
        self.app_version = data.get("appVersion", "")
        self.individual_report = data.get("individualReport", "")
        self._raw = data

    def to_dict(self) -> dict:
        return self._raw


class MemoryService:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._data = self._load()

    def _load(self) -> dict:
        if not self._path.exists():
            return {"version": "1.0", "lastUpdated": None, "crashes": []}
        with self._path.open(encoding="utf-8") as f:
            return json.load(f)

    def _save(self) -> None:
        self._data["lastUpdated"] = datetime.now(tz=timezone.utc).isoformat()
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def get_all(self) -> list[MemoryEntry]:
        return [MemoryEntry(c) for c in self._data.get("crashes", [])]

    def check(self, signature: str) -> tuple:
        for crash in self._data.get("crashes", []):
            match = signatures_match(signature, crash["signature"])
            if match == MATCH_EXACT:
                return MATCH_EXACT, MemoryEntry(crash)
            if match == MATCH_LIKELY:
                return MATCH_LIKELY, MemoryEntry(crash)
        return "none", None

    def upsert(self, entry: dict) -> None:
        crashes = self._data.setdefault("crashes", [])
        idx = next((i for i, c in enumerate(crashes) if c.get("id") == entry.get("id")), None)
        if idx is not None:
            crashes[idx] = entry
        else:
            crashes.append(entry)
        self._save()

    def next_id(self) -> str:
        return f"crash_{len(self._data.get('crashes', [])) + 1:03d}"
