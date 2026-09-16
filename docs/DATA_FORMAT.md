# Supported inputs and limits

Imports require a user-selected directory or file. The application never scans the whole machine or reads `auth.json`, credentials files, `.env`, or Codex configuration for secrets.

## Normalized interchange format

JSONL (one object per line), a JSON array, or `{ "messages": [...] }`:

```json
{"thread_id":"example-thread","timestamp":"2026-01-01T12:00:00+00:00","role":"user","text":"Plan the scope, then implement the change.","project":"synthetic-project"}
```

`role`: `user`, `assistant`, or `tool`. For tool records use `tool` for the name and `text` for supported arguments/context. `timestamp` accepts ISO 8601, Unix seconds or milliseconds. Optional aliases: `session_id`, `ts`, `created_at`, `content`. Use one format consistently; this is not a general importer for arbitrary chat-platform exports.

The example at `examples/normalized.jsonl` has nine user messages across three independent threads plus synthetic assistant/tool context. It demonstrates the plan → execute → verify workflow candidate.

## Codex local adapters

| Input | Fields recognized |
|---|---|
| `history.jsonl` | `session_id`, `ts`, `text` |
| rollout `session_meta` | `payload.id`, `payload.cwd` |
| rollout `event_msg` | `payload.type=user_message/agent_message`, `payload.message`, top-level `timestamp` |
| rollout `response_item` message | `payload.role`, text/input_text/output_text content blocks, timestamp; user fallback only when the file has no user events |
| rollout tool call | `function_call`/`custom_tool_call` name and arguments/input |
| optional metadata DB | explicit import root's `state_*.sqlite`, known `threads(id,cwd)` columns, read-only project enrichment |

Reasoning, token events, tool outputs, binary attachments, screenshots, audio, and unknown event variants are not reconstructed. Some unknown records are counted; recognized non-message noise is skipped. These adapters are format-tolerant, **not an official stable Codex storage API or a universal SQLite export reader**. On-disk format coverage is fixture-tested; no live Codex installation was available for compatibility verification in this delivery.

A Codex-home import looks in `sessions/`, `archived_sessions/` and `history.jsonl`. If no recognized home-layout files are present, an explicitly selected exports/sessions folder is searched for JSONL, excluding common hidden/build/log locations. Child symlinks are not followed. A specifically selected root is resolved as a path; do not assume this is an OS sandbox.

## Resource limits and reporting

Filesystem importer: 256 MiB per file, 8 MiB per JSONL line, at most 250,000 records per import batch, 100,000 text characters per message. Oversized files and batches produce warnings; overlong messages are truncated and counted. Split large histories into explicit batches; totals accumulate across distinct sources. The web-upload body limit is 32 MiB and the picker accepts at most 300 files; it is for small exports. Use the CLI for larger histories. Parsing/analytics currently hold records in memory; this MVP is not a million-thread streaming database engine.

JSONL evidence line numbers refer to physical lines. JSON-array evidence line numbers refer to one-based array item positions, not physical lines of a pretty-printed JSON document. Uploaded file paths are application-local source labels, not new filesystem files.

Imports expose diagnostics: files, lines, malformed JSON, invalid timestamps, unknown events, non-natural users, mirrored response messages, truncated text and warnings. A successfully parsed source snapshot replaces its old snapshot; malformed JSONL lines are skipped, so fixing and re-importing the source is recommended. Invalid whole JSON documents are reported/skipped. Keep original files as the authoritative source.

## Source reference

OpenAI documents configurable local history persistence under the Codex home directory. Persistence settings, deletion and other devices affect coverage:
https://developers.openai.com/codex/config-advanced

This project treats local JSONL decoding as its own versioned adapter and does not assert that every internal event layout is guaranteed by that documentation.
