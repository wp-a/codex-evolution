"""Loopback-only, same-origin local app server. No framework or CDN required."""
from __future__ import annotations
import json
import mimetypes
import os
import secrets
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from . import __version__
from .analytics import analyze, evidence, mine_workflows, prepare, select
from .audit import audit_instructions, audit_plan, load_files
from .demo import demo_messages
from .ingest import ImportResult, import_path, parse_text
from .prompt_library import prompts, get_prompt
from .provider import capabilities, make_packet, interpret
from .reports import public_analysis, report_markdown, report_html, report_csv
from .storage import Store

WEB = Path(__file__).parent / "web"
MAX_BODY = 32 * 1024 * 1024


class EvolutionServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, store: Store, *, initial_mode: str = "demo", timezone: str = "UTC"):
        if address[0] != "127.0.0.1":
            raise ValueError("This single-user local server only binds to 127.0.0.1.")
        self.store = store
        self.token = secrets.token_urlsafe(32)
        self.initial_mode = initial_mode
        self.timezone = timezone
        super().__init__(address, Handler)

    def rows(self, mode: str):
        if mode not in {"demo", "live"}:
            raise ValueError("Unknown dataset mode.")
        return demo_messages() if mode == "demo" else self.store.messages()


class Handler(BaseHTTPRequestHandler):
    server: EvolutionServer
    server_version = "CodexEvolution/" + __version__

    def log_message(self, format, *args):
        # Query strings can contain project paths/search text. Don't log requests.
        pass

    def reply(self, body, status=200, content_type="application/json; charset=utf-8", filename=""):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def guard(self, *, api: bool = True):
        port = self.server.server_port
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if self.headers.get("Host", "").lower() not in hosts:
            raise PermissionError("Invalid Host header.")
        origin = self.headers.get("Origin")
        if origin and origin not in {"http://" + h for h in hosts}:
            raise PermissionError("Cross-origin access is not allowed.")
        if api and self.headers.get("X-Evolution-Token") != self.server.token:
            raise PermissionError("Missing local session token. Reload the app.")

    def query(self):
        query = {key: values[-1] for key, values in parse_qs(urlsplit(self.path).query).items()}
        mode = query.get("mode", self.server.initial_mode)
        filters = {key: query.get(key, "") for key in ("start", "end", "project")}
        filters["tz"] = query.get("tz", self.server.timezone)
        return query, mode, filters

    def do_GET(self):
        try:
            path = urlsplit(self.path).path
            self.guard(api=path.startswith("/api/"))
            if not path.startswith("/api/"):
                allowed = {"/": "index.html", "/index.html": "index.html", "/app.js": "app.js",
                           "/styles.css": "styles.css", "/logo.svg": "logo.svg", "/favicon.ico": "logo.svg"}
                filename = allowed.get(path)
                if not filename:
                    return self.reply({"error": "Not found"}, 404)
                file = WEB / filename
                if filename == "index.html":
                    body = file.read_text(encoding="utf-8").replace("__SESSION_TOKEN__", self.server.token)
                    return self.reply(body, content_type="text/html; charset=utf-8")
                return self.reply(file.read_bytes(), content_type=mimetypes.guess_type(file)[0] or "application/octet-stream")
            query, mode, filters = self.query()
            if path == "/api/status":
                return self.reply({"version": __version__, "initial_mode": self.server.initial_mode,
                                   "timezone": self.server.timezone, "storage": self.server.store.diagnostics(),
                                   "provider": capabilities(), "local_only": True})
            if path == "/api/prompts":
                return self.reply(prompts())
            rows = self.server.rows(mode)
            if path == "/api/analysis":
                return self.reply(analyze(rows, mode=mode, **filters))
            if path == "/api/evidence":
                return self.reply(evidence(rows, **filters, **{key: query.get(key, "") for key in ("word", "stage", "month", "query", "thread")},
                                           offset=max(0, int(query.get("offset", 0))), limit=min(100, max(1, int(query.get("limit", 40))))))
            if path == "/api/workflows":
                return self.reply({"candidates": mine_workflows(rows, **filters)})
            if path == "/api/report":
                data = analyze(rows, mode=mode, **filters)
                format_ = query.get("format", "md")
                formats = {
                    "md": (report_markdown, "text/markdown; charset=utf-8", "report.md"),
                    "html": (report_html, "text/html; charset=utf-8", "report.html"),
                    "json": (lambda d: json.dumps(public_analysis(d), ensure_ascii=False, indent=2), "application/json; charset=utf-8", "statistics.json"),
                    "csv": (report_csv, "text/csv; charset=utf-8", "monthly.csv"),
                }
                if format_ not in formats:
                    raise ValueError("Unknown export format.")
                fn, content_type, filename = formats[format_]
                return self.reply(fn(data), content_type=content_type, filename="codex-evolution-" + filename)
            return self.reply({"error": "Not found"}, 404)
        except PermissionError as exc:
            self.reply({"error": str(exc)}, 403)
        except (ValueError, TypeError) as exc:
            self.reply({"error": str(exc)}, 400)
        except Exception:
            self.reply({"error": "Local request failed. Check input format or server permissions; no source files were changed."}, 500)

    def do_POST(self):
        try:
            self.guard()
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise ValueError("Use application/json.")
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_BODY:
                return self.reply({"error": "Request body must be between 1 byte and 32 MiB."}, 413)
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError("Request body must be a JSON object.")
            path = urlsplit(self.path).path
            if path == "/api/import":
                raw = body.get("path", "")
                if not isinstance(raw, str) or not raw.strip():
                    raise ValueError("Enter an explicit local history path.")
                result = import_path(raw)
                return self.reply(self.server.store.ingest(result))
            if path == "/api/import-upload":
                files = body.get("files")
                if not isinstance(files, list) or not 1 <= len(files) <= 300:
                    raise ValueError("Select between 1 and 300 JSON/JSONL history files.")
                result = ImportResult()
                for file in files:
                    name, content = file.get("name"), file.get("text")
                    if not isinstance(name, str) or not isinstance(content, str):
                        raise ValueError("Invalid uploaded file.")
                    name = name.replace("\\", "/")
                    if Path(name).is_absolute() or ":" in name or ".." in Path(name).parts or Path(name).suffix not in {".json", ".jsonl"}:
                        raise ValueError("Only relative JSON/JSONL history filenames are allowed.")
                    parsed = parse_text(content, "upload/" + name.lstrip("/"), json_document=name.endswith(".json"))
                    result.merge(parsed)
                return self.reply(self.server.store.ingest(result))
            if path == "/api/clear":
                if body.get("confirmation") != "DELETE LOCAL IMPORTS":
                    raise ValueError("Type DELETE LOCAL IMPORTS to delete this application's imported records.")
                self.server.store.clear()
                return self.reply({"cleared": True, "source_files_changed": False})
            if path == "/api/audit":
                if body.get("kind") == "plan":
                    return self.reply(audit_plan(body.get("text", "")))
                warnings = []
                if body.get("path"):
                    files, warnings = load_files(body["path"])
                else:
                    files = body.get("files", [])
                if not files:
                    raise ValueError("No instruction files selected/found.")
                result = audit_instructions(files)
                result["input_files"] = files
                result["limitations"].extend(warnings)
                return self.reply(result)
            if path == "/api/packet":
                kind = body.get("kind", "retrospective")
                mode = body.get("mode", self.server.initial_mode)
                filters = {key: str(body.get(key, "")) for key in ("start", "end", "project")}
                filters["tz"] = body.get("tz", self.server.timezone)
                data = None
                samples = []
                if kind in {"retrospective", "workflow-to-skill"}:
                    rows = self.server.rows(mode)
                    data = analyze(rows, mode=mode, **filters)
                    prepared, _ = prepare(rows, filters["tz"])
                    filtered = select(prepared, filters["start"], filters["end"], filters["project"])
                    users = [r for r in filtered if r["role"] == "user" and r["natural"]]
                    # Evenly spaced user excerpts with following assistant context when present.
                    for i in range(min(18, len(users))):
                        user = users[i * len(users) // min(18, len(users))]
                        samples.append(user)
                        assistant = next((r for r in filtered if r["thread_id"] == user["thread_id"] and r["role"] == "assistant"
                                          and r["timestamp"] >= user["timestamp"]), None)
                        if assistant:
                            samples.append(assistant)
                packet = make_packet(kind, files=body.get("files"), text=body.get("text", ""), analysis=data, samples=samples)
                return self.reply({"packet": packet, "prompt": get_prompt(kind)})
            if path == "/api/model":
                return self.reply(interpret(body.get("packet"), consent=body.get("consent") is True))
            return self.reply({"error": "Not found"}, 404)
        except PermissionError as exc:
            self.reply({"error": str(exc)}, 403)
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            self.reply({"error": str(exc)}, 400)
        except Exception:
            self.reply({"error": "Local operation failed. Check input format or permissions; original project files were not modified."}, 500)


def serve(store: Store, *, port: int = 8765, mode: str = "demo", timezone: str = "UTC", open_browser: bool = False):
    # Validate timezone before listening.
    prepare([], timezone)
    with EvolutionServer(("127.0.0.1", port), store, initial_mode=mode, timezone=timezone) as httpd:
        url = f"http://127.0.0.1:{httpd.server_port}"
        print(f"\n  Codex Evolution v{__version__}\n  {url}\n  Dataset: {mode}; timezone: {timezone}\n  Local only. Ctrl+C to stop.\n", flush=True)
        if open_browser:
            threading.Timer(.3, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
