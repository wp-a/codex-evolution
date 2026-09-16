# Codex Evolution usage guide

[Project overview](../README.md) · [中文快速上手](QUICKSTART.zh-CN.md) · [Data formats](DATA_FORMAT.md)

Codex Evolution runs locally with Python **3.10+** and zero runtime dependencies. The interface is currently in Chinese. Demo mode lets you explore every local page using synthetic data before importing any records.

## Run from a checkout

```bash
git clone https://github.com/wp-a/codex-evolution.git
cd codex-evolution
python3 -m codex_evolution demo --open
```

Open `http://127.0.0.1:8765` if browser opening is unavailable. Press `Ctrl+C` to stop the server. No Node.js, database service, GPU or API key is needed. Demo mode never imports your history automatically.

The default application database is `~/.codex-evolution/evolution.sqlite`, separate from Codex. Put a custom `--db` option **before** the command:

```bash
python3 -m codex_evolution --db ./workspace.sqlite demo --port 9000
```

The server supports `--tz` for the initial reporting timezone:

```bash
python3 -m codex_evolution serve --tz Asia/Shanghai --open
```

## Install the console command

From the checkout:

```bash
python3 -m pip install .
codex-evolution demo --open
```

Building or installing the source package requires setuptools; running the checkout uses only Python's standard library. The installed `codex-evolution` command accepts the same options as `python3 -m codex_evolution`.

## Import records explicitly

```bash
python3 -m codex_evolution import "${CODEX_HOME:-$HOME/.codex}"
python3 -m codex_evolution serve --open
```

Original files are not changed. The importer creates an application-owned copy in the selected database. To try a small fixture in a separate database:

```bash
python3 -m codex_evolution --db ./example.sqlite import examples/normalized.jsonl
python3 -m codex_evolution --db ./example.sqlite serve --open
```

Supported adapters include Codex `history.jsonl`; selected rollout JSONL `session_meta`, `event_msg` and `response_item` records; and normalized JSON/JSONL exports. When explicitly importing a Codex home directory, known `state_*.sqlite` thread tables may enrich project labels **read-only**. This is not a general SQLite message-history adapter.

Local history formats are internal and version-dependent. Deleted or unpersisted sessions, records on other machines, cloud-only history, omitted event types and truncated inputs cannot be recovered by the importer. It reports malformed lines, unknown records, excluded wrappers and mirror counts. See [format support](DATA_FORMAT.md).

## Workspace reference

| Workspace | Functionality in v0.1.1 |
|---|---|
| Start here | Feature introduction, three-step guide, actual analysis preview, import and synthetic-demo actions. |
| Collaboration overview | Monthly prompt-word and task-signal heatmaps, measured trends, activity grid, weighted changes, project/date/timezone filters. |
| Prompt explorer | Message-level evidence, source filename and line, literal search, word filters, thread context. |
| Evolution timeline | Monthly topic hints, message counts and actual imported tool-call names/counts; no inferred skill scores. |
| Instruction audit | `AGENTS.md`, `AGENTS.override.md`, `SKILL.md`; stopping/confirmation/overlap/completion checks, line citations, protected instructions and proposal-only diffs. |
| Anti-bloat review | Questions about unnecessary Gates, repeated hashes, fallbacks and premature architecture; preserves explicit approval and integrity protections. |
| Skill lab | Three-stage patterns supported by at least three independent threads, supporting excerpts, editable and downloadable Skill drafts. |
| Prompt workbench | Five complete, editable prompts: retrospective, anti-bloat, instruction audit, workflow-to-skill and lightweight checkpoint. |
| Growth report | Seven-signal change ledger, six-row monthly task-signal matrix, heuristic observation anchors, cautious readout and optional four-line protocol; Markdown, standalone HTML, aggregate JSON, monthly CSV and shareable PNG card. |
| Optional semantic interpretation | Previewable/redacted evidence packet, handoff to an existing Codex session, or explicit opt-in OpenAI Responses API request. |

## Reports, audits and Skill drafts from the CLI

```bash
python3 -m codex_evolution report --demo --format html --out demo-report.html
python3 -m codex_evolution report --format json --out statistics.json
python3 -m codex_evolution audit /path/to/project --out instruction-audit.json
python3 -m codex_evolution audit examples/plan.md --plan --out plan-review.json
python3 -m codex_evolution skills --demo --out ./review-drafts
python3 -m codex_evolution prompt instruction-audit --out audit-prompt.md
python3 -m codex_evolution doctor
```

Reports also support `--format md` and `--format csv`, plus `--from`, `--to`, `--project` and `--tz` filters. Use `python3 -m codex_evolution report --help` for the options.

Standalone review skills are included in [`skills/`](../skills/README.md). Review them before manually adopting them. Exporting a candidate does not install it. Audit exports and task packets contain selected text; aggregate reports intentionally exclude raw messages, source paths and project identifiers.

## Optional model interpretation

Every local page, deterministic report, rule audit and Skill draft works without API configuration. The workbench can also export a self-contained prompt and evidence packet for an existing Codex session.

For an actual API interpretation, set these in the **server process environment**, then restart:

```bash
export OPENAI_API_KEY="your-api-key"
export CODEX_EVOLUTION_MODEL="a-model-you-can-access-that-supports-structured-outputs"
python3 -m codex_evolution serve --open
```

There is no hardcoded model name. The built-in connection uses the fixed official endpoint `https://api.openai.com/v1/responses`, structured output, `store: false` and **no tools**. It does not currently support a custom base URL or relay configuration. Configuration alone sends nothing: preview and explicitly approve each request. This uses a separate API credential, not Codex subscription authentication.

Statistics process all imported supported records. The model retrospective receives aggregate statistics plus **at most 36 selected excerpts**, not all conversations. Instruction and plan packets have a visible size limit. Common-secret redaction is best effort, not a guarantee, and `store: false` is not a promise about all provider retention policies. API behavior is mock-tested; no paid live inference was performed for this release. See [architecture and model boundaries](ARCHITECTURE.md).

## Read findings in context

### Instruction changes remain proposals

For a pair such as “Every step must wait for confirmation” and “Work autonomously,” the audit cites both lines, checks whether their directory scopes may overlap, and asks whether the friction was intentional. Suggested changes identify permission expansion. Explicit deployment, deletion and credential approvals, along with release-artifact integrity checks, are preserved.

**No endpoint applies a patch, installs a Skill, runs transcript commands or changes Codex permissions.**

### Signals describe the available records

A verification-word increase is not proof of more tests. Short prompts can depend on rich context. Repeated workflows can be ineffective. Observed tool names do not prove task success. The UI, reports, prompts and model instructions preserve these distinctions.

The growth dossier uses the same filtered natural messages as the overview. At least three active months are needed for its early/middle/late comparison; shorter windows explain why a trend is unavailable. Phrase rates pool hits and denominators, while prompt length and short-prompt share compare the first and last active months. Empty calendar months remain unavailable in the task matrix. The four-line protocol is optional guidance for longer tasks, not an approval requirement. See the [measurement definitions](METHODOLOGY.md#growth-dossier-v011).

## How local processing fits together

```text
Local Codex JSONL / normalized exports
  → explicit import → source-preserving adapters → app-owned SQLite
  → one-to-one mirror matching → deterministic metrics / evidence
  → heatmaps · timeline · reports · workflow candidates

Selected instructions / plan
  → conservative rule audit → quotes + proposed edits + permission flags
  → optional reviewed evidence packet → Codex handoff / opt-in model
```

The backend uses the Python standard library. The frontend uses native HTML, CSS and JavaScript with SVG/Canvas charts. There are no CDNs, trackers, external fonts, frontend build pipeline, microservices or agent orchestration framework. The HTTP service is intended for one trusted local user, not public hosting.

## Verify changes and contribute

```bash
python3 -m unittest discover -s tests -v
```

Unit and integration tests cover adapters, mirror handling, weighted denominators, empty months, growth-dossier calculations, scope-aware audits, permission preservation, exports, real localhost HTTP and the optional API request contract. CI is configured for Python 3.10–3.13 on Ubuntu. See [QA](QA.md) for the actual execution record and optional browser checks.

Adapter improvements, multilingual evidence quality, accessibility and real-world audit fixtures are welcome. Share **synthetic minimal reproductions**, never private transcripts. See [CONTRIBUTING](../CONTRIBUTING.md) and the [focused roadmap](ROADMAP.md).
