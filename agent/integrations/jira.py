from __future__ import annotations
import base64
from typing import TYPE_CHECKING, Any
import httpx
from agent.utils.logger import get_logger
from agent.utils.retry import with_retry

if TYPE_CHECKING:
    from config import JiraConfig

log = get_logger(__name__)
PRIORITY_MAP = {"Critical": "Highest", "High": "High", "Medium": "Medium", "Low": "Low"}


class JiraClient:
    def __init__(self, cfg: "JiraConfig") -> None:
        self.cfg = cfg
        token = base64.b64encode(f"{cfg.email}:{cfg.api_token}".encode()).decode()
        self._http = httpx.AsyncClient(base_url=f"{cfg.host}/rest/api/3", headers={"Authorization": f"Basic {token}", "Accept": "application/json", "Content-Type": "application/json"}, timeout=30)

    async def create_ticket(self, summary, description, priority, labels=None, assignee_email=None, parent_ticket=None) -> dict:
        body: dict[str, Any] = {"fields": {"project": {"key": self.cfg.project_key}, "summary": summary, "description": self._to_adf(description), "issuetype": {"name": self.cfg.issue_type}, "priority": {"name": PRIORITY_MAP.get(priority, "Medium")}, "labels": labels or ["crash", "auto-detected"]}}
        if assignee_email:
            account_id = await self._resolve_account_id(assignee_email)
            if account_id:
                body["fields"]["assignee"] = {"accountId": account_id}
        resp = await with_retry(lambda: self._http.post("/issue", json=body))
        resp.raise_for_status()
        data = resp.json()
        ticket_id = data["key"]
        if parent_ticket:
            await self._link_tickets(ticket_id, parent_ticket)
        return {"id": data["id"], "key": ticket_id, "url": f"{self.cfg.host}/browse/{ticket_id}"}

    async def add_comment(self, ticket_id: str, comment: str) -> None:
        resp = await with_retry(lambda: self._http.post(f"/issue/{ticket_id}/comment", json={"body": self._to_adf(comment)}))
        resp.raise_for_status()

    async def update_priority(self, ticket_id: str, priority: str) -> None:
        resp = await with_retry(lambda: self._http.put(f"/issue/{ticket_id}", json={"fields": {"priority": {"name": PRIORITY_MAP.get(priority, "Medium")}}}))
        resp.raise_for_status()

    async def _resolve_account_id(self, email: str) -> str | None:
        try:
            resp = await self._http.get("/user/search", params={"query": email})
            resp.raise_for_status()
            users = resp.json()
            return users[0]["accountId"] if users else None
        except Exception:
            return None

    async def _link_tickets(self, new_id: str, parent_id: str) -> None:
        try:
            resp = await self._http.post("/issueLink", json={"type": {"name": "Cloners"}, "inwardIssue": {"key": new_id}, "outwardIssue": {"key": parent_id}})
            resp.raise_for_status()
        except Exception as e:
            log.warning("Could not link tickets: %s", e)

    @staticmethod
    def _to_adf(text: str) -> dict:
        return {"version": 1, "type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}
