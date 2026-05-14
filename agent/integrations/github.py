from __future__ import annotations
import base64
from typing import TYPE_CHECKING, Any
import httpx
from agent.utils.logger import get_logger
from agent.utils.retry import with_retry

if TYPE_CHECKING:
    from config import GitHubConfig

log = get_logger(__name__)


class GitHubClient:
    def __init__(self, cfg: "GitHubConfig") -> None:
        self.cfg = cfg
        self._http = httpx.AsyncClient(base_url=f"https://api.github.com/repos/{cfg.owner}/{cfg.repo}", headers={"Authorization": f"Bearer {cfg.token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}, timeout=30)

    async def get_default_branch_sha(self) -> str:
        resp = await with_retry(lambda: self._http.get(f"/branches/{self.cfg.default_branch}"))
        resp.raise_for_status()
        return resp.json()["commit"]["sha"]

    async def create_branch(self, branch_name: str) -> str:
        sha = await self.get_default_branch_sha()
        resp = await with_retry(lambda: self._http.post("/git/refs", json={"ref": f"refs/heads/{branch_name}", "sha": sha}))
        if resp.status_code == 422:
            return sha
        resp.raise_for_status()
        return sha

    async def push_file(self, branch: str, file_path: str, content: str, commit_message: str) -> str:
        encoded = base64.b64encode(content.encode()).decode()
        existing_sha: str | None = None
        try:
            resp = await self._http.get(f"/contents/{file_path}", params={"ref": branch})
            if resp.status_code == 200:
                existing_sha = resp.json().get("sha")
        except Exception:
            pass
        body: dict[str, Any] = {"message": commit_message, "content": encoded, "branch": branch}
        if existing_sha:
            body["sha"] = existing_sha
        resp = await with_retry(lambda: self._http.put(f"/contents/{file_path}", json=body))
        resp.raise_for_status()
        return resp.json()["commit"]["sha"]

    async def create_pr(self, title: str, body: str, head_branch: str, reviewers=None, labels=None) -> dict:
        resp = await with_retry(lambda: self._http.post("/pulls", json={"title": title, "body": body, "head": head_branch, "base": self.cfg.default_branch}))
        resp.raise_for_status()
        pr = resp.json()
        if reviewers:
            try:
                await self._http.post(f"/pulls/{pr['number']}/requested_reviewers", json={"reviewers": reviewers})
            except Exception:
                pass
        return {"number": pr["number"], "url": pr["html_url"], "branch": head_branch}
