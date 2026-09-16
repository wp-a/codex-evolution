"""Read explicit, local inputs. Never import credentials or execute transcript text.

Codex's on-disk formats are internal, version-dependent formats. Adapters tolerate
unknown events and report their coverage; a local import is NOT an account export.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_FILE_BYTES = 256 * 1024 * 1024
MAX_LINE_BYTES = 8 * 1024 * 1024
MAX_MESSAGES = 250_000
DENIED_NAMES = {"auth.json", "credentials.json", "config.toml", ".env"}


@dataclass
class Message:
    source: str
    line: int
    thread_id: str
    timestamp: str
    role: str
    text: str
    channel: str = "normalized"
    project: str = "unassigned"
    tool: str = ""
    natural: bool = True
    uid: str = ""

    def record(self) -> dict:
        d = asdict(self)
        d["uid"] = self.uid or f"{self.source}::{self.line}::{self.channel}"
        return d


@dataclass
class ImportResult:
    messages: list[Message] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    diagnostics: dict = field(default_factory=lambda: {
        "files": 0, "lines": 0, "invalid_json": 0, "unknown_events": 0,
        "invalid_timestamps": 0, "non_natural_users": 0,
        "mirrored_user_records": 0, "truncated_messages": 0, "warnings": [],
    })

    def merge(self, other: "ImportResult") -> None:
        self.messages.extend(other.messages)
        self.sources.extend(other.sources)
        for k, v in other.diagnostics.items():
            if k == "warnings":
                self.diagnostics[k].extend(v)
            else:
                self.diagnostics[k] += v


def timestamp(value: Any) -> str | None:
    try:
        if isinstance(value, bool) or value is None:
            return None
        if isinstance(value, (int, float)):
            value = value / 1000 if value > 100_000_000_000 else value
            dt = datetime.fromtimestamp(value, timezone.utc)
        else:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        if not 1970 <= dt.year <= 2100:
            return None
        return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds")
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            str(c.get("text", "")) for c in content if isinstance(c, dict)
            and c.get("type", "text") in {"text", "input_text", "output_text"}
        )
    return ""


def natural_user(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    prefixes = ("# AGENTS.md instructions for ", "<environment_context>",
                "<permissions instructions>", "<user_shell_command>",
                "<turn_aborted>", "<INSTRUCTIONS>")
    return not stripped.startswith(prefixes)


def parse_objects(objects: list[tuple[int, Any]], source: str) -> ImportResult:
    result = ImportResult(sources=[source])
    result.diagnostics["files"] = 1
    result.diagnostics["lines"] = len(objects)
    meta: dict[str, Any] = {}
    has_user_events = False
    for _, obj in objects:
        if not isinstance(obj, dict):
            continue
        payload = obj.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        if obj.get("type") == "session_meta":
            meta.update(payload)
        if obj.get("type") == "event_msg" and payload.get("type") == "user_message":
            has_user_events = True
    thread = str(meta.get("id") or Path(source).stem)
    project = str(meta.get("cwd") or "unassigned")

    def add(line: int, obj: dict, role: str, text: str, channel: str,
            tool: str = "", thread_id: str | None = None, project_name: str | None = None) -> None:
        raw_time = obj.get("timestamp", obj.get("ts", obj.get("created_at")))
        ts = timestamp(raw_time)
        if not ts:
            result.diagnostics["invalid_timestamps"] += 1
            return
        if not text and not tool:
            return
        if len(text) > 100_000:
            text = text[:100_000]
            result.diagnostics["truncated_messages"] += 1
        natural = role == "user" and natural_user(text)
        if role == "user" and not natural:
            result.diagnostics["non_natural_users"] += 1
        result.messages.append(Message(source, line, thread_id or thread, ts,
                                       role, text, channel, project_name or project,
                                       tool, natural))

    known_noise = {"turn_context", "compacted", "session_meta"}
    event_noise = {"token_count", "agent_reasoning", "agent_reasoning_delta",
                   "task_started", "task_complete", "turn_aborted", "context_compacted",
                   "agent_message_delta", "user_message"}
    for line, obj in objects:
        if not isinstance(obj, dict):
            result.diagnostics["unknown_events"] += 1
            continue
        typ = obj.get("type", "")
        p = obj.get("payload", {})
        p = p if isinstance(p, dict) else {}
        if typ == "event_msg":
            t = p.get("type", "")
            if t == "user_message":
                add(line, obj, "user", content_text(p.get("message", "")), "event")
            elif t == "agent_message":
                add(line, obj, "assistant", content_text(p.get("message", "")), "event")
            elif t not in event_noise:
                result.diagnostics["unknown_events"] += 1
        elif typ == "response_item":
            t, role = p.get("type"), p.get("role", "")
            if t == "message" and role in {"user", "assistant"}:
                if role == "user" and has_user_events:
                    result.diagnostics["mirrored_user_records"] += 1
                    continue
                add(line, obj, role, content_text(p.get("content", "")), "response")
            elif t in {"function_call", "custom_tool_call"}:
                add(line, obj, "tool", str(p.get("arguments") or p.get("input") or ""),
                    "response", str(p.get("name") or "unknown"))
            elif t not in {"reasoning", "function_call_output", "custom_tool_call_output"}:
                result.diagnostics["unknown_events"] += 1
        elif "session_id" in obj and "text" in obj and "ts" in obj:
            add(line, obj, "user", str(obj["text"]), "history", thread_id=str(obj["session_id"]))
        elif obj.get("role") in {"user", "assistant", "tool"}:
            add(line, obj, str(obj["role"]), content_text(obj.get("text", obj.get("content", ""))),
                "normalized", str(obj.get("tool", "")),
                str(obj.get("thread_id") or obj.get("session_id") or thread),
                str(obj.get("project") or project))
        elif typ not in known_noise:
            result.diagnostics["unknown_events"] += 1
    return result


def parse_text(text: str, source: str, *, json_document: bool = False) -> ImportResult:
    if Path(source).name.lower() in DENIED_NAMES:
        raise ValueError("Credential/config files are not history inputs.")
    invalid = oversized = 0
    objects = []
    if json_document:
        data = json.loads(text)
        if isinstance(data, dict):
            data = data.get("messages")
        if not isinstance(data, list):
            raise ValueError("JSON must be a message array or an object with a messages array.")
        objects = list(enumerate(data, 1))
    else:
        for line, raw in enumerate(text.splitlines(), 1):
            if not raw.strip():
                continue
            if len(raw.encode("utf-8")) > MAX_LINE_BYTES:
                oversized += 1
                continue
            try:
                objects.append((line, json.loads(raw)))
            except (json.JSONDecodeError, RecursionError):
                invalid += 1
    result = parse_objects(objects, source)
    result.diagnostics["invalid_json"] += invalid
    result.diagnostics["lines"] += invalid + oversized
    if oversized:
        result.diagnostics["warnings"].append(f"{oversized} lines exceeded the 8 MiB line limit.")
    return result


def discover(path: Path) -> list[Path]:
    path = path.expanduser().resolve()
    if not path.exists():
        raise ValueError(f"Input does not exist: {path}")
    if path.is_file():
        if path.name.lower() in DENIED_NAMES or path.suffix.lower() not in {".jsonl", ".json"}:
            raise ValueError("Select history.jsonl, rollout JSONL, or a normalized JSON export; never auth.json.")
        return [path]
    files: list[Path] = []
    # Only known history locations inside CODEX_HOME; never recurse into arbitrary logs/auth caches.
    for folder in (path / "sessions", path / "archived_sessions"):
        if folder.is_dir() and not folder.is_symlink():
            for base, dirs, names in os.walk(folder, followlinks=False):
                dirs[:] = [d for d in dirs if not (Path(base) / d).is_symlink()]
                files.extend(Path(base) / n for n in names if n.endswith(".jsonl") and not (Path(base) / n).is_symlink())
    if (path / "history.jsonl").is_file() and not (path / "history.jsonl").is_symlink():
        files.append(path / "history.jsonl")
    # An explicit standalone exports/sessions folder is also allowed (JSONL only).
    if not files:
        for base, dirs, names in os.walk(path, followlinks=False):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {"node_modules", "auth", "logs"}
                       and not (Path(base) / d).is_symlink()]
            files.extend(Path(base) / n for n in names if n.endswith(".jsonl") and not (Path(base) / n).is_symlink())
    return sorted(set(files))


def thread_metadata(root: Path) -> dict[str, str]:
    """Optional read-only enrichment of known Codex threads tables; not a message adapter."""
    projects = {}
    if not root.is_dir():
        return projects
    for file in sorted(root.glob("state_*.sqlite")):
        if file.is_symlink():
            continue
        try:
            with closing(sqlite3.connect(file.resolve().as_uri() + "?mode=ro", uri=True)) as db:
                db.execute("PRAGMA query_only = ON")
                cols = {row[1] for row in db.execute("PRAGMA table_info(threads)")}
                if {"id", "cwd"} <= cols:
                    projects.update({str(k): str(v) for k, v in db.execute("SELECT id, cwd FROM threads") if v})
        except sqlite3.Error:
            continue
    return projects


def import_path(path: str | Path) -> ImportResult:
    root = Path(path).expanduser().resolve()
    files = discover(root)
    if not files:
        raise ValueError("No supported history files found. Select CODEX_HOME, a sessions folder, or an export file.")
    result = ImportResult()
    projects = thread_metadata(root)
    for file in files:
        try:
            if file.stat().st_size > MAX_FILE_BYTES:
                result.diagnostics["warnings"].append(f"Skipped oversized file: {file.name} (>256 MiB)")
                continue
            parsed = parse_text(file.read_text(encoding="utf-8-sig", errors="replace"), str(file),
                                json_document=file.suffix == ".json")
            if len(result.messages) + len(parsed.messages) > MAX_MESSAGES:
                result.diagnostics["warnings"].append("Stopped before the 250,000-record import limit; import smaller batches.")
                break
            result.merge(parsed)
        except (OSError, ValueError) as exc:
            result.diagnostics["warnings"].append(f"{file.name}: {exc}")
    for msg in result.messages:
        if msg.project == "unassigned":
            msg.project = projects.get(msg.thread_id, "unassigned")
    result.diagnostics["warnings"].append(
        "Local projection only. Deleted, unpersisted, other-device and cloud-only sessions are not covered."
    )
    return result


def canonical_messages(rows: list[dict]) -> tuple[list[dict], int]:
    """One-to-one cross-stream mirror matching within two seconds.

    Repeated identical prompts inside the SAME stream are never collapsed. A
    mirror may match once per secondary stream, preserving occurrence counts.
    No fuzzy text matching or content hashes are used.
    """
    priority = {"event": 0, "response": 1, "normalized": 1, "history": 2}
    ordered = sorted(rows, key=lambda r: (priority.get(r["channel"], 3), r["source"], r["line"]))
    buckets: dict[tuple, list] = {}
    kept = []
    duplicates = 0
    for row in ordered:
        key = (row["thread_id"], row["role"], row["text"], row.get("tool", ""))
        stream = (row["source"], row["channel"])
        ts = datetime.fromisoformat(row["timestamp"]).timestamp()
        bucket = buckets.setdefault(key, [])
        match = next((entry for entry in bucket
                      if stream not in entry["streams"] and abs(ts - entry["ts"]) <= 2), None)
        if match:
            match["streams"].add(stream)
            duplicates += 1
            if match["row"].get("project") == "unassigned" and row.get("project") != "unassigned":
                match["row"]["project"] = row["project"]
            continue
        saved = dict(row)
        kept.append(saved)
        bucket.append({"ts": ts, "streams": {stream}, "row": saved})
    return sorted(kept, key=lambda r: (r["timestamp"], r["source"], r["line"])), duplicates
