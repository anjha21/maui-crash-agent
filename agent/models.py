from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class CrashEventModel(BaseModel):
    issue_id: str
    exception_type: str
    message: str
    stack_trace: str
    platform: str
    occurrence_count: int = 0
    affected_users: int = 0
    app_version: str = ""
    os_version: str = ""
    first_seen: str = ""
    last_seen: str = ""


class AnalysisResultModel(BaseModel):
    exception_type: str
    pattern: str
    root_cause: str
    fix_summary: str
    fix_code_before: str = ""
    fix_code_after: str = ""
    files_to_change: list[str] = Field(default_factory=list)
    severity_score: int = Field(ge=0, le=100)
    priority: str = "P3"
    assigned_developer: str = ""
    assigned_developer_email: str = ""
    platform: str = "cross-platform"
    is_recurring: bool = False


class JiraTicketModel(BaseModel):
    key: str
    url: str
    id: str


class PullRequestModel(BaseModel):
    number: int
    url: str
    branch: str


class PipelineItemModel(BaseModel):
    crash: CrashEventModel
    signature: str
    type: str
    memory_entry: Optional[dict] = None
    analysis: Optional[AnalysisResultModel] = None
    from_memory: bool = False
    analysis_error: Optional[str] = None
    fixed_files: list[str] = Field(default_factory=list)
    build_passed: bool = False
    review_results: dict = Field(default_factory=dict)
    review_failed: list[str] = Field(default_factory=list)
    jira_ticket: str = ""
    jira_url: str = ""
    pr_url: str = ""
    pr_branch: str = ""
    pr_number: Optional[int] = None
