# Architecture

## One process, two independent datasets

`python -m codex_evolution` enters `cli.py`. The web application starts a Python `ThreadingHTTPServer` on IPv4 loopback. `Store` owns a SQLite file separate from Codex. The reproducible demo is generated in memory and never merged into imported records. The frontend explicitly selects `demo` or `live`; both use the same analysis engine.

| Module | Responsibility |
|---|---|
| `ingest.py` | Explicit source discovery, adapters, natural-message prefixes, timestamps, one-to-one cross-stream mirror matching. |
| `storage.py` | App-owned SQLite snapshots and import diagnostics. |
| `rules.py` | Inspectable multilingual word/stage/topic dictionaries. |
| `analytics.py` | Filters, denominators, weighted changes, optional growth dossier, evidence query, workflow proposals. |
| `audit.py` | Conservative plan/instruction checks, scope compatibility, protected lines, proposal-only diffs. |
| `provider.py` | Preview-packet generation, best-effort redaction, explicit tool-free Responses API request, output validation. |
| `reports.py` | Aggregate-only JSON/CSV/Markdown/standalone HTML. |
| `server.py` | Loopback routes, host/origin/token controls, static assets, explicit reads/imports. |
| `web/app.js`, `web/styles.css` | Default introduction plus eight functional pages, SVG heatmaps/trends, evidence dialogs, draft editors, report and Canvas card exports. |

No background model jobs, task executor, shell runner, arbitrary filesystem browser, automatic edits, vector database, cloud sync or separate frontend toolchain is present. The code is intentionally small enough to extend without an agent framework.

The `#start` view explains the three main jobs and previews the current analysis. Its demo action explicitly switches to synthetic data and clears view filters; importing remains a separate user action. Existing route keys remain compatible. The UI starts in light mode unless the browser has a saved theme preference. Native `details` elements disclose secondary report operations while keeping keyboard access and existing request handlers.

## Local API

All API requests require the server-generated `X-Evolution-Token` injected into the local index page. GET queries may select `mode`, `start`, `end`, `project`, `tz`.

| Route | Purpose |
|---|---|
| `GET /api/status`, `/api/prompts` | Runtime/import status; full prompt catalog. |
| `GET /api/analysis`, `/api/evidence`, `/api/workflows` | Statistics, source-linked messages, candidate sequences. |
| `GET /api/report?format=html\|md\|json\|csv` | Aggregate-only downloads. |
| `POST /api/import`, `/api/import-upload` | Explicit filesystem or uploaded history snapshots. |
| `POST /api/audit` | In-memory Markdown/plan review or explicit instruction-root read. |
| `POST /api/packet` | Generate previewable material and its complete prompt. Does not call a model. |
| `POST /api/model` | Send that packet only with explicit consent and environment configuration. |
| `POST /api/clear` | Delete application-imported records after confirmation; source history stays intact. |

This is a local internal API, not an authenticated multi-user service contract. There is no apply-diff or install-skill route.

The `growth` object on `/api/analysis` is computed within the existing natural-message analysis. The report page consumes it directly; `reports.py` applies a nested aggregate allowlist before including it in JSON, Markdown or standalone HTML. It does not require a new endpoint or stored table. Missing or insufficient coverage produces a compact report state. CSV keeps its existing monthly schema; PNG keeps its summary-card format.

## Optional model boundary

The model endpoint is fixed to `https://api.openai.com/v1/responses`. `OPENAI_API_KEY` and `CODEX_EVOLUTION_MODEL` are read from the server process environment. Codex credentials are not reused. Structured output uses `text.format` with a strict JSON schema; requests set `store: false` and provide no tools. The server validates the returned structure and supplied evidence IDs. Provider errors are sanitized rather than echoing secret-bearing response bodies.

Prompt and transcript contents are treated as untrusted **data**. This reduces direct execution risk, but cannot prove the model is immune to misleading text. Always inspect suggestions. Full statistics do not imply full-context model analysis: retrospective packets contain selected excerpts plus aggregates, and all packets are bounded and previewable.

No API compatibility claim is made for every model; choose one your API project can access that supports the required schema. Mock contract/error tests are included; paid live inference was not run. Broader provider support and a reviewed `codex exec` subprocess adapter are roadmap items, not implemented features.

## Primary references consulted, 2026-09-06

Official AGENTS hierarchy and override rules:
https://developers.openai.com/codex/guides/agents-md

Official skill metadata and conditional discovery:
https://developers.openai.com/codex/skills

Official structured-output request guidance:
https://platform.openai.com/docs/guides/structured-outputs

The project implements only the documented subset described above; configuration-dependent runtime instruction loading cannot be fully reconstructed from a selected folder alone.
