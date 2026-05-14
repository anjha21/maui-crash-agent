---
description: >
  Full-cycle .NET MAUI crash agent: fetch crashes from AppCenter/Firebase,
  check memory for recurring issues, analyze C# stack traces, create Jira tickets,
  fix code, self-review, and raise GitHub PRs.
allowed-tools: Bash(git log:*), Bash(git blame:*), Bash(dotnet build:*), Bash(dotnet test:*)
---

# /crash-report — Full Pipeline

Runs all 10 phases of the MAUI crash agent. See `claude.md` for the full behavior contract.

## Usage

```
/crash-report
/crash-report --dry-run           # analyze only, no Jira/GitHub writes
/crash-report --phase analyze     # fetch + analyze only
/crash-report --max-crashes 5     # limit to 5 crashes
```

## Phases

| Phase | Action |
|-------|--------|
| 0 | Validate env vars, memory file, MAUI project |
| 1 | Detect ViewModels, Services, DI registrations |
| 2 | Fetch top crashes from Firebase/AppCenter |
| 3 | Check crash-memory.json for recurring issues |
| 4 | Analyze stack traces with Claude (concurrent, max 5) |
| 5 | Create Jira tickets (new / update recurring / regression) |
| 6 | Apply C# fixes, run dotnet build + test |
| 7 | Self-review: root cause, null safety, platform safety, DI |
| 8 | Create GitHub branch + PR with full description |
| 9 | Update crash-memory.json |
| 10 | Generate crash-report-YYYY-MM-DD.md |
