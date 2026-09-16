<div align="center">
  <img src="codex_evolution/web/logo.svg" width="64" alt="Codex Evolution logo">
  <h1>Codex Evolution</h1>
  <p><strong>Turn your Codex history into a clearer way to work.</strong></p>
  <p>Local-first · Zero runtime dependencies · Evidence-linked · MIT</p>
  <p><a href="README.zh-CN.md">简体中文</a> · <a href="docs/QUICKSTART.zh-CN.md">快速上手</a> · <a href="docs/METHODOLOGY.md">Methodology</a> · <a href="SECURITY.md">Privacy & security</a> · <a href="docs/marketing/README.md">Media kit</a></p>
</div>

![Codex Evolution — review your habits, follow the evidence, and prepare reusable methods](docs/marketing/cover-en.png)

**A local workspace for reviewing how you use Codex.** Explore your conversation history, inspect the messages behind each observation, check project rules, and prepare reusable prompts and Skill drafts.

| Start with a question | What you can do |
|---|---|
| How have my prompting habits changed? | Compare monthly patterns and export a retrospective report. |
| What is this observation based on? | Open the original messages with source files, line numbers and thread context. |
| Do my project rules overlap or conflict? | Review `AGENTS.md`, Skill instructions and project plans with cited suggestions. |
| Which methods can I reuse? | Edit prompt templates and review evidence-supported `SKILL.md` drafts. |

Start with **先看示例** to explore synthetic data, or **导入我的记录** to import local history. The macOS-inspired interface supports light and dark themes. The current interface is in Chinese; both English and Chinese documentation are included.

Your records stay on your machine by default. Shareable retrospective reports contain aggregate statistics; optional model requests require a separate preview and explicit consent. Observations describe recorded behavior and do not score your ability.

Version **0.1.1** · Independent community project, not affiliated with or endorsed by OpenAI.

## Run it

Python **3.10+**. No Node.js, database service, API key, GPU, or dependency installation is needed to run from this checkout.

```bash
git clone https://github.com/wp-a/codex-evolution.git
cd codex-evolution
python3 -m codex_evolution demo --open
```

Open `http://127.0.0.1:8765` when browser opening is unavailable. `Ctrl+C` stops the server. Demo mode uses reproducible synthetic data; it never reads your Codex history automatically.

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

## See the workspace

All pictured conversations and statistics use **synthetic demo data**. The images show the Chinese interface.

| Review your habits | Follow the evidence |
|---|---|
| ![Monthly prompting patterns in the collaboration overview](docs/marketing/feature-overview.png) | ![Original message evidence behind a selected observation](docs/marketing/feature-evidence.png) |
| Check project rules | Prepare reusable workflows |
| ![Instruction review with source citations and proposed changes](docs/marketing/feature-rules.png) | ![Prompt templates and reviewable Skill drafts](docs/marketing/feature-workflows.png) |

## A complete observe → improve loop

| Workspace | Functionality in v0.1.1 |
|---|---|
| Start here | Plain-language feature introduction, three-step guide, actual analysis preview, import and synthetic-demo actions. |
| Collaboration overview | Monthly prompt-word and task-signal heatmaps, measured trends, activity grid, weighted changes, project/date/timezone filters. |
| Prompt explorer | Message-level evidence, source filename and line, literal search, word filters, thread context. |
| Evolution timeline | Monthly topic hints, message counts, actual imported tool-call names/counts; no inferred skill scores. |
| Instruction audit | `AGENTS.md`, `AGENTS.override.md`, `SKILL.md`; stopping/confirmation/overlap/completion checks, line citations, protected instructions and proposal-only diffs. |
| Anti-bloat review | Questions about unnecessary Gates, repeated hashes, fallbacks and premature architecture; keeps explicit approval and integrity protections. |
| Skill lab | Three-stage patterns supported by at least three independent threads, supporting excerpts, editable and downloadable skill drafts. |
| Prompt workbench | Five complete, editable prompts: retrospective, anti-bloat, instruction audit, workflow-to-skill, lightweight checkpoint. |
| Growth report | Seven-signal change ledger, six-row monthly task-signal matrix, heuristic observation anchors, cautious readout and optional four-line protocol; Markdown, standalone HTML, aggregate JSON, monthly CSV, and shareable PNG card. |
| Optional semantic interpretation | Previewable/redacted evidence packet, handoff to an existing Codex session, or explicit opt-in OpenAI Responses API request. |

### Better instructions, not fewer protections

> “Every step must wait for confirmation” + “Work autonomously”

The audit cites both lines, checks whether their directory scopes may overlap, and asks whether the friction was intentional. Suggested changes identify permission expansion. Explicit deployment/deletion/credential approvals and release-artifact integrity checks are preserved. **No endpoint applies a patch, installs a skill, runs transcript commands, or changes Codex permissions.**

### Signals, not personality scores

A verification-word increase is not proof of more tests. Short prompts can depend on rich context. Repeated workflows can be ineffective. Observed tool names do not prove task success. This distinction appears in the UI, reports, prompts, and model instructions—not only in this README.

The growth dossier uses the same filtered natural messages as the overview. At least three active months are needed for its early/middle/late comparison; shorter windows show the reason instead of inventing a trend. Phrase rates pool hits and denominators, while prompt length and short-prompt share compare the first and last active months. Empty calendar months stay unavailable in the task matrix. The four-line protocol is optional guidance for longer tasks, not an approval requirement. See [the measurement definitions](docs/METHODOLOGY.md#growth-dossier-v011).

## Inputs and evidence

Supported adapters: Codex `history.jsonl`; selected rollout JSONL `session_meta`, `event_msg` and `response_item` records; normalized JSON/JSONL exports. When explicitly importing a Codex home directory, known `state_*.sqlite` thread tables may enrich project labels **read-only**; this is not a general SQLite message-history adapter.

Local history formats are internal and version-dependent. Deleted/unpersisted sessions, other machines, cloud-only history, omitted event types, and truncated inputs are not magically recovered. The importer reports malformed lines, unknown records, excluded wrappers and mirror counts. See [format support](docs/DATA_FORMAT.md).

Try a small fixture:

```bash
python3 -m codex_evolution --db ./example.sqlite import examples/normalized.jsonl
python3 -m codex_evolution --db ./example.sqlite serve --open
```

## Reports, audits and skills from the CLI

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

## Optional model, explicit choice

Without any API configuration, every local page, deterministic report, rule audit and skill draft works. The workbench can export a self-contained prompt + evidence packet for your existing Codex session.

For an actual API interpretation, set these in the **server process environment**, then restart:

```bash
export OPENAI_API_KEY="your-api-key"
export CODEX_EVOLUTION_MODEL="a-model-you-can-access-that-supports-structured-outputs"
python3 -m codex_evolution serve --open
```

There is no hardcoded, potentially unavailable model name. The request uses the fixed OpenAI Responses API, structured output, `store: false`, and **no tools**. Configuration alone sends nothing: preview and explicitly approve each request. This is separate API usage, not reused Codex subscription authentication.

Statistics process all imported supported records. The model retrospective receives aggregate statistics plus **at most 36 selected excerpts**, not all conversations; instruction/plan packets have a visible size limit. Common-secret redaction is best effort, not a guarantee. `store: false` is not a promise about all provider retention policies. API behavior is mock-tested; no paid live inference was performed for this release. See [architecture and model boundaries](docs/ARCHITECTURE.md).

## Built to be small enough to understand

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

## Tests and contributing

```bash
python3 -m unittest discover -s tests -v
```

Unit/integration tests cover adapters, mirror handling, weighted denominators, empty months, growth-dossier calculations, scope-aware audits, permission preservation, exports, real localhost HTTP and the optional API request contract. Test counts, optional browser checks and the actual verification record are in [QA](docs/QA.md). CI is configured for Python 3.10–3.13 on Ubuntu; only the execution environments listed in QA were actually run during delivery.

Contributions that improve adapters, multilingual evidence quality, accessibility or real-world audit fixtures are especially useful. Share **synthetic minimal reproductions**, never private transcripts. See [CONTRIBUTING](CONTRIBUTING.md) and the [focused roadmap](docs/ROADMAP.md).

MIT © 2026 Codex Evolution contributors.
