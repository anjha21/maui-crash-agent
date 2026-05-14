---
name: maui-crash-agent
description: >
  Full-cycle crash analysis agent for .NET MAUI apps. Fetches crashes from
  AppCenter or Firebase Crashlytics, checks memory for recurring issues,
  creates Jira tickets, fixes C# code, runs code review, and raises GitHub PRs.
  Use when asked to analyze crashes, triage production issues, fix bugs from
  crash reports, or automate the crash → ticket → fix → PR workflow.
---

# .NET MAUI Crash Agent

Full-cycle automated crash handling: detect → memory check → analyze → Jira ticket → fix → review → PR.

## When to Use

- "Analyze our crashes"
- "Check Crashlytics and fix any issues"
- "Create Jira tickets for our top crashes"
- "Run the crash agent"
- Any mention of AppCenter, Crashlytics, MAUI crashes, production exceptions

## Commands

### `/crash-report`
Full automated pipeline:
1. Fetch crashes from AppCenter/Firebase
2. Check crash-memory.json for recurring issues
3. Analyze C# stack traces, find root causes
4. Create Jira tickets (linked if recurring)
5. Fix code in codebase
6. Self-review the fix
7. Raise GitHub PR
8. Update crash-memory.json

## Requirements

- .NET MAUI project with AppCenter Crashes or Firebase Crashlytics
- Git repository with GitHub remote
- Jira project
- MCP servers configured in .mcp.json
- crash-memory.json in project root

## Severity Score (0-100)

- Crash frequency: 40%
- Affected users: 30%
- Pattern criticality: 30%

## Memory System

crash-memory.json tracks every crash ever seen:
- Signature (exception type + class + method + line)
- Root cause and applied fix
- Jira ticket ID and PR link
- Recurrence count

Recurring crashes get flagged, previous fix is retrieved, and Jira ticket is linked to the original.
