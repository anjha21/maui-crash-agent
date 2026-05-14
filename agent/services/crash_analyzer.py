from __future__ import annotations
import json, re, subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any
import anthropic
from agent.prompts.analyze_prompt import build_analysis_prompt
from agent.prompts.system_prompt import SYSTEM_PROMPT
from agent.utils.logger import get_logger
from agent.utils.retry import with_retry

if TYPE_CHECKING:
    from config import ClaudeConfig
    from agent.integrations.firebase import CrashEvent

log = get_logger(__name__)
MAUI_PATTERNS = {"NullReferenceException": "null-reference", "async void": "async-void", "CalledFromWrongThreadException": "ui-thread-violation", "Handler is null": "handler-null", "Unable to resolve service": "di-resolution-failure", "GoToAsync": "shell-navigation", "MemoryWarningException": "ios-memory-pressure", "Fragment already added": "android-fragment", "AggregateException": "unhandled-task"}


class AnalysisResult:
    def __init__(self, raw: dict) -> None:
        self.exception_type = raw.get("exception_type", "")
        self.pattern = raw.get("pattern", "unknown")
        self.root_cause = raw.get("root_cause", "")
        self.fix_summary = raw.get("fix_summary", "")
        self.fix_code_before = raw.get("fix_code_before", "")
        self.fix_code_after = raw.get("fix_code_after", "")
        self.files_to_change = raw.get("files_to_change", [])
        self.severity_score = raw.get("severity_score", 0)
        self.priority = raw.get("priority", "P3")
        self.assigned_developer = raw.get("assigned_developer", "")
        self.assigned_developer_email = raw.get("assigned_developer_email", "")
        self.platform = raw.get("platform", "cross-platform")
        self.is_recurring = raw.get("is_recurring", False)
        self.raw = raw


class CrashAnalyzer:
    def __init__(self, cfg: "ClaudeConfig") -> None:
        self.cfg = cfg
        self._client = anthropic.AsyncAnthropic(api_key=cfg.api_key)

    async def analyze(self, crash: "CrashEvent", memory_entry: dict | None = None) -> AnalysisResult:
        tools = self._build_tools()
        messages = [{"role": "user", "content": build_analysis_prompt(crash, memory_entry)}]
        for _ in range(5):
            response = await with_retry(lambda: self._client.messages.create(model=self.cfg.model, max_tokens=self.cfg.max_tokens, system=SYSTEM_PROMPT, tools=tools, messages=messages))
            if response.stop_reason == "end_turn":
                return self._parse_response(response, crash)
            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = self._execute_local_tool(block.name, block.input)
                        tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
        raise RuntimeError("Analysis did not complete in 5 tool-use rounds")

    def _build_tools(self) -> list[dict]:
        return [
            {"name": "read_source_file", "description": "Read a source file from the local MAUI codebase.", "input_schema": {"type": "object", "properties": {"file_path": {"type": "string"}, "start_line": {"type": "integer", "default": 1}, "num_lines": {"type": "integer", "default": 150}}, "required": ["file_path"]}},
            {"name": "git_blame", "description": "Run git blame on a file at a specific line.", "input_schema": {"type": "object", "properties": {"file_path": {"type": "string"}, "line_number": {"type": "integer"}}, "required": ["file_path", "line_number"]}},
            {"name": "search_codebase", "description": "Search the codebase for a class or method name.", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
        ]

    def _execute_local_tool(self, name: str, inputs: dict) -> str:
        try:
            if name == "read_source_file":
                p = Path(inputs["file_path"])
                if not p.exists():
                    return f"File not found: {inputs['file_path']}"
                lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
                start = inputs.get("start_line", 1)
                end = min(start - 1 + inputs.get("num_lines", 150), len(lines))
                return "\n".join(f"{start + i:4d} | {line}" for i, line in enumerate(lines[max(0, start - 1):end]))
            if name == "git_blame":
                result = subprocess.run(["git", "blame", "-L", f"{inputs['line_number']},{inputs['line_number']}", "--porcelain", inputs["file_path"]], capture_output=True, text=True, timeout=10)
                return result.stdout or result.stderr or "No blame output"
            if name == "search_codebase":
                result = subprocess.run(["grep", "-rn", "--include=*.cs", inputs["query"], "."], capture_output=True, text=True, timeout=15)
                return result.stdout[:3000] or "No matches found"
            return f"Unknown tool: {name}"
        except Exception as e:
            return f"Error: {e}"

    def _parse_response(self, response: Any, crash: "CrashEvent") -> AnalysisResult:
        text = "".join(block.text for block in response.content if hasattr(block, "text"))
        try:
            match = re.search(r"```json\s*([\s\S]+?)\s*```", text)
            raw = json.loads(match.group(1) if match else text)
        except (json.JSONDecodeError, AttributeError):
            raw = {"exception_type": crash.exception_type, "pattern": next((v for k, v in MAUI_PATTERNS.items() if k.lower() in crash.exception_type.lower() or k.lower() in crash.message.lower()), "unknown"), "root_cause": text[:500], "fix_summary": "See full analysis above", "severity_score": 30, "priority": "P2", "platform": crash.platform}
        return AnalysisResult(raw)
