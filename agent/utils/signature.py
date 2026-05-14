from __future__ import annotations
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.integrations.firebase import CrashEvent

MATCH_EXACT = "exact"
MATCH_LIKELY = "likely"
MATCH_NONE = "none"
LINE_TOLERANCE = 5
SYSTEM_PREFIXES = ("System.", "Microsoft.", "Xamarin.", "Java.", "Android.", "Mono.", "mscorlib.", "netstandard.", "CommunityToolkit.")


def build_signature(crash: "CrashEvent") -> str:
    exc_type = crash.exception_type.split(".")[-1]
    frame = _find_app_frame(crash.stack_trace)
    if frame is None:
        return f"{exc_type}::unknown::0"
    return f"{exc_type}::{frame[0]}.{frame[1]}::{frame[2]}"


def signatures_match(sig_a: str, sig_b: str) -> str:
    if sig_a == sig_b:
        return MATCH_EXACT
    parts_a, parts_b = sig_a.split("::"), sig_b.split("::")
    if len(parts_a) != 3 or len(parts_b) != 3:
        return MATCH_NONE
    exc_a, loc_a, line_a = parts_a
    exc_b, loc_b, line_b = parts_b
    if exc_a != exc_b or loc_a != loc_b:
        return MATCH_NONE
    try:
        if abs(int(line_a) - int(line_b)) <= LINE_TOLERANCE:
            return MATCH_LIKELY
    except ValueError:
        pass
    return MATCH_NONE


def _find_app_frame(stack_trace: str):
    pattern = re.compile(r"at\s+([\w.]+)\.([\w<>]+)\([^)]*\)(?:\s+in\s+[^\n:]+:line\s+(\d+))?", re.MULTILINE)
    for m in pattern.finditer(stack_trace):
        full_class, method, line = m.group(1), m.group(2), int(m.group(3) or 0)
        if any(full_class.startswith(p) for p in SYSTEM_PREFIXES):
            continue
        return (full_class.split(".")[-1], method, line)
    return None
