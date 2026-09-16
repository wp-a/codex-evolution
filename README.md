<div align="center">
  <img src="codex_evolution/web/logo.svg" width="64" alt="Codex Evolution logo">
  <h1>Codex Evolution</h1>
  <p><strong>Turn your Codex history into a clearer way to work.</strong></p>
  <p>Local-first · Zero runtime dependencies · Evidence-linked · MIT</p>
  <p><a href="README.zh-CN.md">简体中文</a> · <a href="#quick-start">Quick start</a> · <a href="docs/USAGE.md">Usage guide</a> · <a href="docs/METHODOLOGY.md">Methodology</a> · <a href="https://github.com/wp-a/codex-evolution/releases/latest">Downloads</a></p>
</div>

![Codex Evolution — review your habits, follow the evidence, and prepare reusable methods](docs/marketing/cover-en.png)

## What this project is for

**A local workspace for understanding and improving how you use Codex.** Explore your conversation history, inspect recorded token usage, check project rules, and turn observations into a task brief and a small improvement to try next time.

| Start with a question | What you can do |
|---|---|
| How have my prompting habits changed? | Compare monthly patterns and export a retrospective report. |
| Where is my recorded token usage going? | Review monthly and model-context breakdowns, inspect high-usage threads, and check which records are covered. |
| What is this observation based on? | Open the original messages with source files, line numbers and thread context. |
| Do my project rules overlap or conflict? | Review `AGENTS.md`, Skill instructions and project plans with cited suggestions. |
| Which methods can I reuse? | Edit prompt templates and review evidence-supported `SKILL.md` drafts. |
| What can I improve on my next task? | Write a four-part task brief, try one change, and record whether it helped against your own acceptance criteria. |

Start with **先看示例** to explore synthetic data, or **导入我的记录** to import local history. The macOS-inspired interface supports light and dark themes. The current interface is in Chinese; both English and Chinese documentation are included.

Your records stay on your machine by default. Shareable retrospective reports contain aggregate statistics; optional model requests require a separate preview and explicit consent. Observations describe recorded behavior and do not score your ability.

Version **0.2.0** · Independent community project, not affiliated with or endorsed by OpenAI.

## What you can do

| Workspace | Functionality in v0.2.0 |
|---|---|
| Start here | Plain-language feature introduction, three-step guide, actual analysis preview, import and synthetic-demo actions. |
| Collaboration overview | Monthly prompt-word and task-signal heatmaps, measured trends, activity grid, weighted changes, project/date/timezone filters. |
| Token usage (`#usage`) | Imported usage records; monthly and model-context summaries; high-usage threads; input, output, cached-input and reasoning-token fields; visible coverage and aggregate JSON export. Per-response records and legacy cumulative snapshots stay separate. |
| Improvement workbench (`#improve`) | Suggestions grounded in recorded expressions; an editable goal/context/scope/success brief; browser-local trials with acceptance criteria, your own helpful/not-helpful/inconclusive/pending assessment, result notes and JSON export. |
| Prompt explorer | Message-level evidence, source filename and line, literal search, word filters, thread context. |
| Evolution timeline | Monthly topic hints, message counts, actual imported tool-call names/counts; no inferred skill scores. |
| Instruction audit | `AGENTS.md`, `AGENTS.override.md`, `SKILL.md`; stopping/confirmation/overlap/completion checks, line citations, protected instructions and proposal-only diffs. |
| Anti-bloat review | Questions about unnecessary Gates, repeated hashes, fallbacks and premature architecture; keeps explicit approval and integrity protections. |
| Skill lab | Three-stage patterns supported by at least three independent threads, supporting excerpts, editable and downloadable skill drafts. |
| Prompt workbench | Five complete, editable prompts: retrospective, anti-bloat, instruction audit, workflow-to-skill, lightweight checkpoint. |
| Growth report | Seven-signal change ledger, six-row monthly task-signal matrix, heuristic observation anchors, cautious readout and optional four-line protocol; Markdown, standalone HTML, aggregate JSON, monthly CSV, and shareable PNG card. |
| Optional semantic interpretation | Previewable/redacted evidence packet, handoff to an existing Codex session, or explicit opt-in OpenAI Responses API request. |

## Screenshots

All pictured conversations and statistics use **synthetic demo data**. The images show the Chinese interface.

| Review your habits | Follow the evidence |
|---|---|
| ![Monthly prompting patterns in the collaboration overview](docs/marketing/feature-overview.png) | ![Original message evidence behind a selected observation](docs/marketing/feature-evidence.png) |
| Check project rules | Prepare reusable workflows |
| ![Instruction review with source citations and proposed changes](docs/marketing/feature-rules.png) | ![Prompt templates and reviewable Skill drafts](docs/marketing/feature-workflows.png) |

### Recorded Token usage

See input/output totals, cache and reasoning subsets, monthly gaps and coverage before comparing tasks. This screenshot uses synthetic data.

![Recorded Token usage and monthly coverage](docs/screenshots/token-usage.png)

### Prepare a task, then record what helped

Build an editable task brief and keep a small improvement trial with your own acceptance criteria and observations. The example below is synthetic.

![Task brief and local improvement journal](docs/screenshots/improvement-workspace.png)

## Quick start

Python **3.10+**. No Node.js, database service, API key, GPU, or dependency installation is needed to run from this checkout.

```bash
git clone https://github.com/wp-a/codex-evolution.git
cd codex-evolution
python3 -m codex_evolution demo --open
```

Open `http://127.0.0.1:8765` when browser opening is unavailable. `Ctrl+C` stops the server. Demo mode uses reproducible synthetic data; it never reads your Codex history automatically.

Try these two new pages after opening the workspace:

1. Open **Token 用量** (`#usage`) to review the monthly and model-context breakdowns. Read the coverage note before comparing totals or inspecting high-usage threads. Use the page's JSON export to keep the aggregate breakdown.
2. Open **改进工作台** (`#improve`). Fill in your goal, context, scope and success criteria, click **生成任务提示**, then **复制任务提示** to use the brief in your next Codex task. Save one change you want to try with an acceptance criterion; after the task, add a result note and save your own assessment.

You can write a task brief without importing history or configuring a model. Demo and imported-data trial records are kept separately. The [improvement guide](docs/IMPROVEMENT.md) explains the full workflow and browser storage boundaries.

```bash
# Explicitly import your own local history. Original files are not changed.
python3 -m codex_evolution import "${CODEX_HOME:-$HOME/.codex}"
python3 -m codex_evolution serve --open
```

The default application database is `~/.codex-evolution/evolution.sqlite`, separate from Codex. Put a custom `--db` option **before** the command:

```bash
python3 -m codex_evolution --db ./workspace.sqlite demo --port 9000
```

A conventional console entry point is also provided: `python3 -m pip install .`, then `codex-evolution demo --open`. Building/installing this source package requires setuptools, while running the checkout requires only Python's standard library.

For more installation and configuration examples, see the [usage guide](docs/USAGE.md). Source archives and wheels are available in [Releases](https://github.com/wp-a/codex-evolution/releases/latest).

## Detailed usage and data boundaries

### Understand recorded token usage

The usage page reads explicit usage fields in supported imports, including per-response `token_usage_record` events. It groups the records by month and the model context available in the source. Older `token_count` events can contain cumulative snapshots: the latest available snapshot is shown separately instead of adding every snapshot to the per-response total.

Input and output are the primary components; cached input and reasoning are detail fields and should not be added again when the source already includes them in its input or output counts. Missing usage is shown as missing coverage. Records without usage do not establish that a task used zero tokens.

These figures describe the imported local records. The page does not query your account balance, subscription quota or billing, and it does not calculate prices or claim that lower usage means better work. See [usage data definitions](docs/USAGE_DATA.md) for supported fields and aggregation rules.

### Turn an observation into a practical improvement

The improvement workbench offers suggestions from recorded wording and lets you prepare a four-part task brief: **goal, context, scope and success criteria**. Choose one change to try, define how you will judge it, and return after the task to record a result and your own assessment. For example, add an explicit acceptance check to a bug-fix brief, then record whether the requested check was actually completed.

Suggestions and your assessment are not an automatic productivity score or proof that a change caused a better result. Click **生成任务提示** or a save button to persist the relevant brief or records in browser `localStorage`, separate from the imported-history database. They belong to the current browser and service origin: changing the port, hostname or browser creates a separate storage space. Demo and imported-data entries are also separate. Export your notes as JSON before clearing browser data; the export contains what you wrote, so review it before sharing. See the [improvement guide](docs/IMPROVEMENT.md).

### Instruction changes remain reviewable

> “Every step must wait for confirmation” + “Work autonomously”

The audit cites both lines, checks whether their directory scopes may overlap, and asks whether the friction was intentional. Suggested changes identify permission expansion. Explicit deployment/deletion/credential approvals and release-artifact integrity checks are preserved. **No endpoint applies a patch, installs a skill, runs transcript commands, or changes Codex permissions.**

### Read the measurements in context

A verification-word increase is not proof of more tests. Short prompts can depend on rich context. Repeated workflows can be ineffective. Observed tool names do not prove task success. This distinction appears in the UI, reports, prompts, and model instructions—not only in this README.

The growth dossier uses the same filtered natural messages as the overview. At least three active months are needed for its early/middle/late comparison; shorter windows show the reason instead of inventing a trend. Phrase rates pool hits and denominators, while prompt length and short-prompt share compare the first and last active months. Empty calendar months stay unavailable in the task matrix. The four-line protocol is optional guidance for longer tasks, not an approval requirement. See [the measurement definitions](docs/METHODOLOGY.md#growth-dossier-v011).

### Import formats and source evidence

Supported adapters: Codex `history.jsonl`; selected rollout JSONL `session_meta`, `event_msg` and `response_item` records; normalized JSON/JSONL exports. When explicitly importing a Codex home directory, known `state_*.sqlite` thread tables may enrich project labels **read-only**; this is not a general SQLite message-history adapter.

Local history formats are internal and version-dependent. Deleted/unpersisted sessions, other machines, cloud-only history, omitted event types, and truncated inputs are not magically recovered. The importer reports malformed lines, unknown records, excluded wrappers and mirror counts. See [format support](docs/DATA_FORMAT.md).

Try a small fixture:

```bash
python3 -m codex_evolution --db ./example.sqlite import examples/normalized.jsonl
python3 -m codex_evolution --db ./example.sqlite serve --open
```

### Reports, audits and Skill drafts from the CLI

```bash
python3 -m codex_evolution report --demo --format html --out demo-report.html
python3 -m codex_evolution report --format json --out statistics.json
python3 -m codex_evolution audit /path/to/project --out instruction-audit.json
python3 -m codex_evolution audit examples/plan.md --plan --out plan-review.json
python3 -m codex_evolution skills --demo --out ./review-drafts
python3 -m codex_evolution prompt instruction-audit --out audit-prompt.md
python3 -m codex_evolution doctor
```

Standalone review skills are included in [`skills/`](skills/README.md). Review them before manually adopting them. Exporting a candidate does not install it. Audit exports and task packets contain selected text; aggregate reports intentionally exclude raw messages, source paths and project identifiers.

### Optional model interpretation

Without any API configuration, every local page, deterministic report, rule audit and skill draft works. The workbench can export a self-contained prompt + evidence packet for your existing Codex session.

For an actual API interpretation, set these in the **server process environment**, then restart:

```bash
export OPENAI_API_KEY="your-api-key"
export CODEX_EVOLUTION_MODEL="a-model-you-can-access-that-supports-structured-outputs"
python3 -m codex_evolution serve --open
```

There is no hardcoded, potentially unavailable model name. The built-in connection uses the fixed official endpoint `https://api.openai.com/v1/responses`, structured output, `store: false`, and **no tools**. It does not currently support a custom base URL or relay configuration. Configuration alone sends nothing: preview and explicitly approve each request. This is separate API usage, not reused Codex subscription authentication.

Statistics process all imported supported records. The model retrospective receives aggregate statistics plus **at most 36 selected excerpts**, not all conversations; instruction/plan packets have a visible size limit. Common-secret redaction is best effort, not a guarantee. `store: false` is not a promise about all provider retention policies. API behavior is mock-tested; no paid live inference was performed for this release. See [architecture and model boundaries](docs/ARCHITECTURE.md).

## How it works

```text
Local Codex JSONL / normalized exports
  → explicit import → source-preserving adapters → app-owned SQLite
  → one-to-one mirror matching → deterministic metrics / evidence
  → heatmaps · timeline · reports · workflow candidates

Selected instructions / plan
  → conservative rule audit → quotes + proposed edits + permission flags
  → optional reviewed evidence packet → Codex handoff / opt-in model
```

Python standard library backend; native HTML/CSS/JavaScript frontend; native SVG/Canvas charts; no CDN, trackers, external fonts, frontend build pipeline, microservices or agent orchestration framework. The HTTP service is for one trusted local user, not public hosting.

## From the author

> **Author's AI service · Promotion · WPIRONMAN AI Relay**<br>
> OpenAI-compatible API access for clients that support a custom base URL. [Visit the console for setup details](https://api.wpironman.top).<br>
> This service is run by the project author. Codex Evolution's local features do not require it; the optional built-in model connection currently uses the official OpenAI API and does not support relay configuration.

## Documentation and contributing

```bash
python3 -m unittest discover -s tests -v
```

Unit/integration tests cover adapters, mirror handling, weighted denominators, empty months, growth-dossier calculations, scope-aware audits, permission preservation, exports, real localhost HTTP and the optional API request contract. Test counts, optional browser checks and the actual verification record are in [QA](docs/QA.md). CI is configured for Python 3.10–3.13 on Ubuntu; only the execution environments listed in QA were actually run during delivery.

Contributions that improve adapters, multilingual evidence quality, accessibility or real-world audit fixtures are especially useful. Share **synthetic minimal reproductions**, never private transcripts. See [CONTRIBUTING](CONTRIBUTING.md) and the [focused roadmap](docs/ROADMAP.md).

| Read next | Contents |
|---|---|
| [Usage guide](docs/USAGE.md) / [中文快速上手](docs/QUICKSTART.zh-CN.md) | Installation, imports, CLI commands and optional model setup. |
| [Data formats](docs/DATA_FORMAT.md) / [Methodology](docs/METHODOLOGY.md) | Supported records, metrics and interpretation limits. |
| [Usage data](docs/USAGE_DATA.md) / [Improvement guide](docs/IMPROVEMENT.md) | Token coverage, accounting boundaries, task briefs and local improvement trials. |
| [Architecture](docs/ARCHITECTURE.md) / [Security](SECURITY.md) | Local processing, evidence handling and model boundaries. |
| [QA](docs/QA.md) / [Roadmap](docs/ROADMAP.md) | Verification records and planned work. |
| [Contributing](CONTRIBUTING.md) / [Standalone skills](skills/README.md) | Development guidance and manually adoptable review skills. |

MIT © 2026 Codex Evolution contributors.
