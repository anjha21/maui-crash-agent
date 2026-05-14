from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import AgentConfig


@dataclass
class Phase:
    number: int
    name: str
    handler: str
    required: bool = True


class Planner:
    def __init__(self, cfg: "AgentConfig") -> None:
        self.cfg = cfg

    def full_pipeline_phases(self) -> list[Phase]:
        return [
            Phase(0,  "Validate Setup",       "phase0_validate"),
            Phase(1,  "Detect Project",        "phase1_detect_project"),
            Phase(2,  "Fetch Crashes",         "phase2_fetch_crashes"),
            Phase(3,  "Memory Check",          "phase3_memory_check"),
            Phase(4,  "Deep Analysis",         "phase4_analyze",        required=False),
            Phase(5,  "Create Jira Tickets",   "phase5_create_tickets", required=False),
            Phase(6,  "Fix Code",              "phase6_fix_code",       required=False),
            Phase(7,  "Self Code Review",      "phase7_self_review",    required=False),
            Phase(8,  "Raise GitHub PRs",      "phase8_raise_prs",      required=False),
            Phase(9,  "Update Memory",         "phase9_update_memory"),
            Phase(10, "Generate Report",       "phase10_generate_report"),
        ]
