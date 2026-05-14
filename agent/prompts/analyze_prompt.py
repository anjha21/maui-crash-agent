from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.integrations.firebase import CrashEvent


def build_analysis_prompt(crash: "CrashEvent", memory_entry: dict | None = None) -> str:
    recurring_block = ""
    if memory_entry:
        recurring_block = f"""
## ⚠️ RECURRING CRASH
- Previous root cause: {memory_entry.get('rootCause', 'N/A')}
- Previous fix: {memory_entry.get('fix', 'N/A')}
- Previous Jira: {memory_entry.get('jiraTicket', 'N/A')}
- Previous PR: {memory_entry.get('prUrl', 'N/A')}
**If fix was merged but crash reappeared: classify as REGRESSION.**
"""
    return f"""\
Analyze the following .NET MAUI crash and produce a structured JSON response.

## Crash Details
- Exception: {crash.exception_type}
- Message: {crash.message}
- Platform: {crash.platform} / {crash.os_version}
- App version: {crash.app_version}
- Occurrences (last 7 days): {crash.occurrence_count}
- Affected users: {crash.affected_users}

## Stack Trace
```
{crash.stack_trace}
```
{recurring_block}
## Instructions
1. Use `read_source_file` to examine the crashing file (150 lines around crash).
2. Use `git_blame` on the crashing line to identify the responsible developer.
3. If DI involved, use `search_codebase` to check MauiProgram.cs.
4. Identify the MAUI crash pattern: null-reference, async-void, ui-thread-violation, handler-null, shell-navigation, di-resolution-failure, lifecycle-misuse, android-fragment, ios-memory-pressure, unhandled-task, unknown
5. Calculate severity score: frequency(40%) + user impact(30%) + pattern criticality(30%)
6. Map score: 80–100=P0, 60–79=P1, 40–59=P2, 0–39=P3
7. Return the JSON analysis.
"""


def build_fix_prompt(analysis: dict, file_content: str, file_path: str) -> str:
    return f"""\
Apply the fix for this .NET MAUI crash.

## Root Cause
{analysis.get('root_cause')}

## Pattern
{analysis.get('pattern')}

## File to Fix
Path: {file_path}

Current content:
```csharp
{file_content}
```

## Fix Required
{analysis.get('fix_summary')}

## Instructions
1. Apply the minimal fix that addresses the root cause.
2. Cover ALL null paths in the method.
3. Do NOT refactor unrelated code.
4. Return the complete fixed file content only (no explanation, no fences).
"""
