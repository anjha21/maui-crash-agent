from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT_DIR = Path(__file__).parent
MEMORY_FILE = ROOT_DIR / "crash-memory.json"
REPORTS_DIR = ROOT_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


@dataclass
class FirebaseConfig:
    project_id: str = field(default_factory=lambda: os.environ.get("FIREBASE_PROJECT_ID", ""))
    service_account_path: str = field(default_factory=lambda: os.environ.get("FIREBASE_SERVICE_ACCOUNT", ""))
    app_id: str = field(default_factory=lambda: os.environ.get("FIREBASE_APP_ID", ""))
    lookback_days: int = 7
    max_crashes: int = 10


@dataclass
class JiraConfig:
    host: str = field(default_factory=lambda: os.environ["JIRA_HOST"])
    email: str = field(default_factory=lambda: os.environ["JIRA_EMAIL"])
    api_token: str = field(default_factory=lambda: os.environ["JIRA_API_TOKEN"])
    project_key: str = field(default_factory=lambda: os.environ["JIRA_PROJECT_KEY"])
    issue_type: str = "Bug"


@dataclass
class GitHubConfig:
    token: str = field(default_factory=lambda: os.environ["GITHUB_TOKEN"])
    owner: str = field(default_factory=lambda: os.environ["GITHUB_OWNER"])
    repo: str = field(default_factory=lambda: os.environ["GITHUB_REPO"])
    default_branch: str = field(default_factory=lambda: os.environ.get("GITHUB_DEFAULT_BRANCH", "main"))


@dataclass
class ClaudeConfig:
    api_key: str = field(default_factory=lambda: os.environ["ANTHROPIC_API_KEY"])
    model: str = field(default_factory=lambda: os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6"))
    max_tokens: int = 8192
    max_concurrent_analyses: int = 5


@dataclass
class AgentConfig:
    firebase: FirebaseConfig = field(default_factory=FirebaseConfig)
    jira: JiraConfig = field(default_factory=JiraConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)
    claude: ClaudeConfig = field(default_factory=ClaudeConfig)
    memory_file: Path = MEMORY_FILE
    reports_dir: Path = REPORTS_DIR
    p0_threshold: int = 80
    p1_threshold: int = 60
    p2_threshold: int = 40
    max_retries: int = 3
    retry_base_delay: float = 1.0
    batch_size: int = 5
    batch_delay_seconds: float = 2.0


def load_config() -> AgentConfig:
    try:
        return AgentConfig()
    except KeyError as e:
        missing = str(e).strip("'")
        raise EnvironmentError(
            f"Required environment variable missing: {missing}\nCopy .env.example to .env and fill in the values."
        ) from None
