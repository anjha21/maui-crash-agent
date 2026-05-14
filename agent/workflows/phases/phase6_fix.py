from __future__ import annotations
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
import anthropic
from agent.prompts.analyze_prompt import build_fix_prompt
from agent.prompts.system_prompt import SYSTEM_PROMPT
from agent.utils.logger import get_logger

if TYPE_CHECKING:
    from agent.core.executor import PhaseExecutor

log = get_logger(__name__)


async def run(executor: "PhaseExecutor") -> None:
    project_root = executor.state.get("project_root", Path("."))
    for item in executor.state.get("analyses", []):
        analysis = item.get("analysis")
        if not analysis or not analysis.files_to_change:
            continue
        item["fixed_files"] = []
        item["build_passed"] = False
        for file_path_rel in analysis.files_to_change:
            file_path = project_root / file_path_rel
            if not file_path.exists():
                continue
            current = file_path.read_text(encoding="utf-8", errors="replace")
            fixed = await _get_fix(executor, analysis.raw, current, str(file_path))
            if not fixed or fixed.strip() == current.strip():
                continue
            file_path.write_text(fixed, encoding="utf-8")
            item["fixed_files"].append(file_path_rel)
        if item["fixed_files"]:
            result = subprocess.run(["dotnet", "build", "--no-restore", "-v", "minimal"], cwd=project_root, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                item["build_passed"] = True
            else:
                log.error("Build failed — reverting")
                for f in item["fixed_files"]:
                    subprocess.run(["git", "checkout", "--", f], cwd=project_root, capture_output=True)
                item["fixed_files"] = []


async def _get_fix(executor, analysis: dict, content: str, path: str) -> str:
    import re
    client = anthropic.AsyncAnthropic(api_key=executor.cfg.claude.api_key)
    response = await client.messages.create(model=executor.cfg.claude.model, max_tokens=executor.cfg.claude.max_tokens, system=SYSTEM_PROMPT, messages=[{"role": "user", "content": build_fix_prompt(analysis, content, path)}])
    text = "".join(block.text for block in response.content if hasattr(block, "text"))
    match = re.search(r"```(?:csharp|cs)?\s*([\s\S]+?)\s*```", text)
    return match.group(1) if match else text
