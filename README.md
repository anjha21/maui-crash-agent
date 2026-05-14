# .NET MAUI Crash Agent

Full-cycle automated crash handling for .NET MAUI apps:
**Detect → Memory Check → Analyze → Jira Ticket → Fix Code → Self-Review → GitHub PR**

---

## What This Does

| Step | What Happens |
|------|-------------|
| 🔍 **Fetch** | Pulls top crashes from AppCenter or Firebase Crashlytics |
| 🧠 **Memory** | Checks `crash-memory.json` — is this a recurring crash? |
| 🔬 **Analyze** | Parses C# stack traces, finds root cause in your codebase |
| 🎫 **Jira** | Creates ticket with severity, root cause, fix summary, assignee |
| 🔧 **Fix** | Applies C# fix following MAUI best practices, runs `dotnet build` + `dotnet test` |
| 🔎 **Review** | Self-reviews the fix against a checklist before raising PR |
| 🚀 **PR** | Raises GitHub PR with full description, links Jira ticket |
| 💾 **Memory** | Updates `crash-memory.json` with fix, ticket, PR link |
| 📄 **Report** | Generates `crash-report-YYYY-MM-DD.md` |

---

## Install (User-Level — works across all your MAUI projects)

```bash
# Clone once into your Claude skills folder
git clone https://github.com/anjha21/maui-crash-agent ~/.claude/skills/crash-report

# Copy and fill in your credentials
cp ~/.claude/skills/crash-report/.env.example ~/.claude/skills/crash-report/.env
```

Then open `.env` and fill in your keys. Done — `/crash-report` now works in any MAUI project.

---

## Usage

```
/crash-report                    # full pipeline
/crash-report --dry-run          # analyze only, no Jira/GitHub writes
/crash-report --phase analyze    # fetch + analyze only
/crash-report --phase tickets    # create Jira tickets only
/crash-report --max-crashes 5   # limit to 5 crashes
/crash-report --force-full       # force full pipeline even for P2/P3
```

---

## Requirements

- .NET MAUI app with Firebase Crashlytics or AppCenter
- Claude Code (`npm install -g @anthropic-ai/claude-code`)
- Python 3.10+
- Jira account with API token
- GitHub personal access token (`repo` + `pull_request` scopes)

---

## Configuration

All config lives in `.env` (copied from `.env.example`):

```env
ANTHROPIC_API_KEY=sk-ant-...
FIREBASE_PROJECT_ID=your-project-id
JIRA_HOST=https://yourorg.atlassian.net
JIRA_EMAIL=you@company.com
JIRA_API_TOKEN=your-token
JIRA_PROJECT_KEY=TRC
GITHUB_TOKEN=ghp_...
GITHUB_OWNER=your-org
GITHUB_REPO=your-repo
```

---

## Memory System

`crash-memory.json` is auto-created in your project root on first run. It tracks every crash ever seen — signature, root cause, fix, Jira ticket, PR link. Commit it to your project repo so the whole team benefits.

---

## License
MIT
