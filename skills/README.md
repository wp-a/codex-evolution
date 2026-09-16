# Companion review skills

Four instruction-only skills mirror the application's core improvement workflow:

| Folder | Explicit purpose |
|---|---|
| `collaboration-retrospective` | Evidence-backed longitudinal collaboration review. |
| `anti-bloat-review` | First-principles questions about unnecessary complexity, not deletion of safeguards. |
| `instruction-audit` | Source-cited AGENTS/Skill scope, autonomy, approval and completion review. |
| `workflow-distiller` | Minimal reusable workflow proposals from supporting examples. |

These are included source files, **not installed skills**. Review the entire chosen directory first. Manual adoption typically means copying it into the chosen project's `.agents/skills/` directory; that is an explicit user action outside the app. Each included `agents/openai.yaml` disables implicit invocation, so use an explicit `$skill-name` request when supported by your Codex installation.

No skill grants broader permissions, runs commands by itself, or authorizes changing AGENTS files. The application's mined candidate drafts are separate: they must be reviewed for suitable triggers, scope and actual evidence before adoption.

Official format/activation reference, checked 2026-09-06:
https://developers.openai.com/codex/skills
