from __future__ import annotations
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING
import httpx
from agent.utils.logger import get_logger
from agent.utils.retry import with_retry

if TYPE_CHECKING:
    from config import FirebaseConfig

log = get_logger(__name__)


class CrashEvent:
    def __init__(self, raw: dict) -> None:
        self.raw = raw
        self.exception_type: str = raw.get("exceptionType", "UnknownException")
        self.message: str = raw.get("exceptionMessage", "")
        self.stack_trace: str = raw.get("stackTrace", "")
        self.platform: str = raw.get("platform", "unknown")
        self.occurrence_count: int = raw.get("occurrenceCount", 0)
        self.affected_users: int = raw.get("affectedUsers", 0)
        self.app_version: str = raw.get("appVersion", "")
        self.os_version: str = raw.get("osVersion", "")
        self.first_seen: str = raw.get("firstSeen", "")
        self.last_seen: str = raw.get("lastSeen", "")
        self.issue_id: str = raw.get("issueId", "")


class FirebaseClient:
    def __init__(self, cfg: "FirebaseConfig") -> None:
        self.cfg = cfg
        self._token: str | None = None
        self._http = httpx.AsyncClient(timeout=30)

    async def get_top_crashes(self, lookback_days: int = 7, limit: int = 10, platform: str = "all") -> list[CrashEvent]:
        if not self.cfg.service_account_path:
            log.warning("No service account — returning mock crashes")
            return self._mock_crashes(limit)
        await self._ensure_token()
        end = datetime.now(tz=timezone.utc)
        start = end - timedelta(days=lookback_days)
        url = f"https://firebasecrashlytics.googleapis.com/v1alpha/projects/{self.cfg.project_id}/apps/{self.cfg.app_id}/issues"
        params = {"pageSize": limit, "orderBy": "eventCount desc", "filter": f"firstSeen > '{start.isoformat()}' AND type = 'crash'"}
        try:
            resp = await with_retry(lambda: self._http.get(url, params=params, headers={"Authorization": f"Bearer {self._token}"}))
            resp.raise_for_status()
            issues = resp.json().get("issues", [])
            events = [CrashEvent(self._normalize(i)) for i in issues]
            if platform != "all":
                events = [e for e in events if e.platform == platform]
            return events[:limit]
        except httpx.HTTPStatusError as e:
            log.error("Firebase API error %d: %s", e.response.status_code, e.response.text)
            raise

    async def _ensure_token(self) -> None:
        if self._token:
            return
        sa_path = Path(self.cfg.service_account_path)
        if not sa_path.exists():
            raise FileNotFoundError(f"Service account file not found: {sa_path}")
        sa_data = json.loads(sa_path.read_text())
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        creds = service_account.Credentials.from_service_account_info(sa_data, scopes=["https://www.googleapis.com/auth/firebase.readonly", "https://www.googleapis.com/auth/cloud-platform"])
        creds.refresh(Request())
        self._token = creds.token

    @staticmethod
    def _normalize(issue: dict) -> dict:
        return {"issueId": issue.get("name", "").split("/")[-1], "exceptionType": issue.get("subtitle", "").split(":")[0], "exceptionMessage": issue.get("subtitle", ""), "stackTrace": issue.get("stackTrace", {}).get("frames", []), "platform": issue.get("platform", "").lower(), "occurrenceCount": issue.get("eventCount", 0), "affectedUsers": issue.get("userCount", 0), "appVersion": issue.get("appVersion", ""), "osVersion": "", "firstSeen": issue.get("firstSeenTime", ""), "lastSeen": issue.get("lastSeenTime", "")}

    @staticmethod
    def _mock_crashes(limit: int) -> list[CrashEvent]:
        return [CrashEvent(d) for d in [
            {"issueId": "mock_001", "exceptionType": "System.NullReferenceException", "exceptionMessage": "Object reference not set to an instance of an object.", "stackTrace": "System.NullReferenceException: Object reference not set to an instance of an object.\n   at MyApp.ViewModels.HomeViewModel.LoadDataAsync()\n      in /src/ViewModels/HomeViewModel.cs:line 42", "platform": "android", "occurrenceCount": 1234, "affectedUsers": 892, "appVersion": "2.1.0", "osVersion": "Android 13", "firstSeen": "2025-04-10", "lastSeen": "2025-04-17"},
            {"issueId": "mock_002", "exceptionType": "System.InvalidOperationException", "exceptionMessage": "Unable to resolve service for type 'IBookingService'.", "stackTrace": "System.InvalidOperationException: Unable to resolve service...\n   at MyApp.ViewModels.BookingViewModel..ctor(IBookingService service)\n      in /src/ViewModels/BookingViewModel.cs:line 24", "platform": "ios", "occurrenceCount": 456, "affectedUsers": 231, "appVersion": "2.1.0", "osVersion": "iOS 17.2", "firstSeen": "2025-04-12", "lastSeen": "2025-04-17"},
        ][:limit]]
