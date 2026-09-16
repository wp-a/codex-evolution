"""App-owned SQLite storage. Original Codex history is never written to."""
from __future__ import annotations
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timezone
from .ingest import ImportResult


def default_db() -> Path:
    return Path(os.environ.get("CODEX_EVOLUTION_HOME", "~/.codex-evolution")).expanduser() / "evolution.sqlite"


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS messages (
                    uid TEXT PRIMARY KEY, source TEXT NOT NULL, line INTEGER NOT NULL,
                    thread_id TEXT NOT NULL, timestamp TEXT NOT NULL, role TEXT NOT NULL,
                    text TEXT NOT NULL, channel TEXT NOT NULL, project TEXT NOT NULL,
                    tool TEXT NOT NULL, natural INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS messages_time ON messages(timestamp);
                CREATE TABLE IF NOT EXISTS imports (
                    id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, diagnostics TEXT NOT NULL
                );
            """)
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def ingest(self, result: ImportResult) -> dict:
        with self.connect() as db:
            # Replace snapshots of successfully parsed sources, including removed lines.
            for source in set(result.sources):
                db.execute("DELETE FROM messages WHERE source = ?", (source,))
            db.executemany("""INSERT OR REPLACE INTO messages VALUES
                (:uid, :source, :line, :thread_id, :timestamp, :role, :text,
                 :channel, :project, :tool, :natural)""", [m.record() for m in result.messages])
            d = dict(result.diagnostics, imported_records=len(result.messages))
            db.execute("INSERT INTO imports(created_at, diagnostics) VALUES (?,?)", (
                datetime.now(timezone.utc).isoformat(), json.dumps(d, ensure_ascii=False)))
        return d

    def messages(self) -> list[dict]:
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM messages ORDER BY timestamp, source, line")]

    def diagnostics(self) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT diagnostics FROM imports ORDER BY id DESC LIMIT 1").fetchone()
            sources = db.execute("SELECT COUNT(DISTINCT source), COUNT(*) FROM messages").fetchone()
        return {"last_import": json.loads(row[0]) if row else None,
                "source_count": sources[0], "stored_records": sources[1]}

    def clear(self) -> None:
        with self.connect() as db:
            db.execute("PRAGMA secure_delete = ON")
            db.execute("DELETE FROM messages")
            db.execute("DELETE FROM imports")
        # Vacuum discards free pages from this app DB; no claim about backups/SSD erasure.
        with self.connect() as db:
            db.execute("VACUUM")
